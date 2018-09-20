from __future__ import print_function, division, absolute_import

import os
import glob
from copy import deepcopy
from functools import lru_cache
from collections import Iterable

import numpy as np

from sasdash.saslib import sasio, image, cormap
from sasdash.utils import parse_yaml, to_basic_type


class Experiment(object):
    def __init__(self, config, name=None, **kwargs):
        self._config = config
        if 'description' not in self._config:
            self._config['description'] = 'Description, comments or summary for this experiment'

        self._name = name

        # check essential parameter
        self._extensions = {
            'subtracted_files': '.dat',
            'gnom_files': '.out',
            'image_files': '.tif'
        }

        self._GnomFileDir = 'GNOM'
        self._SubtractedFileDir = 'Subtracted'
        self._ImageFileDir = 'Data'
        self._file_subdir = {
            'image_files': self._ImageFileDir,
            'subtracted_files': self._SubtractedFileDir,
            'gnom_files': self._GnomFileDir,
        }
        self._file_ext = {
            'image_files': '.tif',
            'subtracted_files': '.dat',
            'gnom_files': '.out',
        }

        # search root_path
        self._root_path = self._config['root_path']
        self._registered_setup = {}
        self._registered_dir = {}

        if isinstance(self._root_path, str):
            self._search_run_dir(self._root_path)
        elif isinstance(self._root_path, Iterable):
            for each in self._root_path:
                self._search_run_dir(each)

    def _search_run_dir(self, dir_path):
        # TODO: improve this if os.walk() costs too much time.
        for path, _, files in os.walk(dir_path):
            for each_file in files:
                if each_file.lower() == 'setup.yml':
                    dir_name = os.path.basename(path)
                    setup_file = os.path.join(path, each_file)
                    self._registered_setup[dir_name] = setup_file
                    self._registered_dir[dir_name] = path

    @property
    def name(self):
        return self._name

    @property
    def config(self):
        return self._config

    @property
    def registered_setup(self):
        return self._registered_setup

    def get_config_parameter(self, run, key):
        # FIXME: undefined method (if config.yml doesn't exist?)
        config_file = os.path.join(self._registered_dir[run], 'config.yml')
        config_dict = parse_yaml(config_file)
        return config_dict.get(key, None)

    def get_setup_parameter(self, run, key):
        setup = self.registered_setup[run]
        setup_dict = parse_yaml(setup)
        return setup_dict.get(key, None)

    @lru_cache()
    def get_prev_next(self, run_name):
        all_run = list(self._registered_dir.keys())
        all_run.sort()
        idx = all_run.index(run_name)
        if idx == 0:
            return None, all_run[1]
        elif idx == len(all_run) - 1:
            return all_run[-2], None
        else:
            return all_run[idx - 1], all_run[idx + 1]

    def get_dir_path(self, run_name):
        return self._registered_dir[run_name]

    def get_parameter(self, key):
        return self._config.get(key)

    # ==================== Data function ============================ #
    def get_files(self, run_name, file_type):
        """Return full path of files as a list.

        Parameters
        ----------
        run_name : str
            registered directory name of run
        file_type : str
            option - ['subtracted_files', 'gnom_files', 'image_files']

        Returns
        -------
        list :
            path of files
        """
        pattern = os.path.join(
            self._registered_dir[run_name],
            self._file_subdir[file_type],
            '*{}'.format(self._file_ext[file_type]),
        )
        files = glob.glob(pattern)
        files.sort()
        # remove buffer file
        if 'image' in file_type:
            for each in reversed(files):
                if 'buffer' in each.lower():
                    files.remove(each)
        # FIXME: do something (warn or raise error) if file list is empty.
        # if not files:
        #     raise ValueError('No files found.')
        return files

    # =============== 1D Profile ==================================== #
    @lru_cache()
    def get_sasprofile(self, run_name):
        pattern = os.path.join(self._registered_dir[run_name],
                               self._file_subdir['subtracted_files'],
                               '*%s' % self._file_ext['subtracted_files'])
        profile_files = glob.glob(pattern)
        profile_files.sort()
        return [sasio.load_dat(f) for f in profile_files]  # sasm_list

    @lru_cache()
    def get_gnom(self, run_name):
        pattern = os.path.join(self._registered_dir[run_name],
                               self._file_subdir['gnom_files'],
                               '*%s' % self._file_ext['gnom_files'])
        gnom_files = glob.glob(pattern)
        gnom_files.sort()
        return [sasio.load_out(f) for f in gnom_files]  # sasm_list

    # ============== Image related ================================== #
    @lru_cache()
    def get_boxed_mask(self, run_name):
        raise NotImplementedError()

    def get_sasimage(self, run, image_fname):
        raise NotImplementedError()

    # =============== CorMap Heatmap ================================ #
    def get_cormap_heatmap(self, run_name, heatmap_type='adj Pr(>C)'):
        """Return CorMap heatmap.

        Parameters
        ----------
        run_name : str
            registered directory name of run
        heatmap_type : str
            options 'C', 'Pr(>C)', 'adj Pr(>C)'

        Returns
        -------
        np.ndarray
            2D matrix of CorMap heatmap
        """
        filelist = self.get_files(run_name, 'subtracted_files')
        heatmap = cormap.calc_cormap_heatmap(filelist)
        return heatmap[heatmap_type]


class PrimusExperiment(Experiment):
    def __init__(self, config, name=None, **kwargs):
        super(PrimusExperiment, self).__init__(config, **kwargs)

        # general config (image center)
        self._default_box_radius = 150

        # generate cfg settings
        # TODO: if raw_cfg is missing?
        if 'raw_cfg' not in self._config:
            raise ValueError('No raw_cfg specified in experiment config file')
        self._raw_cfg = deepcopy(self._config['raw_cfg'])

        # check config
        minimal_config = (
            'cfg_path',
            'mask_npy',
            'MaskDimension',
            'Xcenter',
            'Ycenter',
        )
        for cfg_name, cfg_dict in self._raw_cfg.items():
            if cfg_dict is not None:
                for expected in minimal_config:
                    if expected not in cfg_dict:
                        raise ValueError("no '{}' in {} configuration.".format(expected, cfg_name))

                # convert '(111, 222)' str to tuple (111, 222)
                cfg_dict['MaskDimension'] = tuple(
                    map(to_basic_type,
                        cfg_dict['MaskDimension'].strip('()').split(','))
                )

                cfg_dict['xy_center'] = (cfg_dict['Xcenter'], cfg_dict['Ycenter'])
                cfg_dict['rc_center'] = (
                    cfg_dict['MaskDimension'][0] - cfg_dict['Ycenter'],
                    cfg_dict['Xcenter']
                )

                cfg_dict['boxed_mask'] = image.boxslice(
                    np.load(cfg_dict['mask_npy']),
                    cfg_dict['rc_center'],
                    self._default_box_radius,
                )

                cfg_dict['boxed_rc_center'] = tuple(
                    min(c, self._default_box_radius)
                    for c in cfg_dict['rc_center']
                )
            else:
                self._raw_cfg[cfg_name] = {}

        all_raw_cfg_names = list(self._raw_cfg.keys())
        all_raw_cfg_names.sort()

        self._default_raw_cfg = all_raw_cfg_names[-1]

        # x_center = int(self._raw_simulator.get_raw_settings_value('Xcenter'))
        # y_center = int(self._raw_simulator.get_raw_settings_value('Ycenter'))
        # image_dim = tuple(
        #     int(v) for v in self._raw_simulator.get_raw_settings_value(
        #         'MaskDimension'))

        # col_center = x_center
        # row_center = image_dim[0] - y_center
        # self.center = [row_center, col_center]
        # self.radius = 150

        # mask = self._raw_simulator.get_raw_settings_value('BeamStopMask')
        # if mask is None:
        #     mask = self._raw_simulator.get_raw_settings_value('Masks')[
        #         'BeamStopMask']
        # self.boxed_mask = image.boxslice(mask, self.center, self.radius)

    def get_raw_cfg(self, run_name):
        raw_cfg_name = self.get_setup_parameter(run_name, 'raw_cfg')
        if raw_cfg_name is not None:
            raw_cfg_name = os.path.basename(os.path.splitext(raw_cfg_name)[0])
        else:
            raw_cfg_name = self._default_raw_cfg
        return self._raw_cfg[raw_cfg_name]

    @lru_cache()
    def get_raw_cfg_param(self, run_name, key):
        raw_cfg = self.get_raw_cfg(run_name)
        return raw_cfg.get(key)

    def get_sasimage(self, run, image_fname):
        image_filepath = os.path.join(self._root_path, run,
                                      self._ImageFileDir, image_fname)

        rc_center = self.get_raw_cfg_param(run, 'rc_center')

        img = image.boxslice(
            sasio.load_pilatus_image(image_filepath),
            rc_center,
            self._default_box_radius,
        ) * self.get_raw_cfg_param(run, 'boxed_mask')

        return img


class Playground(Experiment):
    def __init__(self):
        self._root_path = './'

    def get_prev_next(self, run_name):
        return None, None


class Project(object):
    def __init__(self, name, *args, **kwargs):
        self._proj_name = name
        self._exp_instance = {}

    @property
    def name(self):
        return self._proj_name

    def get(self, experiment=None):
        if experiment is None:  # remove this
            return tuple(self._exp_instance.values())[0]
        else:
            return self._exp_instance.get(experiment)

    def get_name_experiments(self):
        return list(self._exp_instance.keys())

    def append_experiment(self, config_file, name=None, typ='SSRF'):
        config = parse_yaml(config_file)
        if name is not None:
            pass
        elif 'name' in config:
            name = config['name']
        elif 'experiment_name' in config:
            name = config['experiment_name']
        else:
            name = os.path.basename(os.path.splitext(config_file)[0])
        self._exp_instance[name] = PrimusExperiment(config, name=name)

    def get_all_setup(self, experiment):
        return self.get(experiment).registered_setup.values()

    def get_prev_next(self, experiment, run):
        return self.get(experiment).get_prev_next(run)


class Warehouse(object):
    def __init__(self):
        playground_save_dir = './'
        self._exp_instance = {'playground': Playground()}
        self._prj_instance = {}

    def get(self, project=None):
        if project is None:  # FIXME: remove this
            return tuple(self._prj_instance.values())[0]
        else:
            return self._prj_instance.get(project)


    def get_name_projects(self):
        return list(self._prj_instance.keys())

    def get_name_experiments(self, project):
        return self.get(project).get_name_experiments()

    def get_parameter(self, project, experiment, key):
        return self.get(project).get(experiment).get_parameter(key)

    def append_project(self, name):
        if name not in self._prj_instance:
            self._prj_instance[name] = Project(name)

    def append_experiment(self, project, config_file, name=None):
        self.get(project).append_experiment(config_file, name)

    def get_prev_next(self, project, experiment, run):
        return self.get(project).get_prev_next(experiment, run)

    def get_all_setup(self, project, experiment):
        return self.get(project).get_all_setup(experiment)

    def get_dir_path(self, project, experiment, run):
        return self.get(project).get(experiment).get_dir_path(run)

    # =================== dashboard data ============================ #
    def get_sasprofile(self, project, experiment, run):
        return self.get(project).get(experiment).get_sasprofile(run)

    def get_gnom(self, project, experiment, run):
        return self.get(project).get(experiment).get_gnom(run)

    def get_raw_cfg_param(self, project, experiment, run, key):
        return self.get(project).get(experiment).get_raw_cfg_param(run, key)

    def get_files(self, project, experiment, run, file_type):
        return self.get(project).get(experiment).get_files(run, file_type)

    def get_sasimage(self, project, experiment, run, image_fname):
        return self.get(project).get(experiment).get_sasimage(run, image_fname)

    def get_cormap_heatmap(self, project, experiment, run, heatmap_type):
        return self.get(project).get(experiment).get_cormap_heatmap(run, heatmap_type)


warehouse = Warehouse()
