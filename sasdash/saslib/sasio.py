from __future__ import print_function, division, absolute_import

import os
import re
import json
from io import open  # python 2/3

from .measurement import SASM


def load_dat(filepath):
    """ `Primus` format """
    filename = os.path.split(filepath)[1]
    fstream = open(filepath)

    # float_pattern = '\d*[.]\d*[+eE-]*\d+\s'
    float_pattern = r'(?:\d+\.)?\d+[eE][-\+]\d+'

    counter = 0
    prog = re.compile(float_pattern)
    q, i, err = [], [], []
    for line in fstream:
        if '### HEADER' in line:
            exist_primus_header = True

        split_line = line.strip().split()
        if prog.match(line) and len(split_line) >= 3:
            q.append(float(split_line[0]))
            i.append(float(split_line[1]))
            err.append(float(split_line[2]))
            counter += 1

    if exist_primus_header:
        pass

    fstream.close()
    return SASM(q, i, err, filename=filename)


def load_ionchamber(filepath):
    raise NotImplementedError


def load_tiff_image(filepath):
    raise NotImplementedError
