import sys
from sasdash import sasdash_app
from sasdash.datamodel import warehouse
from sasdash.utils import parse_yaml

if __name__ == '__main__':
    if len(sys.argv) > 1:
        for config_file in sys.argv[1:]:
            experiment_config = parse_yaml(config_file)
            project = experiment_config['project_name']
            experiment = experiment_config['experiment_name']

            warehouse.append_project(project)
            warehouse.append_experiment(project, config_file, name=experiment)

    sasdash_app.run(debug=True)
