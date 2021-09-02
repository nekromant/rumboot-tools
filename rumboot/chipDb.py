import yaml
from os import listdir
from os.path import join, isfile, dirname


class ChipDb:

    chips_by_name = {}
    chips_by_id = {}
    params_cfg_name = "chips_parameters.yml"

    def __init__(self, path):
        if len(self.chips_by_name) == 0 or len(self.chips_by_id) == 0:
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
                        excess_attrs = \
                            set(chip.__dict__) - set(params['required'] + params['optional'])
                        if excess_attrs:
                            raise ExcessAttrsError(excess_attrs, chip.chip_id, yml)

                        missing_attrs = \
                            set(params['required']).difference(set(chip.__dict__))
                        if missing_attrs:
                            raise MissingAttrsError(missing_attrs, chip.chip_id, yml)

                        excess_hacks = set(chip.hacks) - set(params['hacks'])
                        if excess_hacks:
                            raise ExcessHacksError(excess_hacks, chip.chip_id, yml)

                        missing_hacks = set(params['hacks']).difference(set(chip.hacks))
                        if missing_hacks:
                            raise MissingHacksError(missing_hacks, chip.chip_id, yml)

                        if chip.name in self.chips_by_name:
                            raise MultipleChipConfigError(chip.name, chip.chip_id, yml)
                        self.chips_by_name[chip.name] = chip

                        if chip.chip_id in self.chips_by_id:
                            self.chips_by_id[chip.chip_id].append(chip)
                        else:
                            self.chips_by_id[chip.chip_id] = [chip]

    def __getitem__(self, key):
        try:
            key = int(key)
        except ValueError:
            return self.chips_by_name[key]
        else:
            chips = self.chips_by_id[key]
            if len(chips) > 1:
                raise ChipsWithSameIDError(key)
            return chips[0]


class Chip(yaml.YAMLObject):
    yaml_tag = '!Chip'
    yaml_loader = yaml.SafeLoader


class MultipleChipConfigError(Exception):
    def __init__(self, name, chip_id, filename):
        super().__init__(
            f"Found duplicate config [{filename}] for chip with name [{name}] and ID [{chip_id}]"
        )


class ChipsWithSameIDError(Exception):
    def __init__(self, ID):
        super().__init__(
            f"Found multiple chips for given ID [{ID}]"
        )


class InvalidAttrsError(Exception):
    def __init__(self, chip_id, filename, postfix):
        super().__init__(
            f"Chip with ID [{chip_id}] in file [{filename}] {postfix}"
        )


class MissingHacksError(InvalidAttrsError):
    def __init__(self, hacks, chip_id, filename):
        super().__init__(chip_id, filename, f"has missing hacks [{hacks}]")


class ExcessHacksError(InvalidAttrsError):
    def __init__(self, hacks, chip_id, filename):
        super().__init__(chip_id, filename, f"has excess hacks: {hacks}")


class MissingAttrsError(InvalidAttrsError):
    def __init__(self, attrs, chip_id, filename):
        super().__init__(chip_id, filename, f"has missing attributes: {attrs}")


class ExcessAttrsError(InvalidAttrsError):
    def __init__(self, attrs, chip_id, filename):
        super().__init__(chip_id, filename, f"has excess attributes: {attrs}")
