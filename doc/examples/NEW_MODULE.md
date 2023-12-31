# Create a new Foris Controller Module based on this template

You probably need to have a python virtualenv to install cookiecutter. Then you can:

```bash
pip install cookiecutter
cookiecutter foris_controller/doc/examples/ -o <module_name>
```

Note that after the skeleton in your git repository, you need to initialize `common` git submodule
```
git submodule add https://gitlab.nic.cz/turris/foris-controller/common.git common
ln -s common/foris-controller-modules/tox.ini tox.ini
git add tox.ini
```

# Making a new version of module
* set new version in `<module_name>/foris_controller_<module_name>/__init__.py`
* update changelog `<module_name>/CHANGELOG.md`
* create an version commit (e.g. "version bump" or "Version X.Y.Z")
* create new (signed and annotated tag) `git tag -s -a vX.Y.Z>`
* push tag into repo `git push && git push --tags`
