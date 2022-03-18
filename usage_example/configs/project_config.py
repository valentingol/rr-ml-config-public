import random
from rr.ml.config import Configuration


def check_model_type(model_type):
    assert model_type in ["linear", "polynomial"]
    return model_type


def check_params(param):
    if param is None:
        return None
    if param == "random":
        return random.random()
    assert isinstance(param, float) or isinstance(param, int)
    return param


# This is literally the copy/pasted template given in framework/config/default_config_template
# There is however a few pre-processing functions added to provide with further guidance as to how to modify this class
class ProjectSpecificConfiguration(Configuration):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def get_default_config_path():
        return "./configs/default/main_config.yaml"

    def parameters_pre_processing(self):
        return {
            "model.type": check_model_type,
            "model.param*": check_params,
            "*_variation": self.register_as_config_variations,
            "grid": self.register_as_grid,
            "*path_to_config": self.register_as_additional_config_file,
            "*paths_to_configs": lambda x: [self.register_as_additional_config_file(path) for path in x]
        }
