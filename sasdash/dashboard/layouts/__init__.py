from __future__ import print_function, division, absolute_import

from .sasimage import get_sasimage
from .sasprofile import get_sasprofile
from .cormap import get_cormap
from .series_analysis import get_series_analysis
from .guinier import get_guinier
from .colormap import get_colormap
from .gnom import get_gnom

LAYOUT_OPTIONS = (
    ('sasimage', 'SAS Images'),
    ('sasprofile', 'SAS Profile'),
    ('cormap', 'CorMap Analysis'),
    ('series_analysis', 'Series Analysis'),
    ('guinier', 'Guinier Analysis'),
    ('gnom', 'GNOM'),
    ('colormap', 'Colormap and Crossline'),
)

registered_layouts = {
    'sasimage': get_sasimage,
    'sasprofile': get_sasprofile,
    'cormap': get_cormap,
    'series_analysis': get_series_analysis,
    'guinier': get_guinier,
    'gnom': get_gnom,
    'colormap': get_colormap,
}
