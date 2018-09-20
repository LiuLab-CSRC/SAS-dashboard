from __future__ import print_function, division, absolute_import

import os
import glob
import zipfile

from flask import Blueprint
from flask import render_template, redirect, request, jsonify, url_for
from flask import send_from_directory, send_file

from sasdash.utils import to_basic_type, parse_yaml, dump_yaml, yaml
from sasdash.datamodel import warehouse
from sasdash.base import REGISTERED_LAYOUTS, DOWNLOADABLE, SUBFOLDER, sort_seq

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
    config = warehouse.get().get().config.copy()
    for key, val in config.items():
        if not isinstance(val, (str, float, int)):
            from io import StringIO
            s = StringIO()
            yaml.dump(val, s)
            s.seek(0)
            config[key] = ''.join(s.readlines())
    settings_form = ExperimentSettingsForm(config)
    samples_info_form = SampleInfoForm()
    return render_template(
        'exp_settings.html',
        settings_form=settings_form,
        samples_info_form=samples_info_form,
    )


@exp_pages.route('/exp_cards')
@exp_pages.route('/exp_pages')
@exp_pages.route('/exp_pages/<string:project>', defaults={'experiment': None})
@exp_pages.route('/exp_pages/<string:project>/<string:experiment>')
def show_exp_cards(project: str = None, experiment: str = None):
    # TODO and FIXME: need a better way to set project and experiment
    # FIXME: only run with one project
    if project is None:
        all_projects = warehouse.get_name_projects()
        if not all_projects:
            return "Sorry. No projects found."
        else:
            prj = all_projects[0]

    if experiment is None:
        all_experiments = warehouse.get_name_experiments(prj)

    exp_run_list = []
    for exp in all_experiments:
        exp_dict = {
            'name': exp,
            'description': warehouse.get_parameter(prj, exp, 'description'),
        }
        setup_files = warehouse.get_all_setup(prj, exp)
        per_dict_list = [{
            'project': prj,
            'experiment': exp,
            'run': os.path.basename(os.path.dirname(filepath))
        } for filepath in setup_files]
        run_setup_list = [parse_yaml(filepath) for filepath in setup_files]
        run_table_list=enumerate(zip(per_dict_list, run_setup_list))
        exp_run_list.append((exp_dict, run_table_list))

    return render_template(
        'exp_cards.html',
        project=prj,
        exp_run_list=exp_run_list,
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
    prj_exp_run = {'project': project, 'experiment': experiment, 'run': run}
    dir_path = warehouse.get_dir_path(**prj_exp_run)

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
        run_config = parse_yaml(config_file)
        if 'layouts' not in run_config:
            run_config['layouts'] = ()
    else:
        run_config = {'layouts': ()}
    checkbox_prefix = 'checkbox'
    layouts_checkbox = LayoutConfigCheckbox(
        run_config['layouts'], prefix=checkbox_prefix)

    # process submit action
    if setup_form.validate_on_submit():
        for prefix_key, value in request.form.items():
            if setup_prefix:
                key = prefix_key.split('%s-' % setup_prefix)[1]
            if key not in ('csrf_token', 'submit', 'custom_params'):
                key = key.lower().replace(' ', '_')
                exp_setup[key] = to_basic_type(value)
        dump_yaml(exp_setup, setup_file)
        return redirect(url_for('.individual_page', **prj_exp_run))

    if (layouts_checkbox.generate.data
            and layouts_checkbox.validate_on_submit()):
        curr_layouts = []
        for prefix_key in request.form.keys():
            if checkbox_prefix:
                key = prefix_key.split('%s-' % checkbox_prefix)[1]
            if key not in ('csrf_token', 'generate'):
                curr_layouts.append(key)
        curr_layouts.sort(key=sort_seq)  # sort sequence of graphs
        run_config['layouts'] = curr_layouts
        dump_yaml(run_config, config_file)
        # TODO: reset_exp(run)
        return redirect(url_for('.individual_page', **prj_exp_run))

    # create info for rendering
    if run_config['layouts']:
        show_dashboard = True
        selected_graph = run_config['layouts']
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
    prj_exp_run = {'project': project, 'experiment': experiment, 'run': run}
    directory = warehouse.get_dir_path(**prj_exp_run)
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
