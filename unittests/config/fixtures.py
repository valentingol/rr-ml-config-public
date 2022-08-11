"""
Reactive Reality Machine Learning Config System - unit tests
Copyright (C) 2022  Reactive Reality

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import pytest
import os
import sys

IS_REMOTE = "--junitxml" in sys.argv

if IS_REMOTE:
    from rr.ml.config.user_utils import get_template_class, make_config
else:
    import importlib
    make_config = importlib.import_module("rr-ml-config").user_utils.make_config
    get_template_class = importlib.import_module("rr-ml-config").user_utils.get_template_class


@pytest.fixture
def tmp_file_name(tmpdir):
    index = 1 + max([-1]+[int(i[3:-5]) for i in os.listdir(tmpdir) if i.startswith('tmp') and i.endswith('.yaml')])
    filename = tmpdir / f'tmp{index}.yaml'
    yield filename


@pytest.fixture
def yaml_default(tmpdir):
    index = len(os.listdir(tmpdir))
    content = f"param1: 0.1\n--- !subconfig1\nparam2: 3.0\n---\n" \
              f"def_second_path: '{tmpdir / f'default_second{index}.yaml'}'\nexp_second_path: null"
    with open(tmpdir / f'default{index}.yaml', "w") as s:
        s.write(content)
    content = f"--- !subconfig2\nparam3: 20.0\nsubconfig3: !subconfig3\n  param4: 'string'"
    with open(tmpdir / f'default_second{index}.yaml', "w") as s:
        s.write(content)
    yield str(tmpdir / f'default{index}.yaml')


def load_config(*configs, default_config=None, preprocessing=None, postprocessing=None):
    return make_config(default_config, *configs,
                       pre_processing_dict=preprocessing,
                       post_processing_dict=postprocessing,
                       additional_configs_suffix="_path",
                       variations_suffix="var*",
                       grids_suffix="grid",
                       do_not_merge_command_line=True)


def template(default_config=None):
    return get_template_class(default_config_path=default_config,
                              additional_configs_suffix="_path",
                              variations_suffix="var*",
                              grids_suffix="grid")


@pytest.fixture
def yaml_experiment(tmpdir):
    index = len(os.listdir(tmpdir))
    content = f"subconfig1.param2: 2.0\n\nexp_second_path: \"experiment_second{index}.yaml\""
    with open(tmpdir / f'experiment{index}.yaml', "w") as s:
        s.write(content)
    content = f"--- !subconfig2\nparam3: 30.0"
    with open(tmpdir / f'experiment_second{index}.yaml', "w") as s:
        s.write(content)
    yield str(tmpdir / f'experiment{index}.yaml')


@pytest.fixture
def yaml_default_unlinked(tmpdir):
    content = "param1:\n  param2: 1\n  param3: !param3\n    param4: 2"
    with open(tmpdir / f'tmp{len(os.listdir(tmpdir))}.yaml', "w") as s:
        s.write(content)
    yield str(tmpdir / f'tmp{len(os.listdir(tmpdir))-1}.yaml')


@pytest.fixture
def yaml_default_preproc_default_dot_param(tmpdir):
    content = "param1.param2: 2"
    with open(tmpdir / f'tmp{len(os.listdir(tmpdir))}.yaml', "w") as s:
        s.write(content)
    yield str(tmpdir / f'tmp{len(os.listdir(tmpdir))-1}.yaml')


@pytest.fixture
def yaml_default_sub_variations(tmpdir):
    content = "param1: !param1\n  var: []"
    with open(tmpdir / f'tmp{len(os.listdir(tmpdir))}.yaml', "w") as s:
        s.write(content)
    yield str(tmpdir / f'tmp{len(os.listdir(tmpdir))-1}.yaml')


@pytest.fixture
def yaml_default_set_twice(tmpdir):
    content = "param: 2"
    with open(tmpdir / f'tmp{len(os.listdir(tmpdir))}.yaml', "w") as s:
        s.write(content)
    yield str(tmpdir / f'tmp{len(os.listdir(tmpdir))-1}.yaml')


@pytest.fixture
def yaml_experiment_sub_star(tmpdir):
    content = "subconfig2: !subconfig2\n  '*param*': 1.0"
    with open(tmpdir / f'tmp{len(os.listdir(tmpdir))}.yaml', "w") as s:
        s.write(content)
    yield str(tmpdir / f'tmp{len(os.listdir(tmpdir))-1}.yaml')


@pytest.fixture
def yaml_experiment_sub_dot(tmpdir):
    content = "subconfig2: !subconfig2\n  subconfig3.param4: 1.0"
    with open(tmpdir / f'tmp{len(os.listdir(tmpdir))}.yaml', "w") as s:
        s.write(content)
    yield str(tmpdir / f'tmp{len(os.listdir(tmpdir))-1}.yaml')


@pytest.fixture
def yaml_craziest_config(tmpdir):
    with open(tmpdir / 'd_first.yaml', "w") as s:
        s.write(f"p1: 1\n"
                f"--- !c1\n"
                f"c2: !c2\n"
                f"  f_path: {'d_second.yaml'}\n"
                f"---\n"
                f"c4.p3: 3\n"
                f"c4.p7: 7\n"
                f"f_path: {tmpdir / 'd_second.yaml'}")
    with open(tmpdir / 'd_second.yaml', "w") as s:
        s.write(f"--- !c3\n"
                f"p2: 2\n"
                f"c5.s_path: {tmpdir / 'd_third.yaml'}\n"
                f"---\n"
                f"p6: 6")
    with open(tmpdir / 'd_third.yaml', "w") as s:
        s.write("--- !c6\n"
                "p4: {a: 4}\n"
                "---\n"
                "p5: 5")

    with open(tmpdir / 'e_first.yaml', "w") as s:
        s.write(f"'*p6': 7\n"
                f"--- !c1\n"
                f"c2.f_path: {tmpdir / 'e_second.yaml'}\n"
                f"---\n"
                f"c4: !c4\n"
                f"  p3: 'test'\n"
                f"c4.p7: 'test2'")
    with open(tmpdir / 'e_second.yaml', "w") as s:
        s.write("--- !c3\n"
                "'*.p*': 8\n"
                "'*p4': {b: 5}")
    yield str(tmpdir / 'd_first.yaml'), str(tmpdir / 'e_first.yaml')


@pytest.fixture
def yaml_no_file_call_processing_while_loading(tmpdir):
    with open(tmpdir / 'd_first.yaml', "w") as s:
        s.write(f"test_path: {tmpdir / 'd_second.yaml'}\nexp_path: null")
    with open(tmpdir / 'd_second.yaml', "w") as s:
        s.write("param: 0.1")
    with open(tmpdir / 'e_first.yaml', "w") as s:
        s.write(f"exp_path: {tmpdir / 'e_second.yaml'}")
    with open(tmpdir / 'e_second.yaml', "w") as s:
        s.write("param: 0.2")
    config = make_config(str(tmpdir / 'd_first.yaml'), str(tmpdir / 'e_first.yaml'),
                         additional_configs_suffix="_path",
                         variations_suffix="var*",
                         grids_suffix="grid",
                         do_not_merge_command_line=True)
    config.save(str(tmpdir / 'save.yaml'))
    with open(tmpdir / 'd_second.yaml', "w") as s:
        s.write("param: 0.3")
    with open(tmpdir / 'e_second.yaml', "w") as s:
        s.write("param: 0.4")
    config2 = make_config(str(tmpdir / 'd_first.yaml'), str(tmpdir / 'save.yaml'),
                          additional_configs_suffix="_path",
                          variations_suffix="var*",
                          grids_suffix="grid",
                          do_not_merge_command_line=True)
    yield config, config2


@pytest.fixture
def yaml_no_file_call_processing_while_loading_nested(tmpdir):
    with open(tmpdir / 'nd_first.yaml', "w") as s:
        s.write(f"c: !c\n  test_path: {tmpdir / 'nd_second.yaml'}\n  exp_path: null")
    with open(tmpdir / 'nd_second.yaml', "w") as s:
        s.write("param: 0.1")
    with open(tmpdir / 'ne_first.yaml', "w") as s:
        s.write(f"c: !c\n  exp_path: {tmpdir / 'ne_second.yaml'}")
    with open(tmpdir / 'ne_second.yaml', "w") as s:
        s.write("param: 0.2")
    config = make_config(str(tmpdir / 'nd_first.yaml'), str(tmpdir / 'ne_first.yaml'),
                         additional_configs_suffix="_path",
                         variations_suffix="var*",
                         grids_suffix="grid",
                         do_not_merge_command_line=True)
    config.save(str(tmpdir / 'nsave.yaml'))
    with open(tmpdir / 'nd_second.yaml', "w") as s:
        s.write("param: 0.3")
    with open(tmpdir / 'ne_second.yaml', "w") as s:
        s.write("param: 0.4")
    config2 = make_config(str(tmpdir / 'nd_first.yaml'), str(tmpdir / 'nsave.yaml'),
                          additional_configs_suffix="_path",
                          variations_suffix="var*",
                          grids_suffix="grid",
                          do_not_merge_command_line=True)
    yield config, config2
