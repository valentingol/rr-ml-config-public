from rr.ml.config import Configuration


class ProjectSpecificConfiguration(Configuration):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def get_default_config_path():
        return "./configs/default/main_config.yaml"

    def parameters_pre_processing(self):
        return {
            "*path_to_config": self.register_as_additional_config_file,
            "*paths_to_configs": lambda x: [self.register_as_additional_config_file(path) for path in x]
        }
