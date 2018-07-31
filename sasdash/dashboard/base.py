from __future__ import print_function, division

import dash
import dash_core_components as dcc
import dash_html_components as html
from flask import url_for

from sasdash.webapp.app import flask_app

DASH_URL_BASE = '/dashboard'
dash_app = dash.Dash(
    __name__, server=flask_app, url_base_pathname=DASH_URL_BASE)
# flask_app = dash_app.server

dash_app.config.update({
    # Since we're adding callbacks to elements that don't exist in the
    # app.layout, Dash will raise an exception to warn us that we might
    # be doing something wrong. In this case, we're adding the elements
    # through a callback, so we can ignore the exception.
    'suppress_callback_exceptions': True,
})
"""
<script src='https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML' async></script>
"""
# mathjax_js = 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML'
# mathjax_js = '/static/js/MathJax.js?config=TeX-MML-AM_CHTML'
# dash_app.scripts.append_script({'external_url': mathjax_js})
# dash_app.footer = [
#     html.Script(type='text/javascript', src=mathjax_js)  #async='async')
# ]

# # Append an externally hosted CSS stylesheet
# dash_app.css.append_css({
#     'external_url': (
#         # url_for('static', filename='css/bWLwgP.css'),
#         # url_for('static', filename='css/dash.css'),
#         '/static/css/bWLwgP.css',
#         '/static/css/dash.css',
#     )
# })

dash_app.css.config.serve_locally = True
dash_app.scripts.config.serve_locally = True

dash_app.layout = html.Div(children=[
    # FIXME: fix this hard coding path (/static)
    html.Link(rel='stylesheet', href='/static/css/bWLwgP.css'),
    html.Link(rel='stylesheet', href='/static/css/brPBPO.css'),  # fade in while loading
    html.Link(rel='stylesheet', href='/static/css/dash.css'),
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-info', style={'display': 'none'}),
    html.Div(id='page-content'),
])
