from __future__ import print_function, division, absolute_import

import numpy as np
from scipy.interpolate import interp1d


class DataNotCompatible(Exception):
    pass


class Base(object):
    pass


class SASM(Base):
    """Small Angle Scattering Measurement (SASM)"""

    def __init__(self, q, i, err, filename=None, **kwargs):
        if not (len(q) == len(i) == len(err)):
            raise DataNotCompatible(
                'length of (q, intensity, error) is not equal.')
        self._raw_q = self._q = np.array(q).reshape(-1)
        self._raw_i = self._i = np.array(i).reshape(-1)
        self._raw_err = self._err = np.array(err).reshape(-1)

        self._scale_factor = 1.0
        self._q_i_err = np.asarray((self._q, self._i, self._err))
        self._interp_func = None

        self._parameters = {'filename': filename}
        for key, val in kwargs.items():
            self._parameters[key] = val

    @property
    def q(self):
        return self._q

    @property
    def i(self):
        return self._i

    @property
    def err(self):
        return self._err

    @property
    def scale_factor(self):
        return self._scale_factor

    @property
    def __array_interface__(self):
        # numpy array interface support
        return self._q_i_err.__array_interface__

    def __iter__(self):
        return iter(self._q_i_err)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self._q_i_err[key]
        elif isinstance(key, int):
            if key < -3 or key > 2:
                raise IndexError('index is out of bounds with size 3')
            return self._q_i_err[key]
        else:
            raise NotImplementedError('no support for other keys.')

    def __getslice__(self, i, j):
        # python 2 compatibility
        return self.__getitem__(slice(i, j))

    def __copy__(self):
        pass

    def __deepcopy__(self, memodict={}):
        pass

    def __add__(self, other):
        # sasm + sasm
        pass

    def __sub__(self, other):
        # syntactic sugar: sasm - sasm
        pass

    def __mul__(self, other):
        # sasm * scale_factor
        pass

    def __imul__(self, other):
        # TODO: sasm *= scale_factor
        pass

    def _interpolate(self):
        self._interp_func = {
            'i': interp1d(self._raw_q, self._raw_i, kind='quadratic'),
            'err': interp1d(self._raw_q, self._raw_err, kind='quadratic')
        }

    def _check_bounds(self, qvec_new):
        below_bounds = qvec_new < self._q
        above_bounds = qvec_new > self._q
        if below_bounds.any():
            raise ValueError("A value in qvec_new is below the interpolation "
                             "range.")
        if above_bounds.any():
            raise ValueError("A value in qvec_new is above the interpolation "
                             "range.")

    def _update(self):
        """updates modified intensity after scale, normalization and offset changes"""
        pass

    def get_parameter(self, key, default=None):
        return self._parameters.get(key, default)

    def get_profile(self, qmin, qmax):
        idxs = np.logical_and(self.q >= qmin, self.q < qmax)
        return (self.q[idxs], self.i[idxs], self.err[idxs])

    def find_closest_q_idx(self, q):
        return np.abs(self.q - q).argmin()

    def fit(self, qvec):
        self._check_bounds(qvec)
        if self._interp_func is None:
            self._interpolate()
        return self._interp_func['i'](qvec)

    def scale(self, scale_factor):
        self._scale_factor = scale_factor
        self._i *= self._scale_factor
        self._err *= self._scale_factor

    def rebase(self, qvec):
        self._check_bounds(qvec)
        if self._interp_func is None:
            self._interpolate()
        self._q = np.asarray(qvec)
        self._i = self._interp_func['i'](qvec)
        self._err = self._interp_func['err'](qvec)

    def reset(self):
        self._q = self._raw_q
        self._i = self._raw_i
        self._err = self._raw_err


class IFTM(Base):
    """Inverse Fourier Tranform Measurement (IFTM)"""

    def __init__(self, r, pr, error, q_orig, i_orig, err_orig, i_fit, q_extrap, i_extrap, params):
        self._raw_r = self._r = np.array(r)
        self._raw_pr = self._pr = np.array(pr)
        self._raw_error = self._error = np.array(error)
        self._raw_q_orig = self._q_orig = np.array(q_orig)
        self._raw_i_orig = self._i_orig = np.array(i_orig)
        self._raw_err_orig = self._err_orig = np.array(err_orig)
        self._raw_i_fit = self._i_fit = np.array(i_fit)

        self._raw_q_extrap = self._q_extrap = np.array(q_extrap)
        self._raw_i_extrap = self._i_extrap = np.array(i_extrap)

        self._parameters = params.copy()

    def _update(self):
        pass

    @property
    def r(self):
        return self._r

    @property
    def pr(self):
        return self._pr

    @property
    def error(self):
        return self._error

    @property
    def q_orig(self):
        return self._q_orig

    @property
    def i_orig(self):
        return self._i_orig

    @property
    def err_orig(self):
        return self._err_orig

    @property
    def q_extrap(self):
        return self._q_extrap

    @property
    def i_extrap(self):
        return self._i_extrap

    def get_parameter(self, key, default=None):
        return self._parameters.get(key, default)

    def normalized_pr(self):
        area = np.trapz(self._pr, x=self._r)
        self._pr /= area
        if self._error is not None:
            self._error /= area
        # return normalized_pr

    # def real_space_rg(self):
    #     """
    #     The radius of gyration of this distance distribution, which is calculated as the integral of P(r) with respect
    #     to distances**2 after the distribution is normalized to unity area.
    #     """
    #     # Can't be sure if this distribution is unity area
    #     area = np.trapz(self.pvals, x=self.distances)
    #     d2 = np.square(self.distances)
    #     return np.trapz(self.pvals / area, x=d2)


class SECM(Base):
    """SEC-SAS Measurement (SECM)"""
    pass
