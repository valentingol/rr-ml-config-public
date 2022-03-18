# rr-ml-config

ML-team generic project and experiment config system

### Installation

Install as per the [instructions for rr pip packages](https://reactivereality.atlassian.net/wiki/spaces/DOC/pages/742883338/Installing+RR+python+packages). The `<packagename>` is `rr-ml-config`. It is installed under `rr.ml`, so an example import would be `from rr.ml.config import Configuration`.

To install the package from the repository run `pip install .` in the project root.

#### Removing the package

Simply run `pip uninstall rr-ml-config`.

### config_history
Requirements (**will not** be installed automatically by pip to keep this lightweight):
- `python>=3.7`
- `pygraphviz==1.7`
- `scipy`
- `numpy`
- `sudo apt install graphviz`
