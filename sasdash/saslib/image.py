from __future__ import print_function, division, absolute_import

import numpy as np


def boxsize(array_shape, center, radius=150):
    if len(center) != len(array_shape):
        raise ValueError(
            'Length of center must be the same with dimension of array')
    if np.any(np.asarray(array_shape) - np.asarray(center) < 0):
        raise ValueError('center is out of box.')
    size = (np.minimum(curr_center + radius, max_len, dtype=int) -
            np.maximum(curr_center - radius, 0, dtype=int)
            for curr_center, max_len in zip(center, array_shape))
    return tuple(size)


def boxslice(array, center, radius=150):
    """Slice a box with given radius from ndim array and return a view.
    Please notice the size of return is uncertain which depends on boundary.

    Parameters
    ----------
    array : array_like
    Input array.

    center : tuple of int
    Center in array to boxing. For 2D array, it's (row_center, col_center).
    Length must be the same with dimension of array.

    Returns
    -------
    out : array_like
    A view of `array` with given box range.
    """
    if len(center) != array.ndim:
        raise ValueError(
            'length of center must be the same with dimension of array')
    if np.any(np.asarray(array.shape) - np.asarray(center) < 0):
        raise ValueError('center is out of box.')
    # FutureWarning:
    # Using a non-tuple sequence for multidimensional indexing is deprecated;
    # use `arr[tuple(seq)]` instead of `arr[seq]`. In the future this will be
    # interpreted as an array index, `arr[np.array(seq)]`, which will result
    # either in an error or a different result.
    slicer = tuple(
        slice(
            np.maximum(curr_center - radius, 0, dtype=int),
            np.minimum(curr_center + radius, max_len, dtype=int),
        ) for curr_center, max_len in zip(center, array.shape)
    )
    return array[slicer]


def subtract_radial_average(img, rc_center, mask=None):
    """Let image subtract its radial average matrix.

    Parameters
    ----------
    img : numpy.ndarray
        2D matrix of input image
    rc_center : tuple of int
        (row, col) center of image matrix
    mask : numpy.ndarray, optional
        mask for image. 1 means valid area, 0 means masked area.
        (the default is None, which is no mask.)

    Returns
    -------
    numpy.ndarray
        return residual image.
    """
    assert img.ndim == 2, 'Wrong dimension for image.'
    assert len(rc_center) == 2, 'Wrong dimension for center.'
    if mask is not None:
        masked_img = img * mask
    else:
        masked_img = img
    rc_center = np.round(rc_center)
    meshgrids = np.indices(img.shape)  # return (xx, yy)
    # eq: r = sqrt( (x - x_center)**2 + (y - y_center)**2 + (z - z_center)**2 )
    r = np.sqrt(sum(((grid - c)**2 for grid, c in zip(meshgrids, rc_center))))
    r = np.round(r).astype(np.int)

    total_bin = np.bincount(r.ravel(), masked_img.ravel())
    nr = np.bincount(r.ravel())  # count for each r
    if mask is not None:
        r_mask = np.zeros(r.shape)
        r_mask[np.where(mask == 0.0)] = 1
        nr_mask = np.bincount(r.ravel(), r_mask.ravel())
        nr = nr - nr_mask
    radialprofile = np.zeros_like(nr)
    # r_pixel = np.unique(r.ravel())  # sorted
    nomaskr = np.where(nr > 0)
    radialprofile[nomaskr] = total_bin[nomaskr] / nr[nomaskr]
    if mask is None:
        residual_img = masked_img - radialprofile[r]  # subtract mean matrix
    else:
        residual_img = masked_img - radialprofile[r] * mask
    return residual_img
