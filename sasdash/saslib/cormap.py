from __future__ import print_function, division, absolute_import

import re

import numpy as np
from scipy.spatial.distance import squareform

from sasdash.utils import run_system_command, common_prefix


def get_datcmp_info(scattering_curve_files):
    """
    Extract the data produced by DATCMP.

    This method is used by the constructor method of the ScatterAnalysis
    class. It runs the DATCMP program on the dataset and returns a
    dictionary containing the main results from the DATCMP run.

    Parameters
    ----------
    scattering_curve_files : str
        Location of the scattering curves for the dataset.

    Returns
    -------
    dict(str, numpy.array)
        Dictionary containing the results of the DATCMP run. The dictionary
        key is a string (with no spaces) denoting the pair of frames that
        were compared e.g. "1,2" would be frames 1 and 2. The dictionary
        value is an array of DATCMP results for the corresponding pairwise
        comparison.

    Examples
    --------
    >>>  datcmp_data = get_datcmp_info("saxs_files.00*.dat")
    """
    cmd = "datcmp {}".format(scattering_curve_files)
    log = run_system_command(cmd, shell=True)
    # define a dictionary to store the data produced from DATCMP - this
    # value will be overwritten.
    pair_frames = []
    c_values = []
    p_values = []
    adjp_values = []
    for line in iter(log.splitlines()):
        match_obj = re.match(r'\s* \d{1,} vs', line)
        if match_obj:
            data = line.split()
            if "*" in data[5]:
                data[5] = data[5][:-1]
            pair_frames.append("{},{}".format(data[0], data[2]))
            c_values.append(int(float(data[3])))
            p_values.append(float(data[4]))
            adjp_values.append(float(data[5]))

    return (
        pair_frames,
        np.asarray(c_values, dtype=int),
        np.asarray(p_values, dtype=float),
        np.asarray(adjp_values, dtype=float),
    )


def calc_cormap_heatmap(file_list):
    # heatmap_type options: 'C', 'Pr(>C)', 'adj Pr(>C)'
    # file_list = self.get_files(exp, 'subtracted_files')
    file_pattern = common_prefix(file_list)

    scattering_curve_files = '%s*' % file_pattern
    _, c_values, p_values, adjp_values = get_datcmp_info(
        scattering_curve_files)

    cormap_heatmap = dict()
    cormap_heatmap['C'] = squareform(c_values)
    eye_matrix = np.eye(*cormap_heatmap['C'].shape)
    cormap_heatmap['Pr(>C)'] = squareform(p_values) + eye_matrix
    cormap_heatmap['adj Pr(>C)'] = squareform(adjp_values) + eye_matrix
    return cormap_heatmap
