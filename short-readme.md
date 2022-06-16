# rr-ml-config

This package is a Config System which allows easy manipulation of config files for safe, clear and
repeatable experiments.

**DISCLAIMER: This repository is the public versio of a repository that is the property of [Reactive Reality](https://www.reactivereality.com/). This repository IS NOT OFFICIAL.**

[LINK TO DOCUMENTATION](https://gitlab.com/reactivereality/public/rr-ml-config-public/-/wikis/home)

## Installation

The package can be installed from our registry using pip: `pip install rr-ml-config`

## Getting started

This package is adapted to a *project* where you need to run a number of experiments. In this setup,
it can be useful to gather all the parameters in the project to a common location, some "config files",
so you can access and modify them easily. This package is based on YAML, therefore your config files
should be YAML files. One such YAML file could be :

```yaml
gpu: true
data_path: "./data"
learning_rate: 0.01
```

Those will be the default values for those three parameters, so we will keep them in the file
`my_project/configs/default.yaml`. Then, we just need to subclass the Configuration class in this package
so your project-specific subclass knows where to find the default values for your project. A minimalistic
project-specific subclass looks like:

```python
from rr.ml.config import Configuration

class ProjectSpecific(Configuration):
    @staticmethod
    def get_default_config_path():
        return "./configs/default.yaml"

    def parameters_pre_processing(self):
        return {}
```

That's all there is to it! Now if we use `config = ProjectSpecific.load_config()`, we can then call
`config.data_path` or `config.learning_rate` to get their values as defined in the default config. We
don't need to specify where to get the default config because a project should only ever have one default
config, which centralizes all the parameters in that project. Since the location of the default config is
a project constant, it is defined in your project-specific subclass and there is no need to clutter your
main code with it. Now, for example, your main.py could look like:

```python
from project_config import ProjectSpecific

if __name__ == "__main__":
    config = ProjectSpecific.load_config()
    print(config.details())
```

Then, calling `python main.py --learning_rate=0.001` would parse
the command line and find the pre-existing parameter learning_rate, then change its value to 0.001.

## Contribution

We welcome contributions to this repository via the [GitLab repository](https://gitlab.com/reactivereality/public/rr-ml-config-public).

## License

This repository is licensed under the [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl-3.0.en.html). It is free to use and distribute but modifications are not allowed.
