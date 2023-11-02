#
# foris-controller
# Copyright (C) 2017, 2023 CZ.NIC, z.s.p.o. (http://www.nic.cz/)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
#

import json
import logging
import multiprocessing
import os
import random
import re
import signal
import subprocess
import threading
import typing
from collections import OrderedDict
from tempfile import TemporaryFile

import prctl

from foris_controller.app import app_info
from foris_controller.exceptions import (
    BackendCommandFailed,
    FailedToParseCommandOutput,
)
from foris_controller.utils import RWLock, make_multiprocessing_manager

logger = logging.getLogger(__name__)

i2c_lock = RWLock(app_info["lock_backend"])

CMDLINE_ROOT = os.environ.get("FORIS_CMDLINE_ROOT", "")
logger.debug("Cmdline root is set to '%s'." % str(CMDLINE_ROOT))


def inject_cmdline_root(path):
    """ merge path with root if set (path has to be absolute) relative paths are kept

    :param path: path
    :type path: str
    """
    if CMDLINE_ROOT:
        if os.path.isabs(path):
            return os.path.join(CMDLINE_ROOT, path.strip("/"))
    return path


def handle_command(*args, **kwargs):
    with TemporaryFile() as stdout, TemporaryFile() as stderr:
        popen_kwargs = {}
        input_data = kwargs.pop("input_data", None)
        proc_timeout = kwargs.get("timeout")

        popen_kwargs["stderr"] = stderr
        popen_kwargs["stdout"] = stdout
        if input_data is not None:
            popen_kwargs["stdin"] = subprocess.PIPE

        # update env
        env = dict(os.environ)
        cmd_env = kwargs.get("env", {})
        env.update(cmd_env)
        popen_kwargs["env"] = env

        process = subprocess.Popen(args, **popen_kwargs)

        try:
            if input_data:
                process.communicate(input_data, timeout=proc_timeout)
            else:
                process.communicate(timeout=proc_timeout)
        except subprocess.TimeoutExpired:
            logger.error(f"Process failed to finish in time limit {proc_timeout} seconds.")
            process.kill()

        stdout.seek(0)
        stdout = stdout.read()
        stderr.seek(0)
        stderr = stderr.read()
    return process.returncode, stdout, stderr


class BaseCmdLine(object):
    @staticmethod
    def _run_command_in_background(*args):
        """ Executes command in background

        :param args: cmd and its arguments
        :type args: tuple
        """

        # args[0] should be the script path
        args = list(args)
        args[0] = inject_cmdline_root(args[0])

        logger.debug("Starting Command '%s' is starting in background." % str(args))

        subprocess.Popen(args)

    @staticmethod
    def _run_command(*args, **kwargs):
        """ Executes command and waits till it's finished

        :param args: cmd and its arguments
        :type args: tuple

        :returns: (retcode, stdout, stderr)
        :rtype: (int, str, str)
        """

        # args[0] should be the script path
        args = list(args)
        args[0] = inject_cmdline_root(args[0])

        logger.debug("Command '%s' is starting." % str(args))

        try:
            retval, stdout, stderr = handle_command(*args, **kwargs)
        except (OSError, IOError) as e:
            raise BackendCommandFailed(e.errno, args, e.strerror)

        logger.debug("Command '%s' finished.", str(args))
        logger.debug("retcode: %d", retval)
        logger.debug("stdout: %s", stdout)
        logger.debug("stderr: %s", stderr)
        return retval, stdout, stderr

    @staticmethod
    def _run_command_and_check_retval(args, expected_retval, timeout: typing.Optional[float] = None):
        """ Runs command and checks its retval.

        :param args: cmd and its arguments
        :type args: tuple
        :param expected_retval: expected retval
        :type expected_retval: int
        :param timeout: optional timeout
        :type timeout: float or None

        :returns: (stdout, stderr)
        :rtype: (str, str)
        :raises: BackendCommandFailed
        """
        retval, stdout, stderr = BaseCmdLine._run_command(*args, timeout=timeout)
        if not retval == expected_retval:
            logger.error(
                "Command %s unexpected returncode (%d, expected %d)."
                % (str(args), retval, expected_retval)
            )
            raise BackendCommandFailed(retval, args)
        return stdout, stderr

    @staticmethod
    def _trigger_and_parse(args, regex, groups=(1,)):
        """ Runs command and parses the output by regex,
            raises an exception when the output doesn't match regex

        :param args: command and arguments
        :type args: tuple
        :param regex: regular expression to match
        :type regex: str
        :param groups: groups which will be returned from the matching regex
        :type groups: tuple of int
        :returns: matching strings
        :rtype: tuple
        """
        stdout, _ = BaseCmdLine._run_command_and_check_retval(args, 0)
        match = re.search(regex, stdout.decode("utf-8"), re.MULTILINE)
        if not match:
            logger.error("Failed to parse output of %s." % str(args))
            raise FailedToParseCommandOutput(args, stdout)
        return match.group(*groups)


class AsyncProcessData(object):
    def __init__(self, manager):
        """ Initializes async process data instance.
        Note that these data will be shared between two processes using shared memory

        :param manager: multiprocessing manager
        :type manager: multiprocessing.managers.SyncManager
        """
        self.lock = manager.Lock()
        self.id = "%016x" % random.randrange(2 ** 64)
        self._data = manager.list()
        self._retval = manager.Value(int, 0)
        self._exited = manager.Value(bool, False)

    def read_all_data(self):
        """ Reads and returns all data which were stored by the process
        :returns: process data
        :rtype: dict
        """
        with self.lock:
            return [json.loads(e) for e in self._data]

    def append_data(self, record):
        """ Appends a record to process data
        :returns: process data
        :rtype: dict
        """

        with self.lock:
            # data needed to be stored in string
            # (shared memory migth be inconsistent when more complex types are used)
            self._data.append(json.dumps(record))

    def set_retval(self, retval):
        """ Set the return value of the process
        :param retval: process return value
        :type retval: int
        """
        self._retval.set(retval)

    def get_retval(self):
        """ Returns the return value of the process.
        Should be used only after get_exited() returns True
        :returns: retval of the process
        :rtype: int
        """
        return self._retval.get()

    def set_exited(self):
        """ Sets the the process exited
        """
        self._exited.set(True)

    def get_exited(self):
        """ returns whether the process exited
        :returns: True if process exited False if the process is still running
        :rtype: bool
        """
        return self._exited.get()


class AsyncCommand(object):
    PROCESS_BUFFER = 20

    manager = make_multiprocessing_manager()

    def __init__(self):
        self.lock = RWLock(app_info["lock_backend"])
        self.processes = OrderedDict()

    @staticmethod
    def _command_worker(args, reset_notify, handler_list, handler_exit, process_data, ready):
        """ Watch over an external command

        :param args: arguments of the external commands
        :type args: list[str]
        :param handler_list: list of tuples [(regex, handler(matched, process_data)), ...]
        :type handler_list: list[tuple]
        :param handler_exit: handler which is called when process finishes - handler(process_data)
        :type handler_exit: callable
        :param reset_notify: function which is call to reset notification connection
        :type reset_notify: callable
        :param process_data: place where the data between the worker and the parent process
                             are shared
        :type process_data: AsyncProcessData
        :param ready: event synchronization with parent process
                      (tells parent process that it may continue)
        """

        logger.debug("Async process started.")

        # args[0] should be the script path
        args = list(args)
        args[0] = inject_cmdline_root(args[0])

        # precompile regexes
        handler_list = [(re.compile(regex), handler) for regex, handler in handler_list]

        # exit when parent thread dies
        prctl.set_pdeathsig(signal.SIGKILL)

        # we are in another process so it might be necessary to repopen the connection
        if reset_notify:
            reset_notify()

        # the parent may continue
        ready.set()

        logger.debug("Starting monitored process: %s" % args)

        def preexec():
            # make sure that program dies when parent is terminated
            prctl.set_pdeathsig(signal.SIGKILL)
            # for python programs this will force that stdout/stderr are flushed immediatelly
            os.environ["PYTHONUNBUFFERED"] = "1"

        process = subprocess.Popen(
            args,
            preexec_fn=preexec,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            close_fds=True,
            universal_newlines=True,
        )

        def process_output_line() -> bool:
            line = process.stdout.readline()

            if not line:  # readline() returns '' when it reaches end
                return False

            line = line[:-1]  # remove \n
            logger.debug("Processing output line of the monitored file: '%s'" % line)
            for regex, handler in handler_list:
                match = regex.match(line)
                if match:
                    # Run the handler
                    handler(match, process_data)

            return True

        while process.poll() is None:
            process_output_line()

        while process_output_line():  # program ended, but there ca be some output left
            pass

        process_data.set_retval(process.returncode)
        process_data.set_exited()
        if handler_exit:
            handler_exit(process_data)
        logger.debug("Async process finished.")

    def start_process(self, args, handler_list, handler_exit, reset_notify_function):
        """ Starts a thread which starts a process which monitors external command.

        A new process is started because ubus doesn't allow you to listen and send notification
        at once.

        :param args: arguments of the external commands
        :type args: list[str]
        :param handler_list: list of tuples [(regex, handler(matched, process_data)), ...]
        :type handler_list: list[tuple]
        :param handler_exit: handler which is called when process finishes - handler(process_data)
        :type handler_exit: callable
        :param reset_notify_function: function which is call to reset notification connection
        :type reset_notify_function: callable

        :returns: A new process identifier
        :rtype: str
        """

        new_data_process = AsyncProcessData(self.manager)
        process_started = threading.Event()

        # process is started in another thread
        # prctl kills the child process when parent thread dies
        # and this code might be called from some handler thread which dies
        # after response is delivered
        def worker_thread(process_started):
            import logging

            logger = logging.getLogger(__name__)

            # Prepare ready event to wait for the process to be initialized
            ready = multiprocessing.Event()
            ready.clear()

            logger.debug("Preparing async worker process.")
            process = multiprocessing.Process(
                target=AsyncCommand._command_worker,
                args=(
                    args,
                    reset_notify_function,
                    handler_list,
                    handler_exit,
                    new_data_process,
                    ready,
                ),
            )

            with self.lock.writelock:
                # test whether there is still space in buffer and remove midd
                while len(self.processes) >= self.PROCESS_BUFFER:
                    self.processes.popitem(False)
                self.processes[new_data_process.id] = new_data_process

            logger.debug("Starting async worker process.")
            process.start()
            ready.wait()
            process_started.set()
            process.join()
            logger.debug("Async worker process finished.")

        work_thread = threading.Thread(target=worker_thread, args=(process_started,))
        work_thread.daemon = True
        work_thread.start()

        # Wait for the process
        process_started.wait()

        return new_data_process.id


class AsyncMultipleCommands(object):
    PROCESS_BUFFER = 20

    manager = make_multiprocessing_manager()

    def __init__(self):
        self.lock = RWLock(app_info["lock_backend"])
        self.processes = OrderedDict()

    @staticmethod
    def _command_worker(subprocess_infos, reset_notify, handler_result, handler_exit, process_data, ready):
        """ Watch over an external command

        :param subprocess_infos: arguments of the external commands
        :type subprocess_infos: list[]
        :param handler_result: handler(process_data)
        :type handler_result: callable
        :param handler_exit: handler which is called when process finishes - handler(process_data)
        :type handler_exit: callable
        :param reset_notify: function which is call to reset notification connection
        :type reset_notify: callable
        :param process_data: place where the data between the worker and the parent process
                             are shared
        :type process_data: AsyncProcessData
        :param ready: event synchronization with parent process
                      (tells parent process that it may continue)
        """

        logger.debug("Async process started.")

        def format_args(subprocess_info):
            # args[0] should be the script path
            args = list(subprocess_info["args"])
            args[0] = inject_cmdline_root(args[0])
            subprocess_info["args"] = args
            return subprocess_info

        subprocess_formatted = list(map(format_args, subprocess_infos))

        # exit when parent thread dies
        prctl.set_pdeathsig(signal.SIGKILL)

        # we are in another process so it might be necessary to repopen the connection
        if reset_notify:
            reset_notify()

        # the parent may continue
        ready.set()

        for s in subprocess_formatted:
            logger.debug("Starting monitored process: %s" % s["args"])

        def preexec():
            # make sure that program dies when parent is terminated
            prctl.set_pdeathsig(signal.SIGKILL)
            # for python programs this will force that stdout/stderr are flushed immediatelly
            os.environ["PYTHONUNBUFFERED"] = "1"

        def start_subprocess(subprocess_info):
            process = subprocess.Popen(
                subprocess_info["args"],
                preexec_fn=preexec,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                close_fds=True,
                universal_newlines=True,
            )
            subprocess_info["process"] = process
            subprocess_info["handled"] = False
            return subprocess_info

        subprocesses = list(map(start_subprocess, subprocess_formatted))

        def process_output(subprocess_info):
            if subprocess_info["process"].returncode != 0:
                logger.warning("Failure during ubus call: %s", subprocess_info["process"].stderr)
                return

            decoded = subprocess_info["process"].stdout.read()
            if decoded:
                result = json.loads(decoded)
            else:
                result = {}

            handler_result(process_data, result)

        def handle_subprocesses():
            for s in subprocesses:
                if s["process"].poll() is not None and not s["handled"]:
                    process_output(s)
                    s["handled"] = True

        while any(map(lambda x: x["process"].poll() is None, subprocesses)):
            handle_subprocesses()
            pass

        handle_subprocesses()

        process_data.set_retval(max(map(lambda x: x["process"].returncode, subprocesses)))
        process_data.set_exited()
        if handler_exit:
            handler_exit(process_data)
        logger.debug("Async process finished.")

    def start_process(self, subprocess_infos, handler_result, handler_exit, reset_notify_function):
        """ Starts a thread which starts a process which monitors external command.

        A new process is started because ubus doesn't allow you to listen and send notification
        at once.


        :param subprocess_infos:
        :type subprocess_infos: []
        :param handler_result: handler(process_data)
        :type handler_result: callable
        :param handler_exit: handler which is called when process finishes - handler(process_data)
        :type handler_exit: callable
        :param reset_notify_function: function which is call to reset notification connection
        :type reset_notify_function: callable

        :returns: A new process identifier
        :rtype: str
        """

        new_data_process = AsyncProcessData(self.manager)
        process_started = threading.Event()

        # process is started in another thread
        # prctl kills the child process when parent thread dies
        # and this code might be called from some handler thread which dies
        # after response is delivered
        def worker_thread(process_started):
            import logging

            logger = logging.getLogger(__name__)

            # Prepare ready event to wait for the process to be initialized
            ready = multiprocessing.Event()
            ready.clear()

            logger.debug("Preparing async worker process.")
            process = multiprocessing.Process(
                target=AsyncMultipleCommands._command_worker,
                args=(
                    subprocess_infos,
                    reset_notify_function,
                    handler_result,
                    handler_exit,
                    new_data_process,
                    ready,
                ),
            )

            with self.lock.writelock:
                # test whether there is still space in buffer and remove midd
                while len(self.processes) >= self.PROCESS_BUFFER:
                    self.processes.popitem(False)
                self.processes[new_data_process.id] = new_data_process

            logger.debug("Starting async worker process.")
            process.start()
            ready.wait()
            process_started.set()
            process.join()
            logger.debug("Async worker process finished.")

        work_thread = threading.Thread(target=worker_thread, args=(process_started,))
        work_thread.daemon = True
        work_thread.start()

        # Wait for the process
        process_started.wait()

        return new_data_process.id
