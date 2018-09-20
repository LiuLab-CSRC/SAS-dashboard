# SAS Dashboard

Represent and analyse your Small Angle Scattering (SAS) data.

README: [English](./README.md), 中文

## 环境依赖

使用 `pip` 安装依赖的库:

    pip install -r requirements.txt

使用 `conda` 环境:

    conda install --file requirements.txt

## 使用指南

    python run.py /path/to/experiment-setup-1.yml /path/to/another-experiment-setup-2.yml

实验配置文件示例 `SSRF-MagR-201805.yml`:

    project_name: MagR
    experiment_name: SSRF-MagR-201805
    experiment_facility: SSRF
    experiment_date: May 04~05, 2018
    participants: Haiguang Liu, Can Xie, Peiling Yang, Yingchen Shi, Lanqing Huang, Siyin Qin, Zhen Guo, Xiaotian Wang
    description: Description, comments or summary for this experiment

    # sample_list:  # useless for now

    root_path: /path/to/SSRF/SSRF-MagR-201805/Analysis/Experiments
    # or
    root_path: ['Day_1_data', 'Day_2_data']
    # or
    root_path:
        - 'Day_1_data'
        - 'Day_2_data'

    default_raw_cfg: '20180503-recentering-remasking'
    raw_cfg:
        '20180503':
            cfg_path: ???
            mask_npy: ???
            MaskDimension: (1043, 981)
            Xcenter: ???
            Ycenter: ???
        '20180503-recentering-remasking':
            cfg_path: path/to/SSRF-MagR-201805/cfg/20180503-recentering-remasking.cfg
            mask_npy: path/to/SSRF-MagR-201805/cfg/20180503-recentering-remasking-BeamStopMask.npy
            MaskDimension: (1043, 981)
            Xcenter: 359
            Ycenter: 914

图像的实际中心为:

    (row_center, col_center) = (MaskDimension[0] - Ycenter, Xcenter)

`RAW` 配置鉴于有可能会有多个 RAW 的配置文件 `.cfg`，因此可以通过 `default_raw_cfg` 设定默认的 RAW 配置文件。当需要获取特定 `run` 的 `RAW` 配置时会去 `run` 文件夹里的 `config.yml` 中寻找 `raw_cfg` 设置，如果不存在 `raw_cfg` 的信息就将使用默认的 `default_raw_cfg`。

### 组织结构

`Project` 由 `Experiment` 组成，`Experiment` 由 `Run` 组成。每个 `Run` 包含每次的采集的实验数据。

    Project-Name (eg: 'MagR')
    |- project_settings.yml
    |- Experiment-1 (eg: 'SSRF-MagR-201803')
       |- expperiment-settings-1.yml
       |- Run-1 (eg: EXP01)
       |- Run-2 (eg: EXP02)
          |- Processed
          ...
          |- Subtracted
          |- config.yml
          |- setup.yml
       |- Run-3
       ...
       |- Run-39
       |- Run-40
    |- Experiment-2 (eg: 'SSRF-MagR-201805')
       |- experiment-settings-2.yml
       |- Run-01
       |- Run-02
       ...
       |- Run-49
       |- Run-50

在 `experiment-settings-1.yml` 中设定好 `root_path` 后，`sasdash` 会遍历 `root_path` 中的所有子目录去寻找所有的 `setup.yml`，默认将使用 `setup.yml` 所在的目录视为单个 `run` 的根目录。

`setup.yml` 示例:

    number: 27
    sample: nano magnetic beads
    concentration: 1.0 # mg/ml
    magnetic_field: True
    magnet_distance: None / 60 # mm
    duration: 6 # minuntes
    exposure_mode: automatic
    exposure_time: 1.0 # second / per frame
    frames: 40
    description: None
    extra_info: None
    simple_conclusion: Undone

可以添加更多有效详细的信息。
