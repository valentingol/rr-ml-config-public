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
    # within pypi deployment docker container
    import deploytools
    version = deploytools.get_version()
except ModuleNotFoundError:
    # fallback for local testing
    with open('../.rrci/version.yml', 'r') as f:
        version = f.read().split('version: ')[1].strip()

setup(
    name='rr-ml-config',
    version='1.3.0',
    description='Reactive Reality Machine Learning Config System',
    url='https://gitlab.com/reactivereality/public/rr-ml-config-public',
    author='Reactive Reality AG',
    packages=['rr.ml.config'],
    package_dir={'rr.ml.config': 'rr-ml-config'},
    install_requires=["pyyaml"]
)
