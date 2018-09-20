REGISTERED_LAYOUTS = {
    'sasimage': 'SAS Image',
    'sasprofile': 'SAS Profile',
    'cormap': 'Correlation Map (NotImplemented)',
    'cormap_heatmap': 'CorMap Heatmap',
    'series_analysis': 'Series Analysis',
    'guinier': 'Guinier Fitting',
    'gnom': 'Pair-wise Distribution (GNOM)',
    'mw': 'Molecular Weight',
    'colormap': 'Colormap and Crossline',
}

DOWNLOADABLE = {
    'sasprofile': True,
    'gnom': True,
}

SUBFOLDER = {
    'sasprofile': 'Subtracted',
    'gnom': 'GNOM',
}

LAYOUT_OPTIONS = (
    ('sasimage', 'SAS Images'),
    ('sasprofile', 'SAS Profile'),
    ('cormap', 'Correlation Map (NotImplemented)'),
    ('cormap_heatmap', 'CorMap Heatmap'),
    ('series_analysis', 'Series Analysis'),
    ('guinier', 'Guinier Analysis'),
    ('gnom', 'GNOM'),
    ('mw', 'Molecular Weight (NotImplemented)'),
    ('colormap', 'Colormap and Crossline'),
)

LYAOUT_SEQUENCE = {
    'sasimage': 1,
    'sasprofile': 2,
    'series_analysis': 3,
    'cormap': 4,
    'cormap_heatmap': 5,
    'guinier': 6,
    'gnom': 7,
    'colormap': 8,
    'mw': 9,
}

sort_seq = lambda key: LYAOUT_SEQUENCE.get(key, 1000)
