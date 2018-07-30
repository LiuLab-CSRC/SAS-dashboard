from __future__ import print_function, division, absolute_import

import os
import glob
import zipfile

from flask import Blueprint
from flask import render_template, redirect, request, jsonify, url_for
from flask import send_from_directory, send_file

from sasdash.utils import to_basic_type, parse_yaml, dump_yaml
from sasdash.datamodel import warehouse
from sasdash.base import REGISTERED_LAYOUTS, DOWNLOADABLE, SUBFOLDER

from ..forms import (ExperimentSettingsForm, ExperimentSetupForm,
                     LayoutConfigCheckbox, SampleInfoForm)

exp_pages = Blueprint(
    'exp_pages',
    __name__,
    # template_folder='templates',  # Path for templates
    # static_folder='static',  # Path for static files
)


@exp_pages.route('/exp_settings', methods=('GET', 'POST'))
def experiment_settings():
    exp_settings_form = ExperimentSettingsForm()
    samples_info_form = SampleInfoForm()
    return render_template(
        'exp_settings.html',
        exp_settings_form=exp_settings_form,
        samples_info_form=samples_info_form,
    )


@exp_pages.route('/exp_pages')
@exp_pages.route('/exp_cards')
def show_exp_cards():
    setup_files = warehouse.get_all_setup('MagR', 'SSRF-SAXS-201805')
    run_list = [
        os.path.basename(os.path.dirname(filepath)) for filepath in setup_files
    ]
    exp_setup_list = [parse_yaml(filepath) for filepath in setup_files]
    return render_template(
        'exp_cards.html',
        exp_table_list=enumerate(zip(run_list, exp_setup_list)),
    )


@exp_pages.route(
    '/exp_pages/<string:experiment>/<string:run>',
    defaults={'project': None},
    methods=('GET', 'POST'),
)
@exp_pages.route(
    '/exp_pages/<string:project>/<string:experiment>/<string:run>',
    methods=('GET', 'POST'),
)
def individual_page(project: str, experiment: str, run: str):
    dir_path = warehouse.get_dir_path(project, experiment, run)

    # find and load setup/config file
    setup_file = os.path.join(dir_path, 'setup.yml')
    if os.path.exists(setup_file):
        exp_setup = parse_yaml(setup_file)
    else:
        exp_setup = {}
    setup_prefix = 'setup'
    setup_form = ExperimentSetupForm(exp_setup, prefix=setup_prefix)

    config_file = os.path.join(dir_path, 'config.yml')
    if os.path.exists(config_file):
        exp_config = parse_yaml(config_file)
        if 'layouts' not in exp_config:
            exp_config['layouts'] = ()
    else:
        exp_config = {'layouts': ()}
    checkbox_prefix = 'checkbox'
    layouts_checkbox = LayoutConfigCheckbox(
        exp_config['layouts'], prefix=checkbox_prefix)

    # process submit action
    if setup_form.validate_on_submit():
        for prefix_key, value in request.form.items():
            if setup_prefix:
                key = prefix_key.split('%s-' % setup_prefix)[1]
            if key not in ('csrf_token', 'submit', 'custom_params'):
                key = key.lower().replace(' ', '_')
                exp_setup[key] = to_basic_type(value)
        dump_yaml(exp_setup, setup_file)
        return redirect(url_for('.individual_page', project, experiment, run))

    if (layouts_checkbox.generate.data
            and layouts_checkbox.validate_on_submit()):
        curr_layouts = []
        for prefix_key in request.form.keys():
            if checkbox_prefix:
                key = prefix_key.split('%s-' % checkbox_prefix)[1]
            if key not in ('csrf_token', 'generate'):
                curr_layouts.append(key)
        exp_config['layouts'] = curr_layouts
        dump_yaml(exp_config, config_file)
        # TODO: reset_exp(run)
        return redirect(url_for('.individual_page', project, experiment, run))

    # create info for rendering
    if exp_config['layouts']:
        show_dashboard = True
        selected_graph = exp_config['layouts']
    else:
        show_dashboard = False
        dashboard_params = ()
    if show_dashboard:
        dashboard_params = [{
            'graph_type': gtype,
            'graph_name': REGISTERED_LAYOUTS[gtype],
            'downloadable': DOWNLOADABLE.get(gtype, False),
        } for gtype in selected_graph if gtype != 'exp']

    # TODO: pagination
    prev_run, next_run = warehouse.get_prev_next(project, experiment, run)

    return render_template(
        'exp_base.html',
        project=project,
        experiment=experiment,
        run=run,
        setup_form=setup_form,
        layouts_checkbox=layouts_checkbox,
        show_dashboard=show_dashboard,
        dashboard_params=dashboard_params,
        next_run=next_run,
        prev_run=prev_run,
    )


@exp_pages.route(
    '/download_files/<string:experiment>/<string:run>/<string:graph_type>',
    defaults={'project': None},
)
@exp_pages.route(
    '/download_files/<string:project>/<string:experiment>/<string:run>/<string:graph_type>'
)
def download_files(project, experiment, run, graph_type):
    directory = warehouse.get_dir_path(project, experiment, run)
    filename = os.path.join(directory, '%s_%s.zip' % (run, graph_type))
    if zipfile.is_zipfile(filename):
        return send_file(filename, as_attachment=True)
    else:
        # try to create zip file.
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except PermissionError:
                return ('Ops! PermissionError:'
                        'Failed to remove pre-exist files.')
        sub_dir = os.path.join(directory, SUBFOLDER[graph_type])
        all_files = os.listdir(sub_dir)
        if all_files:  # not empty
            all_files_path = (os.path.join(sub_dir, each)
                              for each in all_files)
            try:
                with zipfile.ZipFile(filename, 'w',
                                     zipfile.ZIP_DEFLATED) as myzip:
                    # TODO: improve encoding problem with non-latin characters
                    # Note: There is no official file name encoding for ZIP files.
                    # If you have unicode file names, you must convert them to
                    # byte strings in your desired encoding before passing them
                    # to `write()`. WinZip interprets all file names as encoded
                    # in CP437, also known as DOS Latin.
                    for fp in all_files_path:
                        myzip.write(fp, os.path.relpath(fp, directory))
            except FileExistsError:
                return 'Ops! File exists.'
            except Exception as err:
                return str(err)
            return send_file(filename, as_attachment=True)
        else:
            return 'Ops! No files found.'
