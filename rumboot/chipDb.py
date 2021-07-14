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
                        if chip.chip_id in self.chips and \
                            self.chips[chip.chip_id].chip_rev == chip.chip_rev:
                            raise MultipleChipConfigError(chip.chip_id, yml)
                        else:
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

                            self.chips[chip.chip_id] = chip

    def __getitem__(self, key):
        try:
            key = int(key)
        except:
            pass
        if key in self.chips:
            return self.chips[key]
        for chip in self.chips.values():
            if chip.name == key:
                return chip
        return None


class Chip(yaml.YAMLObject):
    yaml_tag = '!Chip'
    yaml_loader = yaml.SafeLoader


class MultipleChipConfigError(Exception):
    def __init__(self, chip_id, filename):
        super().__init__(
            f"Found duplicate config [{filename}] for chip with ID [{chip_id}]"
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
