# rr-ml-config

---
This package is a Config System which allows easy manipulation of config files for safe, clear and
repeatable experiments. In a few words, it is:
- built for Machine Learning with its constraints in mind, but also usable out-of-the-box for other
kinds of projects;
- built with scalability in mind and can adapt just as easily to large projects investigating
hundreds of well-organized parameters across many experiments;
- designed to encourage good coding practices for research purposes, and if used rigorously will 
ensure a number of highly desirable properties such that **maintenance-less forward-compatibility**
of old configs, **easy reproducibility** of any experiment, and **extreme clarity** of former 
experiments for your future self or collaborators.

[LINK TO DOCUMENTATION](https://gitlab.com/reactivereality/public/rr-ml-config-public/-/wikis/home)

## Installation

The package can be installed from our registry using pip: `pip install --extra-index-url=https://gitlab.com/api/v4/projects/26449469/packages/pypi/simple rr-ml-config`

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
    config.merge_from_command_line()
    print(config.details())
```
Then, calling `python main.py --learning_rate=0.001`, the call to `merge_from_command_line` would parse
the command line and find the pre-existing parameter learning_rate, then change its value to 0.001.
Thus, the printed result would yield:
```
MAIN CONFIG :
Configuration hierarchy :
> ./configs/default.yaml

 - gpu : true
 - data_path : ./data
 - learning_rate : 0.001
```
The Configuration hierarchy tells you about the creation history of the config, in this case only the
default config was used. Then, all parameters are displayed. There are of course many other features
in this package which you can use to organize your parameters, hierarchise your experiments etc. The
idea being that once the bare minimum presented above is set up, scaling up is just as simple.

You can learn more about all these features in our [DOCUMENTATION](https://gitlab.com/reactivereality/public/rr-ml-config-public/-/wikis/home).

## config_history
The Config History is a side-feature of the main Config System. It can be configured for any project
which uses the Config System and provides a flexible framework to easily build graphs representing
past experiments. In these graphs, each node represents an experiment, and vertices are drawn between
your experiments to visualize easily which parameters changed from one node to another.

The graph can be coloured to show your most successful experiments, or grouped by parameters to see how
well they have been explored in your experiment history. This makes it very useful to review your past
work, share it with colleagues or make unexpected correlations appear.

Please refer to our [DOCUMENTATION](https://gitlab.com/reactivereality/public/rr-ml-config-public/-/wikis/home) to learn more about its setup and usage.

Requirements (**will not** be installed automatically by pip to keep this lightweight):
- `python>=3.7`
- `pygraphviz==1.7`
- `scipy`
- `numpy`
- `sudo apt install graphviz`
