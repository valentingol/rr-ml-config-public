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
import sys
import os
import pytest
from typing import Any

from pathlib import Path
from fixtures import tmp_file_name, yaml_default, yaml_experiment, yaml_default_unlinked, load_config, \
    yaml_default_preproc_default_dot_param, yaml_default_sub_variations, yaml_default_set_twice, \
    yaml_experiment_sub_star, yaml_experiment_sub_dot, yaml_craziest_config, template, \
    yaml_no_file_call_processing_while_loading, yaml_no_file_call_processing_while_loading_nested

IS_REMOTE = "--junitxml" in sys.argv

if IS_REMOTE:
    from rr.ml.config import Configuration
    from rr.ml.config.user_utils import make_config
    from rr.ml.config.config_utils import compare_string_pattern
else:
    import importlib
    config_module = importlib.import_module("rr-ml-config")
    Configuration = config_module.config.Configuration
    make_config = config_module.user_utils.make_config
    compare_string_pattern = config_module.config_utils.compare_string_pattern


def check_integrity(config, p1: Any = 0.1, p2: Any = 2.0, p3: Any = 30.0, p4: Any = "string"):
    assert config["param1"] == p1
    assert config["subconfig1.param2"] == p2
    assert config["subconfig2.param3"] == p3
    assert config["subconfig2.subconfig3.param4"] == p4


def test_load_default(capsys, yaml_default):
    config = load_config(default_config=yaml_default)
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    assert 1 != config
    assert config != 1
    check_integrity(config, p2=3.0, p3=20.0)
    config = template(default_config=yaml_default).load_config([], do_not_merge_command_line=True)
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
    assert config == template(default_config=yaml_default).build_from_configs(
        template(default_config=yaml_default).get_default_config_path(), do_not_merge_command_line=True)


def test_load_experiment(capsys, yaml_default, yaml_experiment, yaml_experiment_sub_dot, yaml_experiment_sub_star):
    config = load_config(yaml_experiment, default_config=yaml_default)
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    check_integrity(config)
    assert config == template(default_config=yaml_default).build_from_configs(
        [template(default_config=yaml_default).get_default_config_path(),
         yaml_experiment],
        do_not_merge_command_line=True)
    config = load_config(yaml_experiment_sub_dot, default_config=yaml_default)
    check_integrity(config, p2=3.0, p3=20.0, p4=1.0)
    config = load_config(yaml_experiment_sub_star, default_config=yaml_default)
    check_integrity(config, p2=3.0, p3=1.0, p4=1.0)


def test_get(capsys):
    config = make_config({"save": "test", "param": 1}, do_not_merge_command_line=True)
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


def test_get_dict(capsys, yaml_default):
    config = load_config(default_config=yaml_default)
    object.__setattr__(config, "___save", "test")
    def_second = os.path.join( os.path.sep.join(yaml_default.split(os.path.sep)[:-1]),
                              f'default_second{yaml_default.split(os.path.sep)[-1][len("default"):-len(".yaml")]}.yaml')
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
    assert isinstance(config['subconfig1'], Configuration)
    assert isinstance(config['subconfig2'], Configuration)


def test_iter(capsys, yaml_default):
    config = load_config(default_config=yaml_default)
    object.__setattr__(config, "___save", "test")
    dict_for_test = {'param1': 0, 'subconfig1': 0, 'subconfig2': 0,
                     'def_second_path': 0, 'exp_second_path': 0, 'save': 0}
    for k in config:
        dict_for_test[k] += 1
        assert dict_for_test[k] == 1
    assert len(dict_for_test) == 6


def test_keys_values_items(capsys, yaml_default):
    config = load_config(default_config=yaml_default)
    object.__setattr__(config, "___save", "test")
    def_second = os.path.join(os.path.sep.join(yaml_default.split(os.path.sep)[:-1]),
                              f'default_second{yaml_default.split(os.path.sep)[-1][len("default"):-len(".yaml")]}.yaml')
    # deep = False (default)
    expected_dict = {'param1': 0.1,
                     'subconfig1': config.subconfig1,
                     'subconfig2': config.subconfig2,
                     'def_second_path': def_second,
                     'exp_second_path': None,
                     'save': 'test'}
    assert config.items() == expected_dict.items()
    assert config.keys() == expected_dict.keys()
    assert list(config.values()) == list(expected_dict.values())
    # deep = True
    expected_dict_deep = {'param1': 0.1,
                          'subconfig1': {'param2': 3.0},
                          'subconfig2': {'param3': 20.0, 'subconfig3': {'param4': 'string'}},
                          'def_second_path': def_second,
                          'exp_second_path': None,
                          'save': 'test'}
    assert config.items(deep=True) == expected_dict_deep.items()
    assert list(config.values(deep=True)) == list(expected_dict_deep.values())


def test_merge_pattern(capsys, yaml_default, yaml_experiment):
    config = load_config(yaml_experiment, default_config=yaml_default)
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    config.merge({"param*": 0.2})
    check_integrity(config, 0.2)
    config.merge({"*param*": 0.2})
    check_integrity(config, 0.2, 0.2, 0.2, 0.2)
    config.subconfig2.merge({"*param*": 0.4})
    check_integrity(config, 0.2, 0.2, 0.4, 0.4)
    assert config.config_metadata["config_hierarchy"] == [yaml_default,
                                                          yaml_experiment,
                                                          {'param*': 0.2}, {'*param*': 0.2},
                                                          {'subconfig2.*param*': 0.4}]
    config.subconfig2.subconfig3.merge({"*param*": "0.5"})
    check_integrity(config, 0.2, 0.2, 0.4, "0.5")
    assert config.config_metadata["config_hierarchy"] == [yaml_default,
                                                          yaml_experiment,
                                                          {'param*': 0.2}, {'*param*': 0.2},
                                                          {'subconfig2.*param*': 0.4},
                                                          {'subconfig2.subconfig3.*param*': "0.5"}]


def test_merge_from_command_line(capsys, yaml_default, yaml_experiment):
    def mcl(cfg, string):
        to_merge = cfg._get_command_line_dict(string_to_merge=string)
        if to_merge:
            print(f"Merging from command line : {to_merge}")
            cfg._merge(to_merge)
    config = load_config(yaml_experiment, default_config=yaml_default)
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    mcl(config, "--lr=0.5 --param1=1 --subconfig1.param2=0.6")
    captured = capsys.readouterr()
    assert captured.out.count("WARNING") == 1
    assert "WARNING: parameter 'lr', encountered while merging params from the command line, does not match a param" \
           " in the config" in captured.out
    check_integrity(config, 1, 0.6)
    mcl(config, "--subconfig2.subconfig3.param4='test test'")
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    check_integrity(config, 1, 0.6, p4="test test")
    config_2 = load_config(yaml_experiment, default_config=yaml_default)
    mcl(config_2, config.get_command_line_argument(do_return_string=True))
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    check_integrity(config_2, 1, 0.6, p4="test test")
    mcl(config_2, "--param1 2 --*param2=none --*param3=none !str "
                  "--*param4= '[ 1!int  ,0.5 !float, {string:\\'[as !str}!dict]' !list")
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    check_integrity(config_2, 2, None, "none", p4=[1, 0.5, {"string": "'[as"}])
    mcl(config, config_2.get_command_line_argument(do_return_string=True))
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    check_integrity(config, 2, None, "none", p4=[1, 0.5, {"string": "'[as"}])
    mcl(config, "--subconfig1.param2")
    assert config.subconfig1.param2 is True
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    mcl(config, "--subconfig1.param2=False")
    assert config.subconfig1.param2 is False
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    mcl(config, "--subconfig1.param2=1")
    assert config.subconfig1.param2 is True
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    with pytest.raises(Exception, match="could not convert string to float: 'False'"):
        mcl(config, "--param1=False")


def test_method_name(capsys):
    config = make_config({"save": "test"}, do_not_merge_command_line=True)
    captured = capsys.readouterr()
    assert captured.out.count("WARNING") == 1
    assert config.details() == "\nMAIN CONFIG :\nConfiguration hierarchy :\n> {'save': 'test'}\n\n - save : test\n"
    config.merge({"save": 0.1})
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    assert config.details() == "\nMAIN CONFIG :\nConfiguration hierarchy :\n> {'save': 'test'}\n> {'save': 0.1}\n\n" \
                               " - save : 0.1\n"


def test_details(capsys, yaml_default, yaml_experiment):
    config = load_config(yaml_experiment, default_config=yaml_default)
    s = f"\nMAIN CONFIG :\nConfiguration hierarchy :\n> {yaml_default}\n" \
        f"> {yaml_experiment}\n\n - param1 : 0.1\n - subconfig1 : \n	" \
        "SUBCONFIG1 CONFIG :\n	 - param2 : 2.0\n\n - subconfig2 : \n	SUBCONFIG2 CONFIG :\n	 - param3 : 30.0\n" \
        "	 - subconfig3 : \n		SUBCONFIG3 CONFIG :\n		 - param4 : string\n\n\n"
    assert s == config.details(no_show="*_path")
    s = f"\nMAIN CONFIG :\nConfiguration hierarchy :\n> {yaml_default}\n" \
        f"> {yaml_experiment}\n\n - param1 : 0.1\n - subconfig1 : SUBCONFIG1\n" \
        " - subconfig2 : \n	SUBCONFIG2 CONFIG :\n	 - param3 : 30.0\n	 - subconfig3 : \n		SUBCONFIG3 CONFIG :\n" \
        "		 - param4 : string\n\n\n"
    assert s == config.details(expand_only=["subconfig2"], no_show="*_path")
    s = f"\nMAIN CONFIG :\nConfiguration hierarchy :\n> {yaml_default}\n" \
        f"> {yaml_experiment}\n\n - param1 : 0.1\n - subconfig1 : \n" \
        "	SUBCONFIG1 CONFIG :\n	 - param2 : 2.0\n\n - subconfig2 : SUBCONFIG2\n"
    assert s == config.details(no_expand=["subconfig2"], no_show="*_path")


def test_variations(capsys):
    config = make_config({"p1": 0.1, "p2": 1.0, "var1": [{"p1": 0.1}, {"p1": 0.2}],
                          "var2": [{"p2": 1.0}, {"p2": 2.0}, {"p2": 3.0}],
                          "grid": None},
                         config_class=template(yaml_default),
                         do_not_merge_command_line=True)
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


def test_pre_processing(capsys, tmp_file_name, yaml_no_file_call_processing_while_loading, yaml_default,
                        yaml_no_file_call_processing_while_loading_nested, yaml_default_preproc_default_dot_param,
                        yaml_experiment):
    preprocessing = {"*param*": lambda x: x+1 if not isinstance(x, str) else x}
    config = load_config(default_config=yaml_default_preproc_default_dot_param, preprocessing=preprocessing)
    assert config.param1.param2 == 3
    config = load_config(yaml_experiment, default_config=yaml_default,
                         preprocessing=preprocessing)
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    check_integrity(config, 1.1, 3.0, 31.0)
    config.save(str(tmp_file_name))
    config2 = load_config(str(tmp_file_name), default_config=yaml_default, preprocessing=preprocessing)
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    assert config == config2
    config2.merge({"param1": 0.2})
    assert config2.param1 == 1.2
    assert yaml_no_file_call_processing_while_loading[0] == yaml_no_file_call_processing_while_loading[1]
    assert yaml_no_file_call_processing_while_loading_nested[0] == yaml_no_file_call_processing_while_loading_nested[1]


def test_post_processing(capsys, yaml_default, yaml_experiment, tmp_file_name,
                         yaml_default_preproc_default_dot_param):
    # Does post-processing work after load_config ?
    postprocessing = {"*param*": lambda x: x + 1 if not isinstance(x, str) else x}
    config = load_config(default_config=yaml_default_preproc_default_dot_param, postprocessing=postprocessing)
    assert config.param1.param2 == 3
    config = load_config(yaml_experiment, default_config=yaml_default,
                         postprocessing=postprocessing)
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    check_integrity(config, 1.1, 3.0, 31.0)
    config.save(str(tmp_file_name))
    config2 = load_config(str(tmp_file_name), default_config=yaml_default, postprocessing=postprocessing)
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    assert config == config2
    config2 = load_config(str(tmp_file_name), default_config=yaml_default)
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    check_integrity(config2)
    # Does post-processing work after manual merge ?
    config = load_config(default_config=yaml_default_preproc_default_dot_param, postprocessing=postprocessing)
    config.merge(yaml_default_preproc_default_dot_param)
    assert config.param1.param2 == 3
    config = load_config({}, default_config=yaml_default,
                         postprocessing=postprocessing)
    config.merge(yaml_experiment)
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    check_integrity(config, 1.1, 3.0, 31.0)
    config.save(str(tmp_file_name))
    config2 = load_config({}, default_config=yaml_default, postprocessing=postprocessing)
    config2.merge(str(tmp_file_name))
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    assert config == config2
    config2 = load_config({}, default_config=yaml_default)
    config2.merge(str(tmp_file_name))
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    check_integrity(config2)
    # Does post-processing interact correctly with save ?

    class Storage:
        def __init__(self, **kwargs):
            self.stored = kwargs
    postprocessing = {"*_to_store": lambda x: Storage(**x)}
    config = make_config({"a": 10, "b.to_store": {"i": 1, "j": 2}}, post_processing_dict=postprocessing)
    config.save(str(tmp_file_name))
    assert config == make_config(str(tmp_file_name), post_processing_dict=postprocessing)
    assert make_config(str(tmp_file_name)).b.to_store == {"i": 1, "j": 2}
    assert make_config(str(tmp_file_name)).a == 10
    # Does post-processing interact correctly with get_command_line_arguments ?
    config = make_config({"a": 10, "b.to_store": {"i": 1, "j": 2}}, post_processing_dict=postprocessing)
    dico = config._get_command_line_dict(config.get_command_line_argument(do_return_string=True))
    assert config == make_config(dico, post_processing_dict=postprocessing)
    assert make_config(dico).b.to_store == {"i": 1, "j": 2}
    assert make_config(dico).a == 10


def test_save_reload(capsys, tmp_file_name, yaml_default, yaml_experiment):
    config = load_config(yaml_experiment, default_config=yaml_default)
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    config.save(str(tmp_file_name))
    config2 = load_config(str(tmp_file_name), default_config=yaml_default)
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    config2.save(str(tmp_file_name))
    config3 = load_config(str(tmp_file_name), default_config=yaml_default)
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    assert config == config2 == config3


def test_save_reload_method_param(capsys, tmp_file_name):
    config = make_config({"save": 1}, do_not_merge_command_line=True)
    captured = capsys.readouterr()
    assert captured.out.count("WARNING") == 1
    config.save(str(tmp_file_name))
    config2 = make_config({"save": 1}, do_not_merge_command_line=True)
    config2.merge(str(tmp_file_name))
    captured = capsys.readouterr()
    assert captured.out.count("WARNING") == 1
    config2.save(str(tmp_file_name))
    config3 = make_config({"save": 1}, do_not_merge_command_line=True)
    config3.merge(str(tmp_file_name))
    captured = capsys.readouterr()
    assert captured.out.count("WARNING") == 1
    config3.save(str(tmp_file_name))
    assert config == config2 == config3


def test_craziest_config(capsys, yaml_craziest_config, tmp_file_name):
    class Storage:
        def __init__(self, **kwargs):
            self.stored = kwargs

        def __repr__(self):
            return f"<STORED: {self.stored}>"

        def __eq__(self, other):
            return self.stored == other.stored
    post_processing = {"*p4": lambda x: Storage(**x)}
    config = make_config(yaml_craziest_config[0], do_not_merge_command_line=True, additional_configs_suffix="_path")
    second = os.path.join(Path(yaml_craziest_config[0]).parents[0], "d_second.yaml")
    third = os.path.join(Path(yaml_craziest_config[0]).parents[0], "d_third.yaml")
    dico_str = "{'a': 4}"
    dico_str2 = "{'b': 5}"
    s = f"\nMAIN CONFIG :\n" \
        f"Configuration hierarchy :\n" \
        f"> {yaml_craziest_config[0]}\n\n" \
        f" - p1 : 1\n - c1 : \n	C1 CONFIG :\n	 - c2 : \n		C2 CONFIG :\n		 - c3 : \n" \
        f"			C3 CONFIG :\n			 - p2 : 2\n			 - c5 : \n				C5 CONFIG :\n" \
        f"				 - c6 : \n					C6 CONFIG :\n					 - p4 : {dico_str}\n\n" \
        f"				 - p5 : 5\n" \
        f"				 - s_path : {third}\n\n\n		 - p6 : 6\n		 - f_path : {second}\n\n\n" \
        f" - c4 : \n	C4 CONFIG :\n	 - p3 : 3\n	 - p7 : 7\n\n - c3 : \n	C3 CONFIG :\n	 - p2 : 2\n	 - c5 : \n" \
        f"		C5 CONFIG :\n		 - c6 : \n			C6 CONFIG :\n			 - p4 : {dico_str}\n\n		 - p5 : 5\n" \
        f"		 - s_path : {third}\n\n\n - p6 : 6\n - f_path : {second}\n"
    assert config.details() == s
    config = make_config(yaml_craziest_config[0], yaml_craziest_config[1],
                         do_not_merge_command_line=True, additional_configs_suffix="_path",
                         post_processing_dict=post_processing)
    second_e = os.path.join(Path(yaml_craziest_config[0]).parents[0], "e_second.yaml")
    s = f"\nMAIN CONFIG :\n" \
        f"Configuration hierarchy :\n" \
        f"> {yaml_craziest_config[0]}\n" \
        f"> {yaml_craziest_config[1]}\n\n" \
        f" - p1 : 1\n - c1 : \n	C1 CONFIG :\n	 - c2 : \n		C2 CONFIG :\n		 - c3 : \n" \
        f"			C3 CONFIG :\n			 - p2 : 2\n			 - c5 : \n				C5 CONFIG :\n" \
        f"				 - c6 : \n					C6 CONFIG :\n					 - p4 : <STORED: {dico_str2}>\n\n" \
        f"				 - p5 : 8\n" \
        f"				 - s_path : {third}\n\n\n		 - p6 : 7\n		 - f_path : {second_e}\n\n\n" \
        f" - c4 : \n	C4 CONFIG :\n	 - p3 : test\n	 - p7 : test2\n\n - c3 : \n	C3 CONFIG :\n	 - p2 : 2\n	 - c5" \
        f" : \n		C5 CONFIG :\n		 - c6 : \n			C6 CONFIG :\n			 - p4 : <STORED: {dico_str}>\n\n" \
        f"		 - p5 : 5\n		 - s_path : {third}\n\n\n - p6 : 7\n - f_path : {second}\n"
    assert config.details() == s
    config.save(str(tmp_file_name))
    config2 = make_config(yaml_craziest_config[0], str(tmp_file_name),
                          do_not_merge_command_line=True, additional_configs_suffix="_path",
                          post_processing_dict=post_processing)
    assert config == config2
    dico = config._get_command_line_dict(config.get_command_line_argument(do_return_string=True))
    assert config == make_config(dico, post_processing_dict=post_processing)


def test_pattern_matching():
    assert compare_string_pattern("", "*")
    assert compare_string_pattern("abcdefgh0123,:", "*")
    assert compare_string_pattern("abcdefgh0123", "abcdefgh0123")
    assert compare_string_pattern("abcdefgh0123", "abcde*gh0123")
    assert compare_string_pattern("abcdeffffgh0123", "abcde*gh0123")
    assert compare_string_pattern("abcdefgh0123", "*a*b*c*d*e*f*g*h*0*1*2*3*")
    assert compare_string_pattern("abcdefgh0123", "*0123")
    assert compare_string_pattern("abcdefgh0123", "abcd*")
    assert compare_string_pattern("abcdefgh0123", "a**3")

    assert not compare_string_pattern("abcdefgh0123", "abcdefgh012")
    assert not compare_string_pattern("abcdefgh0123", "abcde*g0123")
    assert not compare_string_pattern("abcdefgh0123ffffh0123", "abcde*gh0123")
    assert not compare_string_pattern("abcdefgh0123", "*3*3*3")


def test_warnings(capsys, tmp_file_name, yaml_default):
    # config = ConfigForTests(config_path_or_dictionary={"param": None, "lparam": [], "dparam": {"param2": 1}})
    # config.merge_from_command_line("--param=1 --lparam=[1] --dparam={param2:2,param3:3}")
    # captured = capsys.readouterr()
    # assert captured.out.count("is None. It cannot be replaced from the") == 1
    # assert captured.out.count("is an empty list. It cannot be replaced from the") == 1
    # assert captured.out.count(" key. This key will be set") == 1
    # assert config.dparam == {"param2": 2, "param3": None}
    config = make_config({"param": 1}, do_not_merge_command_line=True, overwriting_regime="unsafe")
    config.save(str(tmp_file_name))
    config.merge(str(tmp_file_name))
    captured = capsys.readouterr()
    assert captured.out.count("YOU ARE LOADING AN UNSAFE CONFIG") == 1
    config = make_config({"param": 1}, do_not_merge_command_line=True)
    config.merge({"*d": 1})
    captured = capsys.readouterr()
    assert captured.out.count("will be ignored : it does not match any") == 1


def test_errors(capsys, yaml_default_unlinked, yaml_default_sub_variations, yaml_default_set_twice, yaml_default):
    with pytest.raises(Exception, match="'overwriting_regime' needs to be either 'auto-save', 'locked' or 'unsafe'."):
        _ = make_config({"param": 1}, do_not_merge_command_line=True, overwriting_regime="a")
    with pytest.raises(Exception, match=".*is not a sub-config, it cannot be accessed.*"):
        _ = make_config({"param": 1}, do_not_merge_command_line=True)["param.param"]
    with pytest.raises(Exception, match="Overwriting params in locked configs is not allowed."):
        config = make_config({"param": 1}, do_not_merge_command_line=True, overwriting_regime="locked")
        config.param = 2
    with pytest.raises(Exception, match="build_from_configs needs to be called with at least one config."):
        _ = template().build_from_configs(do_not_merge_command_line=True)
    with pytest.raises(Exception, match="build_from_configs needs to be called with at least one config."):
        _ = template().build_from_configs([], do_not_merge_command_line=True)
    with pytest.raises(Exception, match=".*\nplease use build_from_configs.*"):
        _ = template().build_from_configs([template(default_config=yaml_default).get_default_config_path()],
                                          [{"param1": 1}],
                                          do_not_merge_command_line=True)
    with pytest.raises(Exception, match="No filename was provided.*"):
        make_config({"param": 1}).save()
    with pytest.raises(Exception, match="Grid element.*"):
        _ = make_config({"param": 1, "var": [], "grid": ["var"]}, config_class=template()).create_variations()
    with pytest.raises(Exception, match="Grid element.*"):
        _ = make_config({"param": 1, "grid": ["var"]}, config_class=template()).create_variations()
    with pytest.raises(Exception, match="Variations parsing failed.*"):
        make_config({"param": 1, "var": 1}, config_class=template())
    with pytest.raises(Exception, match="Variations parsing failed.*"):
        make_config({"param": 1, "var": [1]}, config_class=template())
    with pytest.raises(Exception, match="Variations parsing failed.*"):
        make_config({"param": 1, "var": {"a": 1}}, config_class=template())
    with pytest.raises(Exception, match="Grid parsing failed.*"):
        make_config({"param": 1, "grid": {}}, config_class=template())
    with pytest.raises(Exception, match="ERROR : path not found .*"):
        template()(config_path_or_dictionary="not_found")
    with pytest.raises(Exception, match="'config_metadata' is a special parameter.*"):
        make_config({"config_metadata": 1})
    with pytest.raises(Exception, match="'overwriting_regime' is a special parameter.*"):
        metadata = 'Saving time : <date> (<in_seconds>) ; Regime : something_incorrect'
        make_config({"config_metadata": metadata})
    with pytest.raises(Exception, match="Failed to set parameter.*"):
        config = make_config({"param": 1})
        config.merge({"param.param": 1})
    with pytest.raises(Exception, match="Failed to set parameter.*"):
        _ = make_config({"param": 1, "param.param": 1})
    with pytest.raises(Exception, match=".*character is not authorized in the default config.*"):
        _ = make_config({"param*": 1})
    with pytest.raises(Exception, match=".*Unlinked sub-configs are not allowed.*"):
        _ = make_config(yaml_default_unlinked)
    captured = capsys.readouterr()
    assert captured.out.count("ERROR while pre-processing param") == 4
    with pytest.raises(Exception, match=".*Please declare all your variations in the main config.*"):
        _ = make_config(yaml_default_sub_variations, config_class=template())
    with pytest.raises(Exception, match=".*is a protected name and cannot be used as a parameter.*"):
        _ = make_config({"_nesting_hierarchy": 1})
    with pytest.raises(Exception, match=".*cannot be merged : it is not in the default.*"):
        config = make_config({"param": 1})
        config.merge({"subconfig.param": 1})
    with pytest.raises(Exception, match=".*cannot be merged : it is not in the default.*"):
        config = make_config({"param": 1})
        config.merge({"param2": 1})
    with pytest.raises(Exception, match=".*This replacement cannot be performed.*"):
        subconfig = make_config({"param": 1})
        config = make_config({"subconfig": subconfig})  # don't do this at home
        config.merge({"subconfig": 1})
    with pytest.raises(Exception, match=".* was set twice.*"):
        _ = make_config({"param": 1, "set_twice_path": yaml_default_set_twice}, config_class=template())
