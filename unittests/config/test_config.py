"""
Reactive Reality Machine Learning Config System - unit tests
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

from rr.ml.config import Configuration
# from config import Configuration
import os
import pytest
from pathlib import Path


@pytest.fixture
def tmp_file_name(tmpdir):
    filename = tmpdir / 'tmp.yaml'
    yield filename


# @pytest.fixture
# def yaml_default(tmpdir):
#     index = len(os.listdir(tmpdir))
#     content = f"param1: 0.1\n--- !subconfig1\nparam2: 3.0\n---\n" \
#               f"def_second_path: '{tmpdir / f'default_second{index}.yaml'}'\nexp_second_path: null"
#     with open(tmpdir / f'default{index}.yaml', "w") as s:
#         s.write(content)
#     content = f"--- !subconfig2\nparam3: 20.0\nsubconfig3: !subconfig3\n  param4: 'string'"
#     with open(tmpdir / f'default_second{index}.yaml', "w") as s:
#         s.write(content)
#     yield str(tmpdir / f'default{index}.yaml'), str(tmpdir / f'default_second{index}.yaml')


@pytest.fixture
def yaml_default_unlinked(tmpdir):
    content = "param1:\n  param2: 1\n  param3: !param3\n    param4: 2"
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
                "p4: 4\n"
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
        s.write(f"--- !c3\n"
                f"'*.p*': 8")
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
    config = ConfigForTests.build_from_configs(str(tmpdir / 'd_first.yaml'), str(tmpdir / 'e_first.yaml'))
    config.save(str(tmpdir / 'save.yaml'))
    with open(tmpdir / 'd_second.yaml', "w") as s:
        s.write("param: 0.3")
    with open(tmpdir / 'e_second.yaml', "w") as s:
        s.write("param: 0.4")
    config2 = ConfigForTests.build_from_configs(str(tmpdir / 'd_first.yaml'), str(tmpdir / 'save.yaml'))
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
    config = ConfigForTests.build_from_configs(str(tmpdir / 'nd_first.yaml'), str(tmpdir / 'ne_first.yaml'))
    config.save(str(tmpdir / 'nsave.yaml'))
    with open(tmpdir / 'nd_second.yaml', "w") as s:
        s.write("param: 0.3")
    with open(tmpdir / 'ne_second.yaml', "w") as s:
        s.write("param: 0.4")
    config2 = ConfigForTests.build_from_configs(str(tmpdir / 'nd_first.yaml'), str(tmpdir / 'nsave.yaml'))
    yield config, config2


class ConfigForTests(Configuration):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def get_default_config_path():
        return "unittests/config/config_files/default/default.yaml"

    def parameters_pre_processing(self):
        return {"*_path": self.register_as_additional_config_file,
                "*var*": self.register_as_config_variations,
                "grid": self.register_as_grid}


def check_integrity(config, p1=0.1, p2=2.0, p3=30.0, p4="string"):
    assert config["param1"] == p1
    assert config["subconfig1.param2"] == p2
    assert config["subconfig2.param3"] == p3
    assert config["subconfig2.subconfig3.param4"] == p4


def test_load_default(capsys):
    config = ConfigForTests.load_config([])
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    assert 1 != config
    assert config != 1
    check_integrity(config, p2=3.0, p3=20.0)
    config2 = config.copy()
    config2.merge({"subconfig2.subconfig3.param4": "new_string"})
    assert config != config2
    assert config2 != config
    config2 = config.copy()
    object.__setattr__(config2.subconfig2, "subconfig3", 1)
    assert config != config2
    assert config2 != config
    config2 = config.copy()
    object.__delattr__(config2.subconfig2, "subconfig3")
    assert config != config2
    assert config2 != config
    assert config == ConfigForTests.build_from_configs(ConfigForTests.get_default_config_path())


def test_load_experiment(capsys, yaml_experiment_sub_dot, yaml_experiment_sub_star):
    config = ConfigForTests.load_config("unittests/config/config_files/experiment/experiment.yaml")
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    check_integrity(config)
    assert config == ConfigForTests.build_from_configs([ConfigForTests.get_default_config_path(),
                                                        "unittests/config/config_files/experiment/experiment.yaml"])
    config = ConfigForTests.load_config(yaml_experiment_sub_dot)
    check_integrity(config, p2=3.0, p3=20.0, p4=1.0)
    config = ConfigForTests.load_config(yaml_experiment_sub_star)
    check_integrity(config, p2=3.0, p3=1.0, p4=1.0)


def test_get(capsys):
    config = ConfigForTests.build_from_configs({"save": "test", "param": 1})
    captured = capsys.readouterr()
    assert captured.out.count("WARNING") == 1
    assert config["param"] == 1
    assert config["save"] == "test"
    assert config["___save"] == "test"
    assert config.param == 1
    assert config.___save == "test"
    assert callable(config.save)
    assert config.get("param", None) == 1
    assert config.get("save", None) == "test"
    assert config.get("___save", None) == "test"
    assert config.get("not_a_param", None) is None
    assert config.get("param.param", None) is None


def test_get_dict(capsys):
    config = ConfigForTests.load_config([])
    object.__setattr__(config, "___save", "test")
    def_second = os.path.abspath("unittests/config/config_files/default/default_second.yaml")
    assert config.get_dict() == {'param1': 0.1,
                                 'subconfig1': {'param2': 3.0},
                                 'subconfig2': {'param3': 20.0, 'subconfig3': {'param4': 'string'}},
                                 'def_second_path': def_second,
                                 'exp_second_path': None,
                                 'save': 'test'}
    assert config['param1'] == 0.1
    assert config['def_second_path'] == def_second
    assert config['exp_second_path'] is None
    assert config['save'] == 'test'
    assert isinstance(config['subconfig1'], ConfigForTests)
    assert isinstance(config['subconfig2'], ConfigForTests)


def test_merge_pattern(capsys):
    config = ConfigForTests.load_config("unittests/config/config_files/experiment/experiment.yaml")
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    config.merge({"param*": 0.2})
    check_integrity(config, 0.2)
    config.merge({"*param*": 0.2})
    check_integrity(config, 0.2, 0.2, 0.2, 0.2)
    config.subconfig2.merge({"*param*": 0.4})
    check_integrity(config, 0.2, 0.2, 0.4, 0.4)
    assert config.config_metadata["config_hierarchy"] == ['unittests/config/config_files/default/default.yaml',
                                                          'unittests/config/config_files/experiment/experiment.yaml',
                                                          {'param*': 0.2}, {'*param*': 0.2},
                                                          {'subconfig2.*param*': 0.4}]
    config.subconfig2.subconfig3.merge({"*param*": "0.5"})
    check_integrity(config, 0.2, 0.2, 0.4, "0.5")
    assert config.config_metadata["config_hierarchy"] == ['unittests/config/config_files/default/default.yaml',
                                                          'unittests/config/config_files/experiment/experiment.yaml',
                                                          {'param*': 0.2}, {'*param*': 0.2},
                                                          {'subconfig2.*param*': 0.4},
                                                          {'subconfig2.subconfig3.*param*': "0.5"}]


def test_merge_from_command_line(capsys):
    config = ConfigForTests.load_config("unittests/config/config_files/experiment/experiment.yaml")
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    config.merge_from_command_line("--lr=0.5 --param1=1 --subconfig1.param2=0.6")
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    check_integrity(config, 1, 0.6)
    config.merge_from_command_line("--subconfig2.subconfig3.param4='test test'")
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    check_integrity(config, 1, 0.6, p4="test test")
    config_2 = ConfigForTests.load_config("unittests/config/config_files/experiment/experiment.yaml")
    config_2.merge_from_command_line(config.get_command_line_argument(do_return_string=True))
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    check_integrity(config_2, 1, 0.6, p4="test test")


def test_method_name(capsys):
    config = ConfigForTests.build_from_configs({"save": "test"})
    captured = capsys.readouterr()
    assert captured.out.count("WARNING") == 1
    assert config.details() == "\nMAIN CONFIG :\nConfiguration hierarchy :\n> {'save': 'test'}\n\n - save : test\n"
    config.merge({"save": 0.1})
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    assert config.details() == "\nMAIN CONFIG :\nConfiguration hierarchy :\n> {'save': 'test'}\n> {'save': 0.1}\n\n" \
                               " - save : 0.1\n"


def test_details(capsys):
    config = ConfigForTests.load_config("unittests/config/config_files/experiment/experiment.yaml")
    s = "\nMAIN CONFIG :\nConfiguration hierarchy :\n> unittests/config/config_files/default/default.yaml\n" \
        "> unittests/config/config_files/experiment/experiment.yaml\n\n - param1 : 0.1\n - subconfig1 : \n	" \
        "SUBCONFIG1 CONFIG :\n	 - param2 : 2.0\n\n - subconfig2 : \n	SUBCONFIG2 CONFIG :\n	 - param3 : 30.0\n" \
        "	 - subconfig3 : \n		SUBCONFIG3 CONFIG :\n		 - param4 : string\n\n\n"
    assert s == config.details(no_show="*_path")
    s = "\nMAIN CONFIG :\nConfiguration hierarchy :\n> unittests/config/config_files/default/default.yaml\n" \
        "> unittests/config/config_files/experiment/experiment.yaml\n\n - param1 : 0.1\n - subconfig1 : SUBCONFIG1\n" \
        " - subconfig2 : \n	SUBCONFIG2 CONFIG :\n	 - param3 : 30.0\n	 - subconfig3 : \n		SUBCONFIG3 CONFIG :\n" \
        "		 - param4 : string\n\n\n"
    assert s == config.details(expand_only=["subconfig2"], no_show="*_path")
    s = "\nMAIN CONFIG :\nConfiguration hierarchy :\n> unittests/config/config_files/default/default.yaml\n" \
        "> unittests/config/config_files/experiment/experiment.yaml\n\n - param1 : 0.1\n - subconfig1 : \n" \
        "	SUBCONFIG1 CONFIG :\n	 - param2 : 2.0\n\n - subconfig2 : SUBCONFIG2\n"
    assert s == config.details(no_expand=["subconfig2"], no_show="*_path")


def test_variations(capsys):
    config = ConfigForTests.build_from_configs({"p1": 0.1, "p2": 1.0,
                                                "var1": [{"p1": 0.1}, {"p1": 0.2}],
                                                "var2": [{"p2": 1.0}, {"p2": 2.0}, {"p2": 3.0}],
                                                "grid": None})
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    assert config.p1 == 0.1 and config.p2 == 1.0
    variations = config.create_variations()
    assert len(variations) == 5
    assert variations[0] == variations[2] == config
    assert variations[1].p1 == 0.2 and variations[1].p2 == 1.0
    assert variations[3].p1 == variations[4].p1 == 0.1
    assert variations[3].p2 == 2.0 and variations[4].p2 == 3.0
    config.merge({"grid": ["var1", "var2"]})
    variations = config.create_variations()
    assert len(variations) == 6
    assert variations[0] == config and variations[1].p1 == variations[2].p1 == 0.1 and variations[3].p2 == 1.0
    assert variations[3].p1 == variations[4].p1 == variations[5].p1 == 0.2
    assert variations[1].p2 == variations[4].p2 == 2.0 and variations[2].p2 == variations[5].p2 == 3.0


def test_pre_processing(capsys, tmp_file_name, yaml_no_file_call_processing_while_loading,
                        yaml_no_file_call_processing_while_loading_nested):
    ConfigForTests.parameters_pre_processing = lambda self: {"*_path": self.register_as_additional_config_file,
                                                             "*param*": lambda x: x+1 if not isinstance(x, str) else x}
    config = ConfigForTests.load_config("unittests/config/config_files/experiment/experiment.yaml")
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    check_integrity(config, 1.1, 3.0, 31.0)
    config.save(str(tmp_file_name))
    config2 = ConfigForTests.load_config(str(tmp_file_name))
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    assert config == config2
    config2.merge({"param1": 0.2})
    assert config2.param1 == 1.2
    ConfigForTests.parameters_pre_processing = lambda self: {"*_path": self.register_as_additional_config_file,
                                                             "*var*": self.register_as_config_variations,
                                                             "grid": self.register_as_grid}
    assert yaml_no_file_call_processing_while_loading[0] == yaml_no_file_call_processing_while_loading[1]
    assert yaml_no_file_call_processing_while_loading_nested[0] == yaml_no_file_call_processing_while_loading_nested[1]


def test_save_reload(capsys, tmp_file_name):
    config = ConfigForTests.load_config("unittests/config/config_files/experiment/experiment.yaml")
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    config.save(str(tmp_file_name))
    config2 = ConfigForTests.load_config(str(tmp_file_name))
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    config2.save(str(tmp_file_name))
    config3 = ConfigForTests.load_config(str(tmp_file_name))
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    assert config == config2 == config3


def test_save_reload_method_param(capsys, tmp_file_name):
    config = ConfigForTests(config_path_or_dictionary={"save": 1})
    captured = capsys.readouterr()
    assert captured.out.count("WARNING") == 1
    config.save(str(tmp_file_name))
    config2 = ConfigForTests(config_path_or_dictionary={"save": 1})
    config2.merge(str(tmp_file_name))
    captured = capsys.readouterr()
    assert captured.out.count("WARNING") == 1
    config2.save(str(tmp_file_name))
    config3 = ConfigForTests(config_path_or_dictionary={"save": 1})
    config3.merge(str(tmp_file_name))
    captured = capsys.readouterr()
    assert captured.out.count("WARNING") == 1
    config3.save(str(tmp_file_name))
    assert config == config2 == config3


def test_craziest_config(capsys, yaml_craziest_config):
    config = ConfigForTests.build_from_configs(yaml_craziest_config[0])
    second = os.path.join(Path(yaml_craziest_config[0]).parents[0], "d_second.yaml")
    third = os.path.join(Path(yaml_craziest_config[0]).parents[0], "d_third.yaml")
    s = f"\nMAIN CONFIG :\n" \
        f"Configuration hierarchy :\n" \
        f"> {yaml_craziest_config[0]}\n\n" \
        f" - p1 : 1\n - c1 : \n	C1 CONFIG :\n	 - c2 : \n		C2 CONFIG :\n		 - c3 : \n" \
        f"			C3 CONFIG :\n			 - p2 : 2\n			 - c5 : \n				C5 CONFIG :\n" \
        f"				 - c6 : \n					C6 CONFIG :\n					 - p4 : 4\n\n" \
        f"				 - p5 : 5\n" \
        f"				 - s_path : {third}\n\n\n		 - p6 : 6\n		 - f_path : {second}\n\n\n" \
        f" - c4 : \n	C4 CONFIG :\n	 - p3 : 3\n	 - p7 : 7\n\n - c3 : \n	C3 CONFIG :\n	 - p2 : 2\n	 - c5 : \n" \
        f"		C5 CONFIG :\n		 - c6 : \n			C6 CONFIG :\n			 - p4 : 4\n\n		 - p5 : 5\n" \
        f"		 - s_path : {third}\n\n\n - p6 : 6\n - f_path : {second}\n"
    assert config.details() == s
    config = ConfigForTests.build_from_configs(yaml_craziest_config[0], yaml_craziest_config[1])
    second_e = os.path.join(Path(yaml_craziest_config[0]).parents[0], "e_second.yaml")
    s = f"\nMAIN CONFIG :\n" \
        f"Configuration hierarchy :\n" \
        f"> {yaml_craziest_config[0]}\n" \
        f"> {yaml_craziest_config[1]}\n\n" \
        f" - p1 : 1\n - c1 : \n	C1 CONFIG :\n	 - c2 : \n		C2 CONFIG :\n		 - c3 : \n" \
        f"			C3 CONFIG :\n			 - p2 : 2\n			 - c5 : \n				C5 CONFIG :\n" \
        f"				 - c6 : \n					C6 CONFIG :\n					 - p4 : 8\n\n" \
        f"				 - p5 : 8\n" \
        f"				 - s_path : {third}\n\n\n		 - p6 : 7\n		 - f_path : {second_e}\n\n\n" \
        f" - c4 : \n	C4 CONFIG :\n	 - p3 : test\n	 - p7 : test2\n\n - c3 : \n	C3 CONFIG :\n	 - p2 : 2\n	 - c5" \
        f" : \n		C5 CONFIG :\n		 - c6 : \n			C6 CONFIG :\n			 - p4 : 4\n\n		 - p5 : 5\n" \
        f"		 - s_path : {third}\n\n\n - p6 : 7\n - f_path : {second}\n"
    assert config.details() == s


def test_pattern_matching():
    assert ConfigForTests._compare_string_pattern("", "*")
    assert ConfigForTests._compare_string_pattern("abcdefgh0123,:", "*")
    assert ConfigForTests._compare_string_pattern("abcdefgh0123", "abcdefgh0123")
    assert ConfigForTests._compare_string_pattern("abcdefgh0123", "abcde*gh0123")
    assert ConfigForTests._compare_string_pattern("abcdeffffgh0123", "abcde*gh0123")
    assert ConfigForTests._compare_string_pattern("abcdefgh0123", "*a*b*c*d*e*f*g*h*0*1*2*3*")
    assert ConfigForTests._compare_string_pattern("abcdefgh0123", "*0123")
    assert ConfigForTests._compare_string_pattern("abcdefgh0123", "abcd*")
    assert ConfigForTests._compare_string_pattern("abcdefgh0123", "a**3")

    assert not ConfigForTests._compare_string_pattern("abcdefgh0123", "abcdefgh012")
    assert not ConfigForTests._compare_string_pattern("abcdefgh0123", "abcde*g0123")
    assert not ConfigForTests._compare_string_pattern("abcdefgh0123ffffh0123", "abcde*gh0123")
    assert not ConfigForTests._compare_string_pattern("abcdefgh0123", "*3*3*3")


def test_warnings(capsys, tmp_file_name):
    config = ConfigForTests(config_path_or_dictionary={"param": None, "lparam": [], "dparam": {"param2": 1}})
    config.merge_from_command_line("--param=1 --lparam=[1] --dparam={param2:2,param3:3}")
    captured = capsys.readouterr()
    assert captured.out.count("is None. It cannot be replaced from the") == 1
    assert captured.out.count("is an empty list. It cannot be replaced from the") == 1
    assert captured.out.count("key. This key cannot be") == 1
    assert config.dparam == {"param2": 1}
    config = ConfigForTests(config_path_or_dictionary={"param": 1}, overwriting_regime="unsafe")
    config.save(str(tmp_file_name))
    config.merge(str(tmp_file_name))
    captured = capsys.readouterr()
    assert captured.out.count("YOU ARE LOADING AN UNSAFE CONFIG") == 1
    config = ConfigForTests(config_path_or_dictionary={"param": 1})
    config.merge({"*d": 1})
    captured = capsys.readouterr()
    assert captured.out.count("will be ignored : it does not match any") == 1


def test_errors(capsys, yaml_default_unlinked, yaml_default_sub_variations, yaml_default_set_twice):
    with pytest.raises(Exception, match="'overwriting_regime' needs to be either 'auto-save', 'locked' or 'unsafe'."):
        _ = ConfigForTests(config_path_or_dictionary={"param": 1}, overwriting_regime="a")
    with pytest.raises(Exception, match=".*is not a sub-config, it cannot be accessed.*"):
        _ = ConfigForTests(config_path_or_dictionary={"param": 1})["param.param"]
    with pytest.raises(Exception, match="Overwriting params in locked configs is not allowed."):
        config = ConfigForTests(config_path_or_dictionary={"param": 1}, overwriting_regime="locked")
        config.param = 2
    with pytest.raises(Exception, match="build_from_configs needs to be called with at least one config."):
        _ = ConfigForTests.build_from_configs()
    with pytest.raises(Exception, match="build_from_configs needs to be called with at least one config."):
        _ = ConfigForTests.build_from_configs([])
    with pytest.raises(Exception, match=".*\nplease use build_from_configs.*"):
        _ = ConfigForTests.build_from_configs([ConfigForTests.get_default_config_path()], [{"param1": 1}])
    with pytest.raises(Exception, match="No filename was provided.*"):
        ConfigForTests(config_path_or_dictionary={"param": 1}).save()
    with pytest.raises(Exception, match="Grid element.*"):
        _ = ConfigForTests(config_path_or_dictionary={"param": 1, "var": [], "grid": ["var"]}).create_variations()
    with pytest.raises(Exception, match="Grid element.*"):
        _ = ConfigForTests(config_path_or_dictionary={"param": 1, "grid": ["var"]}).create_variations()
    with pytest.raises(Exception, match="Variations parsing failed.*"):
        ConfigForTests(config_path_or_dictionary={"param": 1, "var": 1})
    with pytest.raises(Exception, match="Variations parsing failed.*"):
        ConfigForTests(config_path_or_dictionary={"param": 1, "var": [1]})
    with pytest.raises(Exception, match="Variations parsing failed.*"):
        ConfigForTests(config_path_or_dictionary={"param": 1, "var": {"a": 1}})
    with pytest.raises(Exception, match="Grid parsing failed.*"):
        ConfigForTests(config_path_or_dictionary={"param": 1, "grid": {}})
    with pytest.raises(Exception, match="ERROR : path not found .*"):
        ConfigForTests(config_path_or_dictionary="not_found")
    with pytest.raises(Exception, match="'config_metadata' is a special parameter.*"):
        ConfigForTests(config_path_or_dictionary={"config_metadata": 1})
    with pytest.raises(Exception, match="'overwriting_regime' is a special parameter.*"):
        metadata = 'Saving time : <date> (<in_seconds>) ; Regime : something_incorrect'
        ConfigForTests(config_path_or_dictionary={"config_metadata": metadata})
    with pytest.raises(Exception, match="Failed to set parameter.*"):
        config = ConfigForTests(config_path_or_dictionary={"param": 1})
        config.merge({"param.param": 1})
    with pytest.raises(Exception, match="Failed to set parameter.*"):
        _ = ConfigForTests(config_path_or_dictionary={"param": 1, "param.param": 1})
    with pytest.raises(Exception, match=".*character is not authorized in the default config.*"):
        _ = ConfigForTests(config_path_or_dictionary={"param*": 1})
    with pytest.raises(Exception, match=".*Unlinked sub-configs are not allowed.*"):
        _ = ConfigForTests(config_path_or_dictionary=yaml_default_unlinked)
    captured = capsys.readouterr()
    assert captured.out.count("ERROR while pre-processing param") == 4
    with pytest.raises(Exception, match=".*Please declare all your variations in the main config.*"):
        _ = ConfigForTests(config_path_or_dictionary=yaml_default_sub_variations)
    with pytest.raises(Exception, match=".*is a protected name and cannot be used as a parameter.*"):
        _ = ConfigForTests(config_path_or_dictionary={"_nesting_hierarchy": 1})
    with pytest.raises(Exception, match=".*cannot be merged : it is not in the default.*"):
        config = ConfigForTests(config_path_or_dictionary={"param": 1})
        config.merge({"subconfig.param": 1})
    with pytest.raises(Exception, match=".*cannot be merged : it is not in the default.*"):
        config = ConfigForTests(config_path_or_dictionary={"param": 1})
        config.merge({"param2": 1})
    with pytest.raises(Exception, match=".*This replacement cannot be performed.*"):
        subconfig = ConfigForTests(config_path_or_dictionary={"param": 1})
        config = ConfigForTests(config_path_or_dictionary={"subconfig": subconfig})  # don't do this at home
        config.merge({"subconfig": 1})
    with pytest.raises(Exception, match=".* was set twice.*"):
        _ = ConfigForTests(config_path_or_dictionary={"param": 1, "set_twice_path": yaml_default_set_twice})


if __name__ == '__main__':
    ConfigForTests(config_path_or_dictionary={"param": 1})["param.param"]