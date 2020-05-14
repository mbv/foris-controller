#!/usr/bin/env python3

import argparse
import json


WIFI_DATA = {
    "info": {
        "radio0": {
            "phy": "phy0",
            "bssid": "04:F0:21:24:1D:8D",
            "country": "US",
            "mode": "Master",
            "channel": 0,
            "frequency": 5000,
            "frequency_offset": 0,
            "txpower": 13,
            "txpower_offset": 0,
            "quality_max": 70,
            "noise": 0,
            "htmodes": [
                "HT20",
                "HT40",
                "VHT20",
                "VHT40",
                "VHT80",
                "VHT160"
            ],
            "hwmodes": [
                "ac",
                "b",
                "g",
                "n"
            ],
            "hardware": {
                "id": [
                    32902,
                    10019,
                    32902,
                    132
                ],
                "name": "Generic MAC80211"
            }
        },
        "radio1": {
            "phy": "phy1",
            "country": "US",
            "frequency_offset": 0,
            "txpower_offset": 0,
            "quality_max": 70,
            "noise": 0,
            "htmodes": [
                "HT20",
                "HT40"
            ],
            "hwmodes": [
                "b",
                "g",
                "n"
            ],
            "hardware": {
                "id": [
                    5772,
                    46,
                    5772,
                    12452
                ],
                "name": "Atheros AR9287"
            }
        },
    },
    "freqlist": {
        "radio0": {
            "results": [
                {
                    "channel": 1,
                    "mhz": 2412,
                    "restricted": False
                },
                {
                    "channel": 2,
                    "mhz": 2417,
                    "restricted": False
                },
                {
                    "channel": 3,
                    "mhz": 2422,
                    "restricted": False
                },
                {
                    "channel": 4,
                    "mhz": 2427,
                    "restricted": False
                },
                {
                    "channel": 5,
                    "mhz": 2432,
                    "restricted": False
                },
                {
                    "channel": 6,
                    "mhz": 2437,
                    "restricted": False
                },
                {
                    "channel": 7,
                    "mhz": 2442,
                    "restricted": False
                },
                {
                    "channel": 8,
                    "mhz": 2447,
                    "restricted": False
                },
                {
                    "channel": 9,
                    "mhz": 2452,
                    "restricted": False
                },
                {
                    "channel": 10,
                    "mhz": 2457,
                    "restricted": False
                },
                {
                    "channel": 11,
                    "mhz": 2462,
                    "restricted": False
                },
                {
                    "channel": 12,
                    "mhz": 2467,
                    "restricted": False
                },
                {
                    "channel": 13,
                    "mhz": 2472,
                    "restricted": False
                },
                {
                    "channel": 36,
                    "mhz": 5180,
                    "restricted": False
                },
                {
                    "channel": 40,
                    "mhz": 5200,
                    "restricted": False
                },
                {
                    "channel": 44,
                    "mhz": 5220,
                    "restricted": False
                },
                {
                    "channel": 48,
                    "mhz": 5240,
                    "restricted": False
                },
                {
                    "channel": 52,
                    "mhz": 5260,
                    "restricted": False
                },
                {
                    "channel": 56,
                    "mhz": 5280,
                    "restricted": False
                },
                {
                    "channel": 60,
                    "mhz": 5300,
                    "restricted": False
                },
                {
                    "channel": 64,
                    "mhz": 5320,
                    "restricted": False
                },
                {
                    "channel": 68,
                    "mhz": 5340,
                    "restricted": False
                },
                {
                    "channel": 72,
                    "mhz": 5360,
                    "restricted": False
                },
                {
                    "channel": 76,
                    "mhz": 5380,
                    "restricted": False
                },
                {
                    "channel": 80,
                    "mhz": 5400,
                    "restricted": False
                },
                {
                    "channel": 84,
                    "mhz": 5420,
                    "restricted": False
                },
                {
                    "channel": 88,
                    "mhz": 5440,
                    "restricted": False
                },
                {
                    "channel": 92,
                    "mhz": 5460,
                    "restricted": False
                },
                {
                    "channel": 96,
                    "mhz": 5480,
                    "restricted": False
                },
                {
                    "channel": 100,
                    "mhz": 5500,
                    "restricted": False
                },
                {
                    "channel": 104,
                    "mhz": 5520,
                    "restricted": False
                },
                {
                    "channel": 108,
                    "mhz": 5540,
                    "restricted": False
                },
                {
                    "channel": 112,
                    "mhz": 5560,
                    "restricted": False
                },
                {
                    "channel": 116,
                    "mhz": 5580,
                    "restricted": False
                },
                {
                    "channel": 120,
                    "mhz": 5600,
                    "restricted": False
                },
                {
                    "channel": 124,
                    "mhz": 5620,
                    "restricted": False
                },
                {
                    "channel": 128,
                    "mhz": 5640,
                    "restricted": False
                },
                {
                    "channel": 132,
                    "mhz": 5660,
                    "restricted": False
                },
                {
                    "channel": 136,
                    "mhz": 5680,
                    "restricted": False
                },
                {
                    "channel": 140,
                    "mhz": 5700,
                    "restricted": False
                },
                {
                    "channel": 144,
                    "mhz": 5720,
                    "restricted": False
                },
                {
                    "channel": 149,
                    "mhz": 5745,
                    "restricted": False
                },
                {
                    "channel": 153,
                    "mhz": 5765,
                    "restricted": False
                },
                {
                    "channel": 157,
                    "mhz": 5785,
                    "restricted": False
                },
                {
                    "channel": 161,
                    "mhz": 5805,
                    "restricted": False
                },
                {
                    "channel": 165,
                    "mhz": 5825,
                    "restricted": False
                },
                {
                    "channel": 169,
                    "mhz": 5845,
                    "restricted": False
                },
                {
                    "channel": 173,
                    "mhz": 5865,
                    "restricted": False
                },
                {
                    "channel": 177,
                    "mhz": 5885,
                    "restricted": False
                },
                {
                    "channel": 181,
                    "mhz": 5905,
                    "restricted": False
                }
            ]
        },
        "radio1": {
            "results": [
                {
                    "channel": 1,
                    "mhz": 2412,
                    "restricted": False,
                    "active": False
                },
                {
                    "channel": 2,
                    "mhz": 2417,
                    "restricted": False,
                    "active": False
                },
                {
                    "channel": 3,
                    "mhz": 2422,
                    "restricted": False,
                    "active": False
                },
                {
                    "channel": 4,
                    "mhz": 2427,
                    "restricted": False,
                    "active": False
                },
                {
                    "channel": 5,
                    "mhz": 2432,
                    "restricted": False,
                    "active": False
                },
                {
                    "channel": 6,
                    "mhz": 2437,
                    "restricted": False,
                    "active": True
                },
                {
                    "channel": 7,
                    "mhz": 2442,
                    "restricted": False,
                    "active": False
                },
                {
                    "channel": 8,
                    "mhz": 2447,
                    "restricted": False,
                    "active": False
                },
                {
                    "channel": 9,
                    "mhz": 2452,
                    "restricted": False,
                    "active": False
                },
                {
                    "channel": 10,
                    "mhz": 2457,
                    "restricted": False,
                    "active": False
                },
                {
                    "channel": 11,
                    "mhz": 2462,
                    "restricted": False,
                    "active": False
                },
                {
                    "channel": 12,
                    "mhz": 2467,
                    "restricted": False,
                    "active": False
                },
                {
                    "channel": 13,
                    "mhz": 2472,
                    "restricted": False,
                    "active": False
                }
            ]
        },
    }
}


def main():
    parser = argparse.ArgumentParser(prog="ubus")
    parser.add_argument("command")
    parser.add_argument("object", help="ubus object")
    parser.add_argument("method", help="ubus object method")
    parser.add_argument("message", help="message", nargs="?")

    args = parser.parse_args()

    if args.command != "call":
        print({})

    if args.object != "iwinfo":
        print({})

    if args.method not in ["info", "freqlist"]:
        print({})

    device = json.loads(args.message).get("device")

    print(
        json.dumps(WIFI_DATA[args.method].get(device, {}), indent=2)
    )


if __name__ == "__main__":
    main()
