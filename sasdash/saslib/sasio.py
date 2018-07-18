from __future__ import print_function, division, absolute_import

import os
import re
import json
from io import open # python 2/3

import numpy as np

from .measurement import SASM


def load_dat(filepath):
    # `Primus` format
    filename = os.path.split(filepath)[1]
    fstream = open(filepath)

    float_pattern = '\d*[.]\d*[+eE-]*\d+\s'

    for line in fstream:
        if '### HEADER' in line:
            exist_primus_header = True

    if exist_primus_header:
        pass

    fstream.close()
    return SASM(q, i, err, filename=filename)


def load_ionchamber(filepath):
    raise NotImplementedError


def load_tiff_image(filepath):
    raise NotImplementedError
