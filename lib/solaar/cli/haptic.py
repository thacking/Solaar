## Copyright (C) 2012-2013  Daniel Pavel
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License along
## with this program; if not, write to the Free Software Foundation, Inc.,
## 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""Helpers to inspect and trigger haptic responses on supported devices."""

from __future__ import annotations

from typing import Iterable

from logitech_receiver import settings
from logitech_receiver import settings_templates

from solaar import configuration
from solaar.cli import config as config_cli


def _pick_device(receivers, args, find_device):
    device_name = args.device.lower()
    target = None
    for candidate in find_device(receivers, device_name):
        if candidate.ping():
            target = candidate
            break
    if target is None:
        raise Exception(f"no online device found matching '{args.device}'")
    if not target.settings:
        configuration.attach_to(target)
    return target


def _get_setting(dev, name):
    setting = settings_templates.check_feature_setting(dev, name)
    if setting is None and dev.descriptor and dev.descriptor.settings:
        for sclass in dev.descriptor.settings:
            if sclass.name == name:
                try:
                    setting = sclass.build(dev)
                except Exception:
                    setting = None
    return setting


def _format_level(setting):
    value = setting.read()
    if value is None:
        return "unknown"
    return setting.val_to_string(value)


def _list_waveforms(setting: settings.Setting) -> Iterable[str]:
    choices = getattr(setting, "choices", None)
    if not choices:
        return []
    return [str(choice) for choice in choices]


def _coerce_level(setting, value: str):
    if setting.kind & settings.Kind.CHOICE:
        return config_cli.select_choice(value, setting.choices, setting, None)
    if setting.kind & settings.Kind.RANGE:
        return config_cli.select_range(value, setting)
    raise Exception("haptic level setting is neither range nor choice")


def _coerce_waveform(setting, value: str):
    if not setting.choices:
        raise Exception("device did not report any haptic waveforms")
    return config_cli.select_choice(value, setting.choices, setting, None)


def run(receivers, args, _find_receiver, find_device):
    dev = _pick_device(receivers, args, find_device)

    level_setting = _get_setting(dev, "haptic-level")
    play_setting = _get_setting(dev, "haptic-play")

    if level_setting is None and play_setting is None:
        raise Exception(f"{dev.name} does not expose any haptic controls")

    if args.level is None and args.play is None and not args.list:
        args.list = True

    if args.level is not None:
        if level_setting is None:
            raise Exception(f"{dev.name} does not allow changing haptic level")
        coerced = _coerce_level(level_setting, args.level)
        level_setting.write(coerced)
        print(f"Set haptic level on {dev.name} to {level_setting.val_to_string(coerced)}")

    if args.play is not None:
        if play_setting is None:
            raise Exception(f"{dev.name} does not expose any haptic waveforms")
        waveform = _coerce_waveform(play_setting, args.play)
        play_setting.write(waveform)
        print(f"Played haptic waveform {play_setting.val_to_string(waveform)} on {dev.name}")

    if args.list:
        if level_setting:
            print(f"Current haptic level: {_format_level(level_setting)}")
        if play_setting and play_setting.choices:
            print("Available waveforms:")
            for name in _list_waveforms(play_setting):
                print(f"  - {name}")
        else:
            print("No haptic waveforms reported by the device.")
