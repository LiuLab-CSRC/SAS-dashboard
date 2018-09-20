from __future__ import print_function, division, absolute_import

from urllib import parse
import json

from dash.dependencies import Input, Output

from .layouts import registered_layouts
from .base import dash_app


def get_graph_layout(layout_type):
    if layout_type in registered_layouts:
        return registered_layouts[layout_type]()
    else:
        return '404'


@dash_app.callback(Output('page-content', 'children'), [Input('url', 'href')])
def display_page(href):
    if href is not None:
        query_result = parse.parse_qs(parse.urlparse(href).query)
        layout_type = query_result['graph_type'][0]
        return get_graph_layout(layout_type)
    else:
        return '404'


@dash_app.callback(Output('page-info', 'children'), [Input('url', 'href')])
def set_page_info(href):
    if href is not None:
        query_result = parse.parse_qs(parse.urlparse(href).query)
        info = {key: val[0] for key, val in query_result.items()}
        return json.dumps(info)
    else:
        return '404'


if __name__ == '__main__':
    dash_app.run_server(debug=False)
