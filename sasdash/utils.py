from __future__ import print_function, division, absolute_import

import os.path
import shlex
import subprocess
from io import open
from itertools import groupby
from typing import Union
from difflib import SequenceMatcher
from functools import reduce

from ruamel.yaml import YAML
yaml = YAML()


def parse_yaml(yaml_file):
    try:
        with open(yaml_file, 'r', encoding='utf-8') as fstream:
            info = yaml.load(fstream)
    # except yaml.scanner.ScannerError as err:  # syntax error: empty fields
    except Exception as err:
        print(err)
        info = {}
    if info is None:
        info = {}
    return info


def dump_yaml(data, yaml_file):
    with open(yaml_file, 'w', encoding='utf-8') as fstream:
        yaml.dump(data, fstream)


def to_basic_type(string: str) -> Union[bool, int, float, str]:
    if string.lower() == 'true':
        return True
    elif string.lower() == 'false':
        return False

    try:
        return int(string)
    except ValueError:
        try:
            return float(string)
        except ValueError:
            return string


def find_atsas_package():
    pass


def run_system_command(command_string, shell=False):
    """Function used to run the system command and return the log"""
    if shell:
        cmd = command_string
    else:
        cmd = shlex.split(command_string)
    process = subprocess.Popen(
        cmd,
        shell=shell,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding='utf-8',
    )
    output, error = process.communicate()  # get the log.
    if error is not None:
        print(error)
    return output


def str2bool(param):
    """Cast bool string to real bool type"""
    if param.lower() in ('true', 'yes', 't', 'y', '1'):
        return True
    elif param.lower() in ('false', 'no', 'f', 'n', '0'):
        return False
    else:
        from argparse import ArgumentTypeError
        raise ArgumentTypeError('Boolean value expected.')


def all_equal(iterable):
    """Return True if all the elements are equal to each other"""
    g = groupby(iterable)
    return next(g, True) and not next(g, False)


def common_prefix(iterable):
    """Return common prefix from a string list/tuple"""
    return os.path.commonprefix(
        iterable if isinstance(iterable, (list, tuple)) else tuple(iterable))


def common_suffix(iterable):
    """Return common suffix from a string list/tuple"""
    return common_prefix(tuple(s[::-1] for s in iterable))[::-1]


def _calc_common_string(a, b):
    match = SequenceMatcher(None, a, b).find_longest_match(
        0, len(a), 0, len(b))
    return a[match.a:match.a + match.size]


def common_string(iterable):
    """Return the longest common string from iterable string group"""
    return reduce(_calc_common_string, iterable)
