from __future__ import print_function, division, absolute_import

import os
import re
import json
from io import open  # python 2/3

from PIL import Image
import numpy as np

from .measurement import SASM, IFTM


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


def load_out(filepath):
    """ GNOM format """
    # Port from RAW
    five_col_fit = re.compile('\s*\d*[.]\d*[+eE-]*\d+\s+-?\d*[.]\d*[+eE-]*\d+\s+\d*[.]\d*[+eE-]*\d+\s+\d*[.]\d*[+eE-]*\d+\s+\d*[.]\d*[+eE-]*\d+\s*$')
    three_col_fit = re.compile('\s*\d*[.]\d*[+eE-]*\d+\s+-?\d*[.]\d*[+eE-]*\d+\s+\d*[.]\d*[+eE-]*\d+\s*$')
    two_col_fit = re.compile('\s*\d*[.]\d*[+eE-]*\d+\s+-?\d*[.]\d*[+eE-]*\d+\s*$')

    results_fit = re.compile('\s*Current\s+\d*[.]\d*[+eE-]*\d*\s+\d*[.]\d*[+eE-]*\d*\s+\d*[.]\d*[+eE-]*\d*\s+\d*[.]\d*[+eE-]*\d*\s+\d*[.]\d*[+eE-]*\d*\s+\d*[.]\d*[+eE-]*\d*\s*\d*[.]?\d*[+eE-]*\d*\s*$')

    te_fit = re.compile('\s*Total\s+[Ee]stimate\s*:\s+\d*[.]\d+\s*\(?[A-Za-z\s]+\)?\s*$')
    te_num_fit = re.compile('\d*[.]\d+')
    te_quality_fit = re.compile('[Aa][A-Za-z\s]+\)?\s*$')

    p_rg_fit = re.compile('\s*Real\s+space\s*\:?\s*Rg\:?\s*\=?\s*\d*[.]\d+[+eE-]*\d*\s*\+-\s*\d*[.]\d+[+eE-]*\d*')
    q_rg_fit = re.compile('\s*Reciprocal\s+space\s*\:?\s*Rg\:?\s*\=?\s*\d*[.]\d+[+eE-]*\d*\s*')

    p_i0_fit = re.compile('\s*Real\s+space\s*\:?[A-Za-z0-9\s\.,+-=]*\(0\)\:?\s*\=?\s*\d*[.]\d+[+eE-]*\d*\s*\+-\s*\d*[.]\d+[+eE-]*\d*')
    q_i0_fit = re.compile('\s*Reciprocal\s+space\s*\:?[A-Za-z0-9\s\.,+-=]*\(0\)\:?\s*\=?\s*\d*[.]\d+[+eE-]*\d*\s*')

    qfull = []
    qshort = []
    Jexp = []
    Jerr  = []
    Jreg = []
    Ireg = []

    R = []
    P = []
    Perr = []

    outfile = []

    with open(filepath) as f:
        for line in f:
            twocol_match = two_col_fit.match(line)
            threecol_match = three_col_fit.match(line)
            fivecol_match = five_col_fit.match(line)
            results_match = results_fit.match(line)
            te_match = te_fit.match(line)
            p_rg_match = p_rg_fit.match(line)
            q_rg_match = q_rg_fit.match(line)
            p_i0_match = p_i0_fit.match(line)
            q_i0_match = q_i0_fit.match(line)

            outfile.append(line)

            if twocol_match:
                # print(line)
                found = twocol_match.group().split()

                qfull.append(float(found[0]))
                Ireg.append(float(found[1]))

            elif threecol_match:
                #print(line)
                found = threecol_match.group().split()

                R.append(float(found[0]))
                P.append(float(found[1]))
                Perr.append(float(found[2]))

            elif fivecol_match:
                #print(line)
                found = fivecol_match.group().split()

                qfull.append(float(found[0]))
                qshort.append(float(found[0]))
                Jexp.append(float(found[1]))
                Jerr.append(float(found[2]))
                Jreg.append(float(found[3]))
                Ireg.append(float(found[4]))

            elif results_match:
                found = results_match.group().split()
                Actual_DISCRP = float(found[1])
                Actual_OSCILL = float(found[2])
                Actual_STABIL = float(found[3])
                Actual_SYSDEV = float(found[4])
                Actual_POSITV = float(found[5])
                Actual_VALCEN = float(found[6])

                if len(found) == 8:
                    Actual_SMOOTH = float(found[7])
                else:
                    Actual_SMOOTH = -1

            elif te_match:
                te_num_search = te_num_fit.search(line)
                te_quality_search = te_quality_fit.search(line)

                TE_out = float(te_num_search.group().strip())
                quality = te_quality_search.group().strip().rstrip(')').strip()


            if p_rg_match:
                found = p_rg_match.group().split()
                rg = float(found[-3])
                rger = float(found[-1])

            elif q_rg_match:
                found = q_rg_match.group().split()
                q_rg = float(found[-1])

            if p_i0_match:
                found = p_i0_match.group().split()
                i0 = float(found[-3])
                i0er = float(found[-1])

            elif q_i0_match:
                found = q_i0_match.group().split()
                q_i0 = float(found[-1])


    # Output variables not in the results file:
    #             'r'         : R,            #R, note R[-1] == Dmax
    #             'p'         : P,            #P(r)
    #             'perr'      : Perr,         #P(r) error
    #             'qlong'     : qfull,        #q down to q=0
    #             'qexp'      : qshort,       #experimental q range
    #             'jexp'      : Jexp,         #Experimental intensities
    #             'jerr'      : Jerr,         #Experimental errors
    #             'jreg'      : Jreg,         #Experimental intensities from P(r)
    #             'ireg'      : Ireg,         #Experimental intensities extrapolated to q=0

    name = os.path.basename(filepath)

    results = {
        'dmax'      : R[-1],        #Dmax
        'TE'        : TE_out,       #Total estimate
        'rg'        : rg,           #Real space Rg
        'rger'      : rger,         #Real space rg error
        'i0'        : i0,           #Real space I0
        'i0er'      : i0er,         #Real space I0 error
        'q_rg'      : q_rg,         #Reciprocal space Rg
        'q_i0'      : q_i0,         #Reciprocal space I0
        'out'       : outfile,      #Full contents of the outfile, for writing later
        'quality'   : quality,      #Quality of GNOM out file
        'chisq'     : Actual_DISCRP,#DISCRIP, chi squared
        'oscil'     : Actual_OSCILL,#Oscillation of solution
        'stabil'    : Actual_STABIL,#Stability of solution
        'sysdev'    : Actual_SYSDEV,#Systematic deviation of solution
        'positv'    : Actual_POSITV,#Relative norm of the positive part of P(r)
        'valcen'    : Actual_VALCEN,#Validity of the chosen interval in real space
        'smooth'    : Actual_SMOOTH,#Smoothness of the chosen interval? -1 indicates no real value, for versions of GNOM < 5.0 (ATSAS <2.8)
        'filename'  : name,         #GNOM filename
        'algorithm' : 'GNOM'        #Lets us know what algorithm was used to find the IFT
    }

    return IFTM(R, P, Perr, qshort, Jexp, Jerr, Jreg, qfull, Ireg, results)


def load_ionchamber(filepath):
    raise NotImplementedError


def load_tiff_image(filepath):
    """ Tiff Image """
    # TODO: return image header?
    with Image.open(filepath) as opened_image:
        image = np.asarray(opened_image, dtype=float)
    return image


def load_pilatus_image(filepath):
    """ Pilatus Image Format """
    image = np.fliplr(load_tiff_image(filepath))
    return image  # , img_hdr
