import yaml

def load_yaml_from_file(file_path):
    with open(file_path, 'r') as stream:
        env = yaml.safe_load(stream)
    return env
