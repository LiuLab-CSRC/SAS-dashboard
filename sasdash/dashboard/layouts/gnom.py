from __future__ import print_function, division

import os.path
import json

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from sasdash.datamodel import warehouse

from .style import XLABEL, YLABEL, TITLE, INLINE_LABEL_STYLE
from .style import GRAPH_GLOBAL_CONFIG
from ..base import dash_app

_PLOT_OPTIONS = [{
    'label': 'P(r) distribution',
    'value': 'pr_distribution'
}, {
    'label': 'Fitting curve',
    'value': 'fitting'
}]

_DEFAULT_LAYOUT = html.Div(children=[
    dcc.Graph(
        id='gnom-graph',
        figure={'data': ()},
        config=GRAPH_GLOBAL_CONFIG,
    ),
    html.Label('Plot type'),
    dcc.RadioItems(
        id='gnom-plot-type',
        options=_PLOT_OPTIONS,
        value='pr_distribution',
        labelStyle=INLINE_LABEL_STYLE,
    ),
    html.Label('Select gnom file to plot'),
    dcc.Dropdown(
        id='gnom-file-selection',
        options=[],
        value=0,
    ),
])

_DEFAULT_FIGURE_LAYOUT = {
    'pr_distribution': {
        'height': 500,
        'hovermode': 'closest',
        'title': TITLE['pdf'],
        'xaxis': dict(title=XLABEL['pdf']),
        'yaxis': dict(title=YLABEL['pdf']),
    },
    'fitting': {
        'height': 500,
        # 'hovermode': 'closest',
        'title': TITLE['fitting'],
        'xaxis': dict(title=XLABEL['linear']),
        'yaxis': dict(title=YLABEL['log'], type='log'),
    },
}


def get_gnom():
    return _DEFAULT_LAYOUT


@dash_app.callback(
    Output('gnom-file-selection', 'options'), [Input('page-info', 'children')])
def _update_file_selection(info_json):
    info = json.loads(info_json)
    project, experiment, run = info['project'], info['experiment'], info['run']
    file_list = warehouse.get_files(project, experiment, run, 'gnom_files')
    file_basename = (os.path.basename(each) for each in file_list)
    if file_list:
        return [{
            'label': each,
            'value': i,
        } for i, each in enumerate(file_basename)]
    else:
        return [{
            'label': 'No GNOM files found.',
            'value': 0,
        }]


@dash_app.callback(
    Output('gnom-graph', 'figure'),
    [
        Input('gnom-plot-type', 'value'),
        Input('gnom-file-selection', 'value'),
        Input('page-info', 'children'),
    ],
)
def _update_figure(plot_type, iftm_index, info_json):
    info = json.loads(info_json)
    project, experiment, run = info['project'], info['experiment'], info['run']
    iftm_list = warehouse.get_gnom(project, experiment, run)
    if iftm_list:
        if plot_type == 'pr_distribution':
            data = [{
                'x': each_iftm.r,
                'y': each_iftm.pr,
                'type': 'line',
                'name': each_iftm.get_parameter('filename')
            } for each_iftm in iftm_list]
        elif plot_type == 'fitting':
            selected_iftm = iftm_list[iftm_index]
            data = [{
                'x': selected_iftm.q_orig,
                'y': selected_iftm.i_orig,
                'type': 'line',
                'name': selected_iftm.get_parameter('filename'),
            }, {
                'x': selected_iftm.q_extrap,
                'y': selected_iftm.i_extrap,
                'type': 'line',
                'name': 'fitting result',
            }]

        return {
            'data': data,
            'layout': _DEFAULT_FIGURE_LAYOUT[plot_type],
        }
    else:
        return {
            'layout': {
                'annotations': [{
                    'text': 'No GNOM files found.',
                    'showarrow': False
                }]
            },
        }
