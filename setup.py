"""
Reactive Reality Machine Learning Config System - setup file
Copyright (C) 2022  Reactive Reality

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from setuptools import setup

try:
    # used for automatic deployment pipeline
    import deploytools
    version = deploytools.get_version()
except ModuleNotFoundError:
    # used otherwise
    import requests
    from packaging import version
    print("WARNING : the version which will be displayed for this package will be the latest deployed version. "
          "This is irrespective of which commit was used to build the library from.")
    version = str(max([version.parse(i["version"])
                       for i in requests.get("https://gitlab.com/api/v4/projects/26449469/packages/").json()
                       if i["name"] == "rr-ml-config"]))

setup(
    name='rr-ml-config',
    version=version,
    description='Reactive Reality Machine Learning Config System',
    url='https://gitlab.com/reactivereality/public/rr-ml-config-public',
    author='Reactive Reality AG',
    packages=['rr.ml.config'],
    package_dir={'rr.ml.config': 'rr-ml-config'},
    install_requires=["pyyaml"]
)
