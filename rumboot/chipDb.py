import yaml
from os import listdir
from os.path import join, isfile, dirname


class ChipDb:

    chips = {}
    params_cfg_name = "chips_parameters.yml"

    def __init__(self, path):
        if len(self.chips) == 0:
            path = path.split(".")
            root = dirname(dirname(__file__))
            path = join(root, *path)
            with open(join(path, self.params_cfg_name), 'r') as f:
                params = yaml.safe_load(f)

            yamles = [
                f for f in listdir(path) if isfile(join(path, f)) and \
                f.endswith(".yml") and f != self.params_cfg_name
            ]

            for yml in yamles:
                with open(join(path, yml), 'r') as f:
                    chips = yaml.load_all(f, Loader = yaml.SafeLoader)
                    for chip in chips:
                        if chip.chip_id in self.chips:
                            print(
                                "Warning! Duplicate for chip",
                                f"with id [{chip.chip_id}] was found in file [{yml}],",
                                "please check chip config files"
                            )
                        else:
                            invalid_attrs = \
                                set(chip.__dict__) - set(params['required'] + params['optional'])
                            if invalid_attrs:
                                print(
                                    f"Found invalid parameters for chip [{chip.name}]: {invalid_attrs}"
                                )
                                continue
                            missing_attrs = \
                                set(params['required']).difference(set(chip.__dict__))
                            if missing_attrs:
                                print(
                                    f"Found missing parameters for chip [{chip.name}]: {missing_attrs}"
                                )
                                continue
                            self.chips[chip.chip_id] = chip

    def __getitem__(self, key):
        if key in self.chips:
            return self.chips[key]
        return None


class Chip(yaml.YAMLObject):
    yaml_tag = '!Chip'
    yaml_loader = yaml.SafeLoader
