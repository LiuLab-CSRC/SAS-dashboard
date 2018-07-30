from __future__ import print_function, division, absolute_import

import os
import glob
from functools import lru_cache

from sasdash.saslib import sasio
from sasdash.saslib import image
from sasdash.utils import parse_yaml


class Experiment(object):
    def __init__(self, config, name=None, **kwargs):
        self._config = config
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
        self._registered_setup = []
        self._registered_dir = {}
        # TODO: improve this if os.walk() costs too much time.
        for path, _, files in os.walk(self._root_path):
            for each_file in files:
                if each_file.lower() == 'setup.yml':
                    self._registered_setup.append(os.path.join(path, each_file))
                    dir_name = os.path.basename(path)
                    self._registered_dir[dir_name] = path

    @property
    def name(self):
        return self._name

    @property
    def registered_setup(self):
        return self._registered_setup

    def get_prev_next(self, run_name):
        all_run = list(self._registered_dir.keys())
        idx = all_run.index(run_name)
        if idx == 0:
            return None, all_run[1]
        elif idx == len(all_run) - 1:
            return all_run[-2], None
        else:
            return all_run[idx - 1], all_run[idx + 1]

    def get_dir_path(self, run_name):
        return self._registered_dir[run_name]

    @lru_cache()
    def get_sasprofile(self, run_name):
        pattern = os.path.join(self._registered_dir[run_name],
                               self._file_subdir['subtracted_files'],
                               '*%s' % self._file_ext['subtracted_files'])
        dat_files = glob.glob(pattern)
        dat_files.sort()
        return [sasio.load_dat(f) for f in dat_files]  # sasm_list

    def get_files(self, run_name, file_type):
        """Return full path of files as a list.

        Parameters
        ----------
        run_name : str
            registered sub directory name
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


class PrimusExperiment(Experiment):
    def __init__(self, config_file, name=None, **kwargs):
        super(PrimusExperiment, self).__init__(config_file, **kwargs)


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

    def append_experiment(self, config_file, name=None):
        config = parse_yaml(config_file)
        if name is not None:
            pass
        elif 'name' in config:
            name = config.name
        else:
            name = os.path.basename(os.path.splitext(config_file)[0])
        self._exp_instance[name] = PrimusExperiment(config, name=name)

    def get_all_setup(self, experiment):
        return self._exp_instance[experiment].registered_setup

    def get_dir_path(self, experiment, run):
        return self._exp_instance[experiment].get_dir_path(run)

    def get_sasprofile(self, experiment, run):
        return self._exp_instance[experiment].get_sasprofile(run)

    def get_prev_next(self, experiment, run):
        return self._exp_instance[experiment].get_prev_next(run)


class Warehouse(object):
    def __init__(self):
        playground_save_dir = './'
        self._exp_instance = {'playground': Playground()}
        self._prj_instance = {}

    def append_project(self, name):
        self._prj_instance[name] = Project(name)

    def append_experiment(self, project, config_file, name=None):
        self._prj_instance.get(project).append_experiment(config_file, name)

    def get_all_setup(self, project, experiment):
        return self._prj_instance.get(project).get_all_setup(experiment)

    def get_dir_path(self, project, experiment, run):
        return self._prj_instance.get(project).get_dir_path(experiment, run)

    def get_sasprofile(self, project, experiment, run):
        return self._prj_instance.get(project).get_sasprofile(experiment, run)

    def get_prev_next(self, project, experiment, run):
        return self._prj_instance.get(project).get_prev_next(experiment, run)


warehouse = Warehouse()
warehouse.append_project('projname')
warehouse.append_experiment(
    'projname', r'experiment_config.yml',
    'expname')


class Simulator():
    _CACHED_ANALYSES = [
        'sasimage',
        'cormap',
        'cormap_heatmap',
        'sasprofile',
        'series_analysis',
        'gnom',
        'subtracted_files',
        'gnom_files',
        'image_files',
    ]

    def __init__(self):
        # FIXME: set RAW cfg path
        cfg_path = None
        self._raw_simulator = RAWSimulator(cfg_path)

        self._warehouse = {key: {} for key in self._CACHED_ANALYSES}
        self._root_dir = None

        x_center = int(self._raw_simulator.get_raw_settings_value('Xcenter'))
        y_center = int(self._raw_simulator.get_raw_settings_value('Ycenter'))
        image_dim = tuple(
            int(v) for v in self._raw_simulator.get_raw_settings_value(
                'MaskDimension'))

        col_center = x_center
        row_center = image_dim[0] - y_center
        self.center = [row_center, col_center]
        self.radius = 150

        mask = self._raw_simulator.get_raw_settings_value('BeamStopMask')
        if mask is None:
            mask = self._raw_simulator.get_raw_settings_value('Masks')[
                'BeamStopMask']
        self.boxed_mask = image.boxslice(mask, self.center, self.radius)

    def get_gnom(self, exp):
        if exp not in self._warehouse['gnom']:
            gnom_files = self.get_files(exp, 'gnom_files')
            self._warehouse['gnom'][exp] = self._raw_simulator.loadIFTMs(
                gnom_files)
        return self._warehouse['gnom'][exp]

    def get_sasprofile(self, exp):
        if exp not in self._warehouse['sasprofile']:
            sasm_files = self.get_files(exp, 'subtracted_files')
            self._warehouse['sasprofile'][exp] = self._raw_simulator.loadSASMs(
                sasm_files)
        return self._warehouse['sasprofile'][exp]

    def load_image(self, image_file):
        with Image.open(image_file) as opened_image:
            image = image.boxslice(
                np.fliplr(np.asarray(opened_image, dtype=float)),
                self.center,
                self.radius,
            ) * self.boxed_mask
        return image

    def get_sasimage(self, exp, image_fname):
        if exp not in self._warehouse['sasimage']:
            self._warehouse['sasimage'][exp] = {}
        if image_fname not in self._warehouse['sasimage'][exp]:
            image_file_path = os.path.join(self._root_dir, exp,
                                           self._ImageFileDir, image_fname)
            self._warehouse['sasimage'][exp][image_fname] = self.load_image(
                image_file_path)
        return self._warehouse['sasimage'][exp][image_fname]

    def get_cormap_heatmap(self, exp, heatmap_type):
        """Return CorMap heatmap.

        Parameters
        ----------
        exp : [type]
            [description]
        heatmap_type : str
            options 'C', 'Pr(>C)', 'adj Pr(>C)'
        Returns
        -------
        np.ndarray
            2D matrix of CorMap heatmap
        """
        if exp not in self._warehouse['cormap_heatmap']:
            self._warehouse['cormap_heatmap'][exp] = self.calc_cormap_heatmap(
                exp)
        return self._warehouse['cormap_heatmap'][exp][heatmap_type]

    def reset_exp(self, exp: int):
        for key in self._CACHED_ANALYSES:
            if exp in self._warehouse[key]:
                self._warehouse[key].pop(exp)


# raw_simulator = Simulator()
