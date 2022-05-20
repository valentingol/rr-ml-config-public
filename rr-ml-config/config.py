"""
Reactive Reality Machine Learning Config System - Configuration object
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

import yaml
import os
import sys
import functools
import time
from copy import deepcopy
from pathlib import Path


def update_state(state_descriptor):
    def decorator_update_state(func):
        @functools.wraps(func)
        def wrapper_update_state(self, *args, **kwargs):
            state_to_append = state_descriptor.split(";")[0]  # state name
            for i in state_descriptor.split(";")[1:]:
                state_to_append += f";{getattr(self, i)}"  # additional information
            self._state.append(
                state_to_append + f";arg0={args[0]}"
            )  # first arg of function call
            value = func(self, *args, **kwargs)
            self._state.pop(-1)
            return value

        return wrapper_update_state

    return decorator_update_state


class Configuration:
    def __init__(
        self,
        name="main",
        overwriting_regime="auto-save",
        config_path_or_dictionary=None,
        nesting_hierarchy=None,
        state=None,
        main_config=None,
        from_argv=False,
    ):
        """
        Should probably never be called directly by the user. Please use one of the constructors instead (load_config,
        build_from_configs, build_from_argv).
        :param name: name for the config or sub-config
        :param overwriting_regime: can be "auto-save" (default, when a param is overwritten it is merged instead and the
        config is saved automatically if it had been saved previously), "locked" (params can't be overwritten except
        using merge explicitly) or "unsafe" (params can be freely overwritten but reproducibility is not guaranteed).
        :param config_path_or_dictionary: path or dictionary to create the config from
        :param nesting_hierarchy: list containing the names of all the configs in the sub-config chain leading to this
        config
        :param state: processing state used for state tracking and debugging
        :param main_config: main config corresponding to this sub-config, or None if this config is the main config
        :return: none
        """
        config_path_or_dictionary = (
            self.get_default_config_path()
            if config_path_or_dictionary is None
            else config_path_or_dictionary
        )

        # PROTECTED ATTRIBUTES
        object.__setattr__(self, "_can_set_attributes", True)
        self._state = [] if state is None else state
        self._main_config = self if main_config is None else main_config
        self._methods = [
            name
            for name in dir(self)
            if name not in ["_can_set_attributes", "_state", "_main_config"]
        ]
        self._name = name
        self._pre_process_master_switch = True
        self._reference_folder = None
        self._was_last_saved_as = None
        self._variation_name = (
            None if main_config is None else main_config.get_variation_name()
        )
        self._nesting_hierarchy = (
            [] if nesting_hierarchy is None else [i for i in nesting_hierarchy]
        )
        self._from_argv = from_argv
        self._configuration_variations = []
        self._configuration_variations_names = []
        self._grids = []
        self._sub_configs_list = []
        self._former_saving_time = None
        self._protected_attributes = [i for i in self.__dict__] + [
            "_protected_attributes"
        ]

        # SPECIAL ATTRIBUTES
        self.config_metadata = {
            "saving_time": time.time(),
            "config_hierarchy": [],
            "overwriting_regime": overwriting_regime
            if main_config is None
            else main_config.config_metadata["overwriting_regime"],
        }
        if self.config_metadata["overwriting_regime"] not in [
            "unsafe",
            "auto-save",
            "locked",
        ]:
            raise ValueError(
                "'overwriting_regime' needs to be either 'auto-save', 'locked' or 'unsafe'."
            )

        # INITIALISATION
        self._state.append(f"setup;{self._name}")
        self._init_from_config(config_path_or_dictionary)
        self.config_metadata["config_hierarchy"] = (
            []
            if not self._nesting_hierarchy
            else [
                i
                for i in main_config.get(
                    ".".join(self._nesting_hierarchy[:-1]), main_config
                ).config_metadata["config_hierarchy"]
            ]
        )
        self.config_metadata["config_hierarchy"] += [config_path_or_dictionary]
        if not self._nesting_hierarchy:
            self._check_for_unlinked_sub_configs()
        if main_config is None:
            self.turn_on_pre_processing()
        self._state.pop(-1)
        self._can_set_attributes = False

    def __repr__(self):
        return "<Configuration:" + self.get_name() + ">"

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        for param in self._get_user_defined_attributes():
            try:
                if self[param] != other[param]:
                    return False
            except AttributeError:
                return False
        for param in other._get_user_defined_attributes():
            try:
                _ = self[param]
            except AttributeError:
                return False
        return True

    def __hash__(self):
        return hash(repr(self.get_dict(deep=True)))

    def __getitem__(self, item):
        if "." in item and "*" not in item:
            sub_config_name = (
                "___" + item.split(".")[0]
                if item.split(".")[0] in self._methods
                else item.split(".")[0]
            )
            sub_config = getattr(self, sub_config_name)
            if not isinstance(sub_config, self.__class__):
                raise TypeError(
                    f"As the parameter {sub_config_name} is not a sub-config, it cannot be accessed.\n"
                    f"{self._did_you_mean(sub_config_name, filter_type=self.__class__)}"
                )
            return sub_config[".".join(item.split(".")[1:])]
        else:
            return getattr(self, "___" + item if item in self._methods else item)

    def __setattr__(self, key, value):
        if (
            self._can_set_attributes
            or self._main_config.get_attribute_changeability()
            or self.config_metadata["overwriting_regime"] == "unsafe"
        ):
            object.__setattr__(self, key, value)
        elif self.config_metadata["overwriting_regime"] == "auto-save":
            self.merge({key: value}, verbose=True, from_code=True)
        elif self.config_metadata["overwriting_regime"] == "locked":
            raise RuntimeError("Overwriting params in locked configs is not allowed.")
        else:
            raise ValueError(
                f"No behaviour determined for value {self.config_metadata['overwriting_regime']} of "
                f"parameter 'overwriting_regime'."
            )

    def __iter__(self):
        return iter(self._get_user_defined_attributes())

    @classmethod
    def load_config(
        cls,
        *config_paths,
        default_config_path=None,
        overwriting_regime="auto-save",
        do_not_merge_command_line=False,
        verbose=True,
        **kwargs,
    ):
        """
        First creates a config using the default config, then merges config_path into it. If config_path is a list,
        successively merges all configs in the list instead from index 0 to the last.
        :param config_paths: config's path or dictionary, or list of default config's paths or dictionaries to merge
        :param default_config_path: default config's path or dictionary
        :param overwriting_regime: can be "auto-save" (default, when a param is overwritten it is merged instead and the
        config is saved automatically if it had been saved previously), "locked" (params can't be overwritten except
        using merge explicitly) or "unsafe" (params can be freely overwritten but reproducibility is not guaranteed).
        :param do_not_merge_command_line: if True, prevents the execution of the _merge_command_line function
        :param verbose: controls the verbose in the config creation process
        :return: instance of Configuration object containing the desired config
        """
        default_config_path = (
            cls.get_default_config_path()
            if default_config_path is None
            else default_config_path
        )
        if verbose:
            print("Building config from default : ", default_config_path)
        config = cls(
            config_path_or_dictionary=default_config_path,
            overwriting_regime=overwriting_regime,
            **kwargs,
        )
        if config_paths and isinstance(config_paths[0], list):
            config_paths = config_paths[0]
        for path in config_paths:
            config.merge(path, verbose=verbose)
        if not do_not_merge_command_line:
            config._merge_command_line()
        return config

    @classmethod
    def build_from_configs(
        cls,
        *configs,
        overwriting_regime="auto-save",
        do_not_merge_command_line=False,
        verbose=True,
        **kwargs,
    ):
        """
        First creates a config using the first config provided (or the first config in the provided list), then merges
        the subsequent configs into it from index 1 to the last.
        :param configs: config's path or dictionary, or list of default config's paths or dictionaries to merge
        :param overwriting_regime: can be "auto-save" (default, when a param is overwritten it is merged instead and the
        config is saved automatically if it had been saved previously), "locked" (params can't be overwritten except
        using merge explicitly) or "unsafe" (params can be freely overwritten but reproducibility is not guaranteed).
        :param do_not_merge_command_line: if True, prevents the execution of the _merge_command_line function
        :param verbose: controls the verbose in the config creation process
        :return: instance of Configuration object containing the desired config
        """
        if not configs or (isinstance(configs[0], list) and not configs[0]):
            raise TypeError(
                "build_from_configs needs to be called with at least one config."
            )
        if isinstance(configs[0], list) and len(configs) == 1:
            configs = configs[0]
        elif isinstance(configs[0], list):
            raise TypeError(
                f"Invalid argument : {configs}\n"
                f"please use build_from_configs([cfg1, cfg2, ...]) or build_from_configs(cfg1, cfg2, ...)"
            )
        return cls.load_config(
            list(configs[1:]),
            default_config_path=configs[0],
            overwriting_regime=overwriting_regime,
            do_not_merge_command_line=do_not_merge_command_line,
            verbose=verbose,
            **kwargs,
        )

    @classmethod
    def build_from_argv(
        cls,
        fallback=None,
        default_config_path=None,
        overwriting_regime="auto-save",
        do_not_merge_command_line=False,
        verbose=True,
        **kwargs,
    ):
        """
        Assumes a pattern of the form '--config <path_to_config>' or '--config [<path1>,<path2>,...]' in sys.argv (the
        brackets are optional), and builds a config from the specified paths by merging them into the default config in
        the specified order.
        :param fallback: config path or dictionary, or list of config paths or dictionaries to fall back to if no
        config was detected in the argv
        :param default_config_path: default config's path or dictionary
        :param overwriting_regime: can be "auto-save" (default, when a param is overwritten it is merged instead and the
        config is saved automatically if it had been saved previously), "locked" (params can't be overwritten except
        using merge explicitly) or "unsafe" (params can be freely overwritten but reproducibility is not guaranteed).
        :param do_not_merge_command_line: if True, prevents the execution of the _merge_command_line function
        :param verbose: controls the verbose in the config creation process
        :return: instance of Configuration object containing the desired config
        """
        if "--config" not in sys.argv and fallback is None:
            raise TypeError("The pattern '--config' was not detected in sys.argv.")
        elif "--config" in sys.argv:
            fallback = [
                c.strip(" ")
                for c in sys.argv[sys.argv.index("--config") + 1].strip("[]").split(",")
            ]

        return cls.load_config(
            fallback,
            default_config_path=default_config_path,
            overwriting_regime=overwriting_regime,
            do_not_merge_command_line=do_not_merge_command_line,
            verbose=verbose,
            from_argv=True,
            **kwargs,
        )

    def compare(self, other, reduce=False):
        """
        Returns a list of tuples, where each tuple represents a parameter that is different between the "self"
        configuration and the "other" configuration. Tuples are written in the form :
        (parameter_name, parameter_value_in_other). If parameter_name does not exist in other, (parameter_name, None)
        is given instead.
        :param other: config to compare self with
        :param reduce: tries to reduce the size of the output text as much as possible
        :return: difference list
        """

        def _investigate_parameter(parameter_name, object_to_check):
            if reduce:
                name_path = parameter_name.split(".")
                to_display = name_path.pop(-1)
                while (
                    len(
                        [
                            p
                            for p in object_to_check.get_parameter_names(deep=True)
                            if self._compare_string_pattern(p, "*." + to_display)
                        ]
                    )
                    != 1
                    and name_path
                ):
                    to_display = name_path.pop(-1) + "." + to_display
            else:
                to_display = parameter_name
            return (
                self.get(parameter_name, None),
                other.get(parameter_name, None),
                to_display,
            )

        differences = []
        for name in self.get_parameter_names():
            value_in_self, value_in_other, displayed_name = _investigate_parameter(
                name, self
            )
            if value_in_other != value_in_self:
                if not reduce:
                    differences.append((displayed_name, value_in_other))
                else:
                    if not isinstance(value_in_self, self.__class__):
                        if isinstance(value_in_self, dict) and isinstance(
                            value_in_other, dict
                        ):
                            to_ret = {}
                            for key in value_in_self:
                                if key not in value_in_other:
                                    to_ret[key] = None
                                elif value_in_self[key] != value_in_other[key]:
                                    to_ret[key] = value_in_other[key]
                            for key in value_in_other:
                                if key not in value_in_self:
                                    to_ret[key] = value_in_other[key]
                            differences.append((displayed_name, to_ret))
                        else:
                            differences.append((displayed_name, value_in_other))
        for name in other.get_parameter_names():
            _, value_in_other, displayed_name = _investigate_parameter(name, other)
            if name not in self.get_parameter_names() and value_in_other is not None:
                if reduce:
                    if not isinstance(value_in_other, self.__class__):
                        differences.append((displayed_name, value_in_other))
                else:
                    differences.append((displayed_name, value_in_other))
        return differences

    def copy(self):
        """
        Returns a safe, independent copy of the config
        :return: instance of Configuration that is a deep copy of the config
        """
        return deepcopy(self)

    def create_variations(self):
        """
        Creates a list of configs that are derived from the current config using the internally tracked variations and
        grids registered via the corresponding functions (register_as_config_variations and register_as_grid).
        :return: the list of configs corresponding to the tracked variations
        """
        variations_names_to_use = [i[0] for i in self._configuration_variations]
        variations_names_to_use_changing = [
            i[0] for i in self._configuration_variations
        ]
        variations_to_use = [i[1] for i in self._configuration_variations]
        variations_to_use_changing = [i[1] for i in self._configuration_variations]
        variations = []
        variations_names = []

        # Adding grids
        for grid in self._grids:
            grid_to_add = []
            names_to_add = []
            for dimension in grid:
                if dimension not in variations_names_to_use:
                    raise TypeError(
                        f"Grid element {dimension} is an empty list or not a registered variation configuration."
                    )
                if dimension in variations_names_to_use_changing:
                    index = variations_names_to_use_changing.index(dimension)
                    variations_names_to_use_changing.pop(index)
                    variations_to_use_changing.pop(index)
                if not grid_to_add:
                    grid_to_add = [
                        [i]
                        for i in variations_to_use[
                            variations_names_to_use.index(dimension)
                        ]
                    ]
                    for var_name in self._configuration_variations_names:
                        if var_name[0] == dimension:
                            names_to_add = [var_name[0] + "_" + i for i in var_name[1]]
                else:
                    new_grid_to_add = []
                    new_names_to_add = []
                    for current_variation_index in range(len(grid_to_add)):
                        for index in range(
                            len(
                                variations_to_use[
                                    variations_names_to_use.index(dimension)
                                ]
                            )
                        ):
                            new_grid_to_add.append(
                                grid_to_add[current_variation_index]
                                + [
                                    variations_to_use[
                                        variations_names_to_use.index(dimension)
                                    ][index]
                                ]
                            )
                            for var_name in self._configuration_variations_names:
                                if var_name[0] == dimension:
                                    new_names_to_add.append(
                                        names_to_add[current_variation_index]
                                        + "*"
                                        + var_name[0]
                                        + "_"
                                        + var_name[1][index]
                                    )
                    grid_to_add = [[c2 for c2 in c1] for c1 in new_grid_to_add]
                    names_to_add = [c1 for c1 in new_names_to_add]
            variations = variations + grid_to_add
            variations_names = variations_names + names_to_add

        # Adding remaining non-grid variations
        for remaining_variation_index in range(len(variations_to_use_changing)):
            for variation_index in range(
                len(variations_to_use_changing[remaining_variation_index])
            ):
                variations.append(
                    [
                        variations_to_use_changing[remaining_variation_index][
                            variation_index
                        ]
                    ]
                )
                name = variations_names_to_use_changing[remaining_variation_index]
                for var_name in self._configuration_variations_names:
                    if var_name[0] == name:
                        variations_names.append(
                            name + "_" + var_name[1][variation_index]
                        )

        # Creating configs
        variation_configs = []
        for variation_index in range(len(variations)):
            variation_configs.append(
                self.__class__.load_config(
                    self.config_metadata["config_hierarchy"][1:]
                    + variations[variation_index],
                    default_config_path=self.config_metadata["config_hierarchy"][0],
                    overwriting_regime=self.config_metadata["overwriting_regime"],
                    verbose=False,
                )
            )
            variation_configs[-1].set_variation_name(
                variations_names[variation_index], deep=True
            )
        return variation_configs

    def details(self, show_only=None, expand_only=None, no_show=None, no_expand=None):
        """
        Creates and returns a string describing all the parameters in the config and its sub-configs.
        :param show_only: if not None, list of names referring to params. Only params in the list are displayed in
        the details.
        :param expand_only: if not None, list of names referring to sub-configs. Only sub-configs in the list are
        unrolled in the details.
        :param no_show: if not None, list of names referring to params. Params in the list are not displayed in the
        details.
        :param no_expand: if not None, list of names referring to sub-configs. Sub-configs in the list are not unrolled
        in the details.
        :return: string containing the details
        """

        def _for_sub_config(names):
            new = (
                None
                if names is None
                else [
                    ".".join(c.split(".")[1:])
                    for c in names
                    if c.split(".")[0] == attribute and len(c.split(".")) > 1
                ]
            )
            return None if not new else new

        def _match_params(names):
            if names is None or (len(names) == 1 and names[0] is None):
                return None
            new_names = [n for n in names if "*" not in n]
            for name in [n for n in names if "*" in n]:
                new_names = new_names + [
                    p
                    for p in self.get_parameter_names(deep=True)
                    if self._compare_string_pattern(p, name)
                ]
            return new_names

        def _dict_apply(dictionary, function):
            return {k: function(v) for k, v in dictionary.items()}

        constraints = {
            "show_only": show_only,
            "expand_only": expand_only,
            "no_show": no_show,
            "no_expand": no_expand,
        }
        constraints = _dict_apply(
            constraints, lambda x: x if isinstance(x, list) else [x]
        )
        constraints = _dict_apply(constraints, _match_params)
        string_to_return = (
            "\n"
            + "\t" * len(self._nesting_hierarchy)
            + self.get_name().upper()
            + " CONFIG :\n"
        )
        if not self._nesting_hierarchy:
            string_to_return += "Configuration hierarchy :\n"
            for hierarchy_level in self.config_metadata["config_hierarchy"]:
                string_to_return += f"> {hierarchy_level}\n"
            string_to_return += "\n"
        to_print = [
            attribute
            for attribute in self._get_user_defined_attributes()
            if (
                (
                    constraints["show_only"] is None
                    or attribute in constraints["show_only"]
                )
                and (
                    constraints["no_show"] is None
                    or attribute not in constraints["no_show"]
                )
            )
        ]
        for attribute in to_print:
            string_to_return += (
                "\t" * len(self._nesting_hierarchy) + " - " + attribute + " : "
            )
            if isinstance(self[attribute], self.__class__):
                if (
                    constraints["no_expand"] is None
                    or attribute not in constraints["no_expand"]
                ) and (
                    constraints["expand_only"] is None
                    or attribute
                    in [c.split(".")[0] for c in constraints["expand_only"]]
                ):
                    string_to_return += (
                        self[attribute].details(
                            **(_dict_apply(constraints, _for_sub_config))
                        )
                        + "\n"
                    )
                else:
                    string_to_return += self[attribute].get_name().upper() + "\n"
            else:
                string_to_return += str(self[attribute]) + "\n"
        return string_to_return

    def get(self, parameter_name, default_value):
        """
        Behaves similarly to dict.get(parameter_name, default_value)
        :param parameter_name: parameter to query
        :param default_value: value to return if the parameter does not exist
        :return: queried value
        """
        try:
            return self[parameter_name]
        except (AttributeError, TypeError):
            return default_value

    def get_all_linked_sub_configs(self):
        """
        Returns the list of all sub-configs that are directly linked to the root config by a chain of other sub-configs.
        For this to be the case, all of those sub-configs need to be contained directly in a parameter of another
        sub-config. For example, a sub-config stored in a list that is a parameter of a sub-config is not linked.
        :return: list corresponding to the linked sub-configs
        """
        all_linked_configs = []
        for i in self._get_user_defined_attributes():
            object_to_scan = getattr(self, "___" + i if i in self._methods else i)
            if isinstance(object_to_scan, self.__class__):
                all_linked_configs = (
                    all_linked_configs
                    + [object_to_scan]
                    + object_to_scan.get_all_linked_sub_configs()
                )
        return all_linked_configs

    def get_all_sub_configs(self):
        """
        Returns the list of all sub-configs, including sub-configs of other sub-configs
        :return: list corresponding to the sub-configs
        """
        all_configs = [i for i in self._sub_configs_list]
        for i in self._sub_configs_list:
            all_configs = all_configs + i.get_all_sub_configs()
        return all_configs

    def get_attribute_changeability(self):
        return self._can_set_attributes

    def get_command_line_argument(
        self, deep=True, do_return_string=False, ignore_unknown_types=False
    ):
        def _escape_symbols(string_to_escape, symbols):
            for symbol in symbols:
                string_to_escape = string_to_escape.replace(symbol, f"\\{symbol}")
            return string_to_escape

        def _get_param_as_string(param, in_iterable=False):
            if param is None:
                return "none"
            elif isinstance(param, list):
                return f"[{','.join([_get_param_as_string(i, True) for i in param])}] !list"
            elif isinstance(param, dict):
                return (
                    "{"
                    + ",".join(
                        [
                            f"{k}:{_get_param_as_string(v, True)}"
                            for k, v in param.items()
                        ]
                    )
                    + "} !dict"
                )
            else:
                if isinstance(param, int):
                    type_forcing = "int"
                elif isinstance(param, float):
                    type_forcing = "float"
                elif isinstance(param, str):
                    type_forcing = "str"
                elif isinstance(param, bool):
                    type_forcing = "bool"
                elif ignore_unknown_types:
                    print(
                        f"WARNING: parameter value {param} will not have its type enforced because it is not in "
                        f"[int, float, str, bool]."
                    )
                    type_forcing = ""
                else:
                    raise TypeError(
                        f"Parameter value {param} will not have its type enforced because it is not in "
                        f"[int, float, str, bool]. Pass ignore_unknown_types=True to avoid enforcing "
                        f"type when type is unknown."
                    )
                value = str(param)
                value = _escape_symbols(value, ["\\"])
                if in_iterable:
                    value = _escape_symbols(value, ["{", "}", "[", "]", ","])
                    value = _escape_symbols(value, ["{", "}", "[", "]", ","])
                value = _escape_symbols(value, ["'", '"', " "])
                return value + (f" !{type_forcing}" if type_forcing else "")

        to_return = []
        for p in self.get_parameter_names(deep=deep):
            if not isinstance(self[p], self.__class__):
                pair = _get_param_as_string(self[p])
                if pair.count(" !"):
                    pair_as_list = pair.split(" !")
                    param_value, param_force = (
                        " !".join(pair_as_list[:-1]),
                        pair_as_list[-1],
                    )
                    to_return.append(
                        _escape_symbols(
                            f"--{p} '{param_value}' !{param_force}", ["{", "}", "*"]
                        )
                    )
                else:
                    to_return.append(_escape_symbols(f"--{p} {pair}", ["{", "}", "*"]))

        return " ".join(to_return) if do_return_string else to_return

    @staticmethod
    def get_default_config_path():
        """
        Returns the path to the default config of the project. This function must be implemented at project-level.
        :return: string corresponding to the path to the default config of the project
        """
        raise NotImplementedError

    def get_dict(self, deep=True):
        """
        Returns a dictionary corresponding to the config.
        :param deep: whether to recursively turn sub-configs into dicts or keep them as sub-configs
        :return: dictionary corresponding to the config
        """
        return {
            key: (
                self[key]
                if not deep or not isinstance(self[key], self.__class__)
                else self[key].get_dict()
            )
            for key in self._get_user_defined_attributes()
        }

    def get_main_config(self):
        return self._main_config

    def get_name(self):
        """
        Returns the name of the config. It is composed of a specified part (or 'main' when unspecified) and an indicator
        of its index in the list of variations of its parent if it is a variation of a config. This indicator is
        prefixed by '_VARIATION_'.
        :return: string corresponding to the name
        """
        variation_suffix = (
            "_VARIATION_" + self._variation_name
            if self._variation_name is not None
            else ""
        )
        return self._name + variation_suffix

    def get_nesting_hierarchy(self):
        """
        Returns the nesting hierarchy of the config
        :return: list corresponding to the nesting hierarchy
        """
        return self._nesting_hierarchy

    def get_parameter_names(self, deep=True):
        complete_list = self._get_user_defined_attributes()
        if deep:
            order = len(self.get_nesting_hierarchy())
            for subconfig in self.get_all_linked_sub_configs():
                complete_list += [
                    ".".join(subconfig.get_nesting_hierarchy()[order:] + [param])
                    for param in subconfig.get_parameter_names(deep=False)
                ]
        return complete_list

    def get_variation_name(self):
        """
        Returns the variation name of the config
        :return: variation name
        """
        return self._variation_name

    def items(self, deep=False):
        return self.get_dict(deep).items()

    def keys(self):
        return self.get_dict(deep=False).keys()

    @update_state("merging;_name")
    def merge(self, config_path, from_code=False, verbose=False):
        """
        Merges provided config path of dictionary into the current config.
        :param config_path: path or dictionary for the config to merge
        :param from_code: whether merge was called by setting a variable from the code
        :param verbose: controls the verbose in the config creation and merging process
        :return: none
        """
        if self._main_config == self:
            object.__setattr__(self, "_can_set_attributes", True)
            if verbose:
                if from_code:
                    print(f"Merging from code : {config_path}")
                else:
                    print(f"Merging from new config : {config_path}")
            self._init_from_config(config_path)
            self.config_metadata["config_hierarchy"].append(config_path)
            self._check_for_unlinked_sub_configs()
            self.turn_on_pre_processing()
            self._can_set_attributes = False
            if self.config_metadata["overwriting_regime"] == "auto-save":
                if self._was_last_saved_as is not None:
                    self.save()
        else:
            dicts_to_merge = []
            if isinstance(config_path, str):
                with open(self._find_path(config_path)) as yaml_file:
                    for dictionary_to_add in yaml.load_all(
                        yaml_file, Loader=self._get_yaml_loader()
                    ):
                        dicts_to_merge.append(dictionary_to_add)
                    yaml_file.close()
            else:
                dicts_to_merge.append(config_path)
            for dictionary in dicts_to_merge:
                self._main_config.merge(
                    {
                        ".".join(self._nesting_hierarchy) + "." + a: b
                        for a, b in dictionary.items()
                    },
                    from_code=from_code,
                    verbose=verbose,
                )

    def merge_from_command_line(self, string_to_merge=None):
        print(
            "WARNING: merge_from_command_line is now deprecated and will automatically start after using any "
            "constructor."
        )
        print(
            "You can remove the 'config.merge_from_command_line()' line from your code now :) it's redundant."
        )
        print(
            "If you were using it manually to pass a string, you should avoid doing that, but can use "
            "'config._merge_command_line(string_to_merge)'."
        )
        self._merge_command_line(string_to_merge)

    def parameters_pre_processing(self):
        """
        Returns a dictionary where the keys are parameter names (supporting the '*' character as a replacement for any
        number of characters) and the items are functions. The pre-processing functions need to take a single argument
        and return the new value of the parameter after pre-processing. During pre-processing, all parameters
        corresponding to the parameter name are passed to the corresponding function and their value is replaced by the
        value returned by the corresponding function. This function must be implemented at project-level.
        :return: dictionary of the pre-processing functions
        """
        raise NotImplementedError

    def set_variation_name(self, name, deep=False):
        """
        Sets the variation index of the config. This function is not intended to be used by the user.
        :param name: index to set the variation index with
        :param deep: whether to also recursively set the variation name of all sub-configs
        :return: none
        """
        object.__setattr__(self, "_variation_name", name)
        if deep:
            for subconfig in self._sub_configs_list:
                subconfig.set_variation_name(name, deep=True)

    def register_as_additional_config_file(self, path):
        """
        Pre-processing function used to register the corresponding parameter as a path to another config file. The new
        config file will then also be used to build the config currently being built.
        :param path: config's path or list of paths
        :return: the same path as the input once the parameters from the new config have been added
        """
        if isinstance(path, list):
            for individual_path in path:
                self._init_from_config(individual_path)
            return [
                self._find_path(path)
                if isinstance(individual_path, str)
                else individual_path
                for individual_path in path
            ]
        else:
            self._init_from_config(path)
            return self._find_path(path) if isinstance(path, str) else path

    def register_as_config_variations(self, list_to_register):
        """
        Pre-processing function used to register the corresponding parameter as a variation for the current config.
        Please note that config variations need to be declared in the root config.
        :param list_to_register: list of configs
        :return: the same list of configs once the configs have been added to the internal variation tracker
        """
        name = None
        for state in self._state[::-1]:
            if state.startswith("pre_processing"):
                if state.count(";arg0=") > 1:
                    raise ValueError("How did you even manage to raise this ?")
                name = state.split(";arg0=")[-1]
                break
        if name is None:
            raise RuntimeError(
                "register_as_config_variations was called outside _pre_process_parameter."
            )

        def is_single_var(single):
            return isinstance(single, str) or (isinstance(single, dict))

        def add_to_variations(variations, names=None):
            if variations:
                for index, variation in enumerate(self._configuration_variations):
                    if variation[0] == name:
                        self._configuration_variations.pop(index)
                        break
                self._configuration_variations.append((name, variations))
                if names is None:
                    self._configuration_variations_names.append(
                        (
                            name,
                            [str(i) for i in list(range(len(variations)))],
                        )
                    )
                else:
                    self._configuration_variations_names.append((name, names))

        if self._nesting_hierarchy:
            raise RuntimeError(
                f"Variations declared in sub-configs are invalid ({name}).\n"
                "Please declare all your variations in the main config."
            )
        elif isinstance(list_to_register, dict) and (
            sum(
                [
                    is_single_var(potential_single)
                    for potential_single in list_to_register.values()
                ]
            )
            == len(list_to_register)
        ):
            add_to_variations(
                list(list_to_register.values()), names=list(list_to_register.keys())
            )
        elif isinstance(list_to_register, list) and (
            sum(
                [
                    is_single_var(potential_single)
                    for potential_single in list_to_register
                ]
            )
            == len(list_to_register)
        ):
            add_to_variations(list_to_register)
        elif list_to_register is not None:
            raise TypeError(
                f"Variations parsing failed : variations parameters must be a list of configs or a dict"
                f"containing only configs. Instead, got : {list_to_register}"
            )

        return list_to_register

    @staticmethod
    def register_as_experiment_path(path):
        """
        Pre-processing function used to register the corresponding parameter as the folder used for the current
        experiment. This will automatically create the relevant folder structure and append an experiment index at the
        end of the folder name to avoid any overwriting. The path needs to be either None or an empty string (in which
        case the pre-processing does not happen), or an absolute path, or a path relative to the current working
        directory.
        :param path: None, '', absolute path or path relative to the current working directory
        :return: the actual created path with its appended index
        """
        if not path:
            return path
        folder, experiment = os.path.dirname(path), os.path.basename(path)
        os.makedirs(folder, exist_ok=True)
        experiments = [i for i in os.listdir(folder) if i.startswith(experiment)]
        experiment_id = max([int(i.split("_")[-1]) for i in experiments] + [-1]) + 1
        path = os.path.join(folder, f"{experiment}_{experiment_id}")
        os.makedirs(path, exist_ok=True)
        return path

    def register_as_grid(self, list_to_register):
        """
        Pre-processing function used to register the corresponding parameter as a grid for the current config. Grids
        are made of several parameters registered as variations. Instead of adding the variations in those parameters to
        the list of variations for this config, a grid will be created and all its components will be added instead.
        :param list_to_register: list of parameters composing the grid
        :return: the same list of parameters once the grid has been added to the internal grid tracker
        """
        if isinstance(list_to_register, list) and all(
            [isinstance(param, str) for param in list_to_register]
        ):
            self._grids.append(list_to_register)
        elif list_to_register is not None:
            raise TypeError(
                f"Grid parsing failed : unrecognized grid declaration : {list_to_register}"
            )
        return list_to_register

    def save(self, filename=None, save_header=True, save_hierarchy=True):
        """
        Saves the current config at the provided location. The saving format allows for a perfect recovery of the config
        by using : config = Configuration.load_config(filename). If no filename is given, overwrites the last save.
        :param filename: path to the saving location of the config
        :param save_header: whether to save the config metadata as the fist parameter. This will tag the saved file as a
        saved config in the eye of the config system when it gets merged, which will deactivate pre-processing.
        :param save_hierarchy: whether to save config hierarchy as a '*_hierarchy.yaml' file
        :return: none
        """
        if filename is None:
            if self._was_last_saved_as is None:
                raise RuntimeError(
                    "No filename was provided, but the config was never saved before so there is no "
                    "previous save to overwrite."
                )
            else:
                filename = self._was_last_saved_as
        self.config_metadata["creation_time"] = time.time()
        file_path, file_extension = os.path.splitext(filename)
        file_extension = file_extension if file_extension else ".yaml"
        config_dump_path = file_path + file_extension
        to_dump = {
            a: getattr(self, "___" + a if a in self._methods else a)
            if a != "config_metadata"
            else self._format_metadata()
            for a in (["config_metadata"] if save_header else [])
            + self._get_user_defined_attributes()
        }
        with open(config_dump_path, "w") as f:
            yaml.dump(to_dump, f, Dumper=self._get_yaml_dumper(), sort_keys=False)

        if save_hierarchy:
            hierarchy_dump_path = f"{file_path}_hierarchy{file_extension}"
            to_dump = {"config_hierarchy": self.config_metadata["config_hierarchy"]}
            with open(hierarchy_dump_path, "w") as f:
                yaml.dump(to_dump, f, Dumper=self._get_yaml_dumper())

        object.__setattr__(self, "_was_last_saved_as", config_dump_path)
        print(f"Configuration saved in : {os.path.abspath(config_dump_path)}")

    def turn_on_pre_processing(self):
        object.__setattr__(self._main_config, "_pre_process_master_switch", True)

    def turn_off_pre_processing(self):
        object.__setattr__(self._main_config, "_pre_process_master_switch", False)

    def values(self, deep=False):
        return self.get_dict(deep).values()

    # ||||| PRIVATE METHODS |||||

    @staticmethod
    def _are_same_sub_configs(first, second):
        if first.get_name() != second.get_name():
            return False
        nh1, nh2 = first.get_nesting_hierarchy(), second.get_nesting_hierarchy()
        if len(nh1) != len(nh2) or any([nh1[i] != nh2[i] for i in range(len(nh1))]):
            return False
        return True

    def _check_for_unlinked_sub_configs(self):
        all_configs = self.get_all_sub_configs()
        linked_configs = self.get_all_linked_sub_configs()
        for i in all_configs:
            found_correspondence = False
            for j in linked_configs:
                if self._are_same_sub_configs(i, j):
                    found_correspondence = True
                    break
            if not found_correspondence:
                raise RuntimeError(
                    f"Sub-config {i.get_name()} is unlinked. Unlinked sub-configs are not allowed."
                )

    @staticmethod
    def _compare_string_pattern(name, pattern):
        pattern = pattern.split("*")
        if len(pattern) == 1:
            return pattern[0] == name
        if not (name.startswith(pattern[0]) and name.endswith(pattern[-1])):
            return False
        for fragment in pattern:
            index = name.find(fragment)
            if index == -1:
                return False
            else:
                name = name[index+len(fragment) :]
        return True

    def _did_you_mean(self, name, filter_type=None, suffix=""):
        params = {}
        for parameter in self.get_parameter_names(deep=True):
            if filter_type is None or isinstance(self[parameter], filter_type):
                for index in range(len(name)):
                    if self._compare_string_pattern(
                        parameter, name[:index] + "*" + name[index+1 :]
                    ):
                        if parameter in params:
                            params[parameter] += 1
                        else:
                            params[parameter] = 1
        if not params:
            return ""
        params_to_print = sorted(params.keys(), key=lambda x: params[x], reverse=True)
        to_return = "Perhaps what you actually meant is in this list :"
        for p in params_to_print:
            to_return += f"\n- {p}{suffix}"
        return to_return

    def _find_path(self, path):
        # If the path is absolute, use it...
        if os.path.isabs(path):
            if os.path.exists(path):
                self._reference_folder = Path(path).parents[0]
                return path

        # ... if not, search relatively to some reference folders.
        else:

            # First check relatively to parent configs' directories...
            for config in reversed(self.config_metadata["config_hierarchy"]):
                if isinstance(config, str):
                    relative_path = os.path.join(Path(config).parents[0], path)
                    if os.path.exists(relative_path):
                        return os.path.abspath(relative_path)

            # ... then also check the current reference folder since the config hierarchy is not always up-to-date...
            if self._reference_folder is not None:
                relative_path = os.path.join(self._reference_folder, path)
                if os.path.exists(relative_path):
                    return os.path.abspath(relative_path)
            if (
                self._main_config is not None
                and self._main_config._reference_folder is not None
            ):
                relative_path = os.path.join(self._main_config._reference_folder, path)
                if os.path.exists(relative_path):
                    return os.path.abspath(relative_path)

            # ... and finally, check relatively to the current working directory.
            if os.path.exists(path):
                path_to_return = os.path.abspath(path)
                self._reference_folder = Path(path_to_return).parents[0]
                return path_to_return
        raise FileNotFoundError(f"ERROR : path not found ({path}).")

    def _format_metadata(self):
        return (
            f"Saving time : {time.ctime(self.config_metadata['saving_time'])} "
            f"({self.config_metadata['saving_time']}) ; "
            f"Regime : {self.config_metadata['overwriting_regime']}"
        )

    def _get_yaml_loader(self):
        def generic_constructor(yaml_loader, tag, node):
            sub_config_name = tag[1:]
            self._nesting_hierarchy.append(sub_config_name)
            if yaml_loader.constructed_objects:
                dict_to_return = self.__class__(
                    name=sub_config_name,
                    config_path_or_dictionary=yaml_loader.construct_mapping(
                        node, deep=True
                    ),
                    nesting_hierarchy=self._nesting_hierarchy,
                    state=self._state,
                    main_config=self._main_config,
                )
                if all(
                    [
                        not self._are_same_sub_configs(i, dict_to_return)
                        for i in self._sub_configs_list
                    ]
                ):
                    self._sub_configs_list.append(dict_to_return)

            else:
                dict_to_return = {
                    sub_config_name: self.__class__(
                        name=sub_config_name,
                        config_path_or_dictionary=yaml_loader.construct_mapping(
                            node, deep=True
                        ),
                        nesting_hierarchy=self._nesting_hierarchy,
                        state=self._state,
                        main_config=self._main_config,
                    )
                }
                if all(
                    [
                        not self._are_same_sub_configs(
                            i, dict_to_return[sub_config_name]
                        )
                        for i in self._sub_configs_list
                    ]
                ):
                    self._sub_configs_list.append(dict_to_return[sub_config_name])
            self._nesting_hierarchy.pop(-1)
            return dict_to_return

        loader = yaml.FullLoader
        yaml.add_multi_constructor("", generic_constructor, Loader=loader)
        return loader

    def _get_yaml_dumper(self):
        def config_representer(yaml_dumper, class_instance):
            return yaml_dumper.represent_mapping(
                "!" + class_instance.get_name(),
                {
                    a[3:]
                    if a.startswith("___")
                    else a: self._format_metadata()
                    if a == "config_metadata"
                    else b
                    for (a, b) in class_instance.__dict__.items()
                    if a not in self._protected_attributes
                    and not (
                        class_instance.get_nesting_hierarchy()
                        and a in ["config_metadata"]
                    )
                },
            )

        dumper = yaml.Dumper
        dumper.add_representer(self.__class__, config_representer)
        return dumper

    def _get_user_defined_attributes(self):
        return [
            i[3:] if i.startswith("___") else i
            for i in self.__dict__
            if i not in self._protected_attributes + ["config_metadata"]
        ]

    @update_state("_init_from_config;_name")
    def _init_from_config(self, config_path_or_dict, verbose=False):
        if config_path_or_dict is not None:
            if isinstance(config_path_or_dict, str):
                with open(self._find_path(config_path_or_dict)) as yaml_file:
                    for dictionary_to_add in yaml.load_all(
                        yaml_file, Loader=self._get_yaml_loader()
                    ):
                        for item in dictionary_to_add.items():
                            self._process_item_to_merge_or_add(item, verbose=verbose)
            else:
                for item in config_path_or_dict.items():
                    self._process_item_to_merge_or_add(item, verbose=verbose)

    @update_state("working_on;_name")
    def _process_item_to_merge_or_add(self, item, verbose=False):
        key, value = item

        # Process metadata. If there is metadata, treat the rest of the merge as "loading a saved file"...
        # (which will deactivate the parameter pre-processing for this merge)
        if key == "config_metadata":
            pattern = "Saving time : * (*) ; Regime : *"
            if not isinstance(value, str) or not self._compare_string_pattern(
                value, pattern
            ):
                raise RuntimeError(
                    "'config_metadata' is a special parameter. Please do not edit or set it."
                )

            regime = value.split(" : ")[-1]
            if regime == "unsafe":
                print(
                    "WARNING: YOU ARE LOADING AN UNSAFE CONFIG FILE. Reproducibility with corresponding"
                    " experiment is not ensured"
                )
            elif regime not in ["auto-save", "locked"]:
                raise ValueError(
                    "'overwriting_regime' is a special parameter. It can only be set to 'auto-save'"
                    " (default), 'locked' or 'unsafe'."
                )
            self.config_metadata["overwriting_regime"] = regime

            self._former_saving_time = float(value.split("(")[-1].split(")")[0])
            self.turn_off_pre_processing()
            return

        # ...do not accept other protected attributes to be merged...
        if key in self._protected_attributes:
            raise RuntimeError(
                f"Error : '{key}' is a protected name and cannot be used as a parameter name."
            )

        # ... otherwise, process the data normally :
        else:

            # If we are merging a parameter into a previously defined config...
            if not any([state.startswith("setup") for state in self._state]):
                self._merge_item(key, value, verbose=verbose)

            # ... or if we are creating a config for the first time and are adding non-existing parameters to it
            else:
                self._add_item(key, value)

    def _merge_item(self, key, value, verbose=False):
        if "*" in key:
            to_merge = {}
            for param in self.get_parameter_names(deep=True):
                if self._compare_string_pattern(param, key):
                    to_merge[param] = value
            if not to_merge:
                print(
                    f"WARNING : parameter '{key}' will be ignored : it does not match any existing parameter."
                )
            else:
                print(
                    f"Pattern parameter '{key}' will be merged into the following matched "
                    f"parameters : {list(to_merge.keys())}."
                )
            self._init_from_config(to_merge)
        elif "." in key:
            name, new_key = key.split(".", 1)
            try:
                sub_config = getattr(
                    self, "___" + name if name in self._methods else name
                )
            except AttributeError:
                raise AttributeError(
                    f"ERROR : parameter {key} cannot be merged : "
                    f"it is not in the default '{self.get_name().upper()}' config.\n"
                    f"{self._did_you_mean(key)}"
                )

            if isinstance(sub_config, self.__class__):
                sub_config._init_from_config({new_key: value})
            else:
                raise TypeError(
                    f"Failed to set parameter {key} : {key.split('.')[0]} is not a sub-config.\n"
                    f"{self._did_you_mean(key.split('.')[0], filter_type=self.__class__, suffix=key.split('.', 1)[1])}"
                )
        else:
            try:
                old_value = getattr(self, "___" + key if key in self._methods else key)
            except AttributeError:
                raise AttributeError(
                    f"ERROR : parameter {key} cannot be merged : "
                    f"it is not in the default '{self.get_name().upper()}' config.\n"
                    f"{self._did_you_mean(key)}"
                )
            if isinstance(old_value, self.__class__):
                if not isinstance(value, self.__class__):
                    raise TypeError(
                        f"Trying to set sub-config {old_value._name}\nwith non-config element {value}.\n"
                        f"This replacement cannot be performed."
                    )
                else:
                    old_value._init_from_config(value.get_dict(deep=False))
            else:
                if verbose:
                    print(f"Setting {key} : \nold : {old_value} \nnew : {value}")
                object.__setattr__(
                    self,
                    "___" + key if key in self._methods else key,
                    self._pre_process_parameter(key, value),
                )

    def _add_item(self, key, value):
        if self._state[0].split(";")[0] == "setup" and "*" in key:
            raise ValueError(
                f"The '*' character is not authorized in the default config " f"({key})"
            )
        if "." in key and "*" not in key.split(".")[0]:
            name = key.split(".")[0]
            try:
                sub_config = getattr(
                    self, "___" + name if name in self._methods else name
                )
            except AttributeError:
                # This has to be performed in two steps, otherwise the param
                # inside the new sub-config does not get pre-processed.
                object.__setattr__(
                    self,
                    "___" + name if name in self._methods else name,
                    self.__class__(
                        name=name,
                        overwriting_regime=self._main_config.config_metadata[
                            "overwriting_regime"
                        ],
                        config_path_or_dictionary={},
                        state=self._state,
                        nesting_hierarchy=self._nesting_hierarchy + [name],
                        main_config=self._main_config,
                    ),
                )
                # Now, outside the nested "setup" state during __init__, pre-processing is active
                dict_to_add = {key.split(".", 1)[1]: value}
                self[name]._init_from_config(dict_to_add)
                self[name].config_metadata["config_hierarchy"] += [dict_to_add]
            else:
                if isinstance(sub_config, self.__class__):
                    sub_config._init_from_config({key.split(".", 1)[1]: value})
                else:
                    raise TypeError(
                        f"Failed to set parameter {key} : {key.split('.')[0]} is not a sub-config.\n"
                        f"{self._did_you_mean(key.split('.')[0], filter_type=self.__class__, suffix=key.split('.', 1)[1])}"
                    )
        else:
            try:
                if key != "config_metadata":
                    _ = getattr(self, "___" + key if key in self._methods else key)
                    raise RuntimeError(f"ERROR : parameter '{key}' was set twice.")
            except AttributeError:
                if key in self._methods:
                    print(
                        f"WARNING : '{key}' is the name of a method in the Configuration object."
                    )
                if isinstance(value, self.__class__):
                    # This has to be performed in two steps, otherwise the param
                    # inside the new sub-config does not get pre-processed.
                    object.__setattr__(
                        self,
                        "___" + key if key in self._methods else key,
                        self.__class__(
                            name=value._name,
                            overwriting_regime=self._main_config.config_metadata[
                                "overwriting_regime"
                            ],
                            config_path_or_dictionary={},
                            state=self._state,
                            nesting_hierarchy=self._nesting_hierarchy + [value._name],
                            main_config=self._main_config,
                        ),
                    )
                    # Now, outside the nested "setup" state during __init__, pre-processing is active
                    dict_to_add = {
                        k: value[k] for k in value._get_user_defined_attributes()
                    }
                    self[key]._init_from_config(dict_to_add)
                    self[key].config_metadata["config_hierarchy"] += [dict_to_add]
                else:
                    if (
                        self._state[0].split(";")[0] == "setup"
                        and [i.split(";")[0] for i in self._state].count("setup") < 2
                    ):
                        preprocessed_parameter = self._pre_process_parameter(key, value)
                    else:
                        preprocessed_parameter = value
                    object.__setattr__(
                        self,
                        "___" + key if key in self._methods else key,
                        preprocessed_parameter,
                    )

    def _merge_command_line(self, string_to_merge=None):
        # If a string is passed as input, process it as sys.argv would
        if string_to_merge is not None:
            list_to_merge = [""]
            in_quotes = []
            escaped = False
            for c in string_to_merge:
                if c == "\\" and not escaped:
                    escaped = True
                elif c in ['"', "'"] and not escaped:
                    if not in_quotes or in_quotes[-1] != c:
                        in_quotes.append(c)
                    else:
                        in_quotes.pop(-1)
                elif c == " " and not in_quotes and list_to_merge[-1] and not escaped:
                    list_to_merge.append("")
                else:
                    escaped = False
                    list_to_merge[-1] += c
            if in_quotes:
                raise ValueError(
                    f"Could not parse args : open quotations were left unclosed : {in_quotes}."
                )
        else:
            list_to_merge = sys.argv

        # Gather parameters, their values and their types
        to_merge = {}  # {param: [former_value, new_value, type_forcing], ...}
        found_config_path = not self._from_argv
        in_param = []
        for element in list_to_merge:
            if element.startswith("--") and (
                found_config_path or element[2:] != "config"
            ):
                if "=" in element:
                    pattern, value = element[2:].split("=", 1)
                    value = value if value != "" else None
                else:
                    pattern, value = element[2:], None
                in_param = []
                for parameter in self.get_parameter_names(deep=True):
                    if self._compare_string_pattern(parameter, pattern):
                        in_param.append(parameter)
                        to_merge[parameter] = [self[parameter], value, None]
                if not in_param:
                    print(
                        f"WARNING: parameter {pattern} does not match a param in the config. It will not be merged."
                    )
                    pass
            elif element.startswith("--"):
                in_param = []
                found_config_path = True
            elif in_param and to_merge[in_param[0]][1] is None:
                for parameter in in_param:
                    to_merge[parameter][1] = element
            elif in_param and element[0] == "!":
                if element[1:] in ["int", "float", "str", "bool", "list", "dict"]:
                    for parameter in in_param:
                        to_merge[parameter][2] = element[1:]
                    in_param = []
                else:
                    raise TypeError(
                        f"Unknown type {element[1:]}, should be in [int, float, str, bool, list, dict]."
                    )
            elif in_param:
                for parameter in in_param:
                    to_merge[parameter][1] += f" {element}"

        # Infer types, then merge
        def _adapt_to_type(previous_value, value_to_adapt, force, param):
            def _parse_scalar(raw_string, force_):
                if force_ is None:
                    for forced_type in ["int", "float", "str", "bool", "list", "dict"]:
                        if (
                            raw_string.endswith(f"!{forced_type}")
                            and raw_string[raw_string.rindex("!") - 1] != "\\"
                        ):
                            force_ = forced_type
                            raw_string = raw_string[: -1 - len(forced_type)]
                raw_string.lstrip(" ")
                while raw_string[-1] == " " and raw_string[-2] != "\\":
                    raw_string = raw_string[:-1]
                to_return = ""
                esc = False
                for character in raw_string:
                    if esc or character != "\\":
                        esc = False
                        to_return += character
                    else:
                        esc = True
                return raw_string, force_

            def _parse_container(container_string):
                new_list = [""]
                in_brackets = []
                esc = False
                for character in container_string:
                    if esc:
                        esc = False
                        if character == " ":
                            new_list[-1] += "\\" + character
                        else:
                            new_list[-1] += character
                    else:
                        if character == "\\":
                            esc = True
                        elif character == "," and not in_brackets:
                            new_list.append("")
                        elif character != " " or new_list[-1]:
                            new_list[-1] += character
                            if character in ["[", "{"]:
                                in_brackets.append(character)
                            if character == "]" and in_brackets[-1] == "[":
                                in_brackets.pop(-1)
                            if character == "}" and in_brackets[-1] == "{":
                                in_brackets.pop(-1)
                for i in range(len(new_list)):
                    while new_list[i][-1] == " " and new_list[i][-2] != "\\":
                        new_list[i] = new_list[i][:-1]
                    new_list[i] = new_list[i].replace("\\ ", " ")
                    forced = False
                    for forced_type in ["int", "float", "str", "bool", "list", "dict"]:
                        if (
                            not forced
                            and new_list[i].endswith(f"!{forced_type}")
                            and new_list[i][-2 - len(forced_type)] != "\\"
                        ):
                            forced = True
                            new_list[i] = [
                                new_list[i][: new_list[i].rindex("!")],
                                forced_type,
                            ]
                            while new_list[i][0][-1] == " " and new_list[0][-2] != "\\":
                                new_list[i][0] = new_list[i][0][:-1]
                    if not forced:
                        new_list[i] = [new_list[i], None]
                return new_list

            if value_to_adapt is None:
                return True

            if value_to_adapt.lower() in ["none", "null"] and force is None:
                return None

            scalar_parsed, force = _parse_scalar(value_to_adapt, force)

            if previous_value is None and force is None:
                if scalar_parsed.lower() not in ["none", "null"]:
                    raise TypeError(
                        f"Type of param {param} cannot be inferred because its previous value was None.\n"
                        f"To overwrite None values from command line, please force their type :\n\n"
                        f"Example : \t\t python main.py --none_param=0.001 !float"
                    )
                return None

            if (isinstance(previous_value, str) and force is None) or force == "str":
                return scalar_parsed

            if (isinstance(previous_value, list) and force is None) or force == "list":
                if value_to_adapt[0] == "[" and value_to_adapt[-1] == "]":
                    value_to_adapt = value_to_adapt[1:-1]
                value_to_adapt = (
                    _parse_container(value_to_adapt) if value_to_adapt else []
                )
                if isinstance(previous_value, list):
                    if all(
                        isinstance(i, type(previous_value[-1]))
                        for i in previous_value[:-1]
                    ):
                        return [
                            _adapt_to_type(previous_value[0], v[0], v[1], param)
                            for v in value_to_adapt
                        ]
                    elif len(previous_value) == len(value_to_adapt):
                        return [
                            _adapt_to_type(
                                previous_value[index],
                                value_to_adapt[index][0],
                                value_to_adapt[index][1],
                                param,
                            )
                            for index in range(len(value_to_adapt))
                        ]
                    elif all(
                        [
                            v[1] is not None or v[0].lower() in ["none", "null"]
                            for v in value_to_adapt
                        ]
                    ):
                        return [
                            _adapt_to_type(None, v[0], v[1], param)
                            for v in value_to_adapt
                        ]
                    else:
                        raise TypeError(
                            f"New value for list in '{param}' is inconsistent with old value '{previous_value}'. If the"
                            f" new value is correct, please force the type of the elements in the list so type"
                            f" inference can be done."
                        )
                else:
                    if all(
                        [
                            v[1] is not None or v[0].lower() in ["none", "null"]
                            for v in value_to_adapt
                        ]
                    ):
                        return [
                            _adapt_to_type(None, v[0], v[1], param)
                            for v in value_to_adapt
                        ]
                    else:
                        raise TypeError(
                            f"Since the previous value for '{param}' was not a list, none of its items' "
                            f"values can be inferred. Please force the type of all elements in the new "
                            f"value's list."
                        )

            if (isinstance(previous_value, dict) and force is None) or force == "dict":
                if value_to_adapt[0] == "{" and value_to_adapt[-1] == "}":
                    value_to_adapt = value_to_adapt[1:-1]
                value_to_adapt = (
                    _parse_container(value_to_adapt) if value_to_adapt else []
                )
                if any(value_to_adapt):
                    value_to_adapt = {
                        v[0].split(":", 1)[0]: (v[0].split(":", 1)[1], v[1])
                        for v in value_to_adapt
                    }
                else:
                    value_to_adapt = {}
                if isinstance(previous_value, dict):
                    if all(
                        [
                            key in previous_value
                            or value_to_adapt[key][1] is not None
                            or value_to_adapt[key][0].lstrip(" ").lower()
                            in ["none", "null"]
                            for key in value_to_adapt
                        ]
                    ):
                        return {
                            k.rstrip(" "): _adapt_to_type(
                                previous_value.get(k, None),
                                v[0].lstrip(" "),
                                v[1],
                                param,
                            )
                            for k, v in value_to_adapt.items()
                        }
                    else:
                        raise TypeError(
                            f"New value for dict in '{param}' is inconsistent with old value {previous_value}. If the "
                            f"new value is correct, please force the type of the new elements in the dict so "
                            f"type inference can be done."
                        )
                else:
                    if all(
                        [
                            value_to_adapt[key][1] is not None
                            or value_to_adapt[key][0].lstrip(" ").lower()
                            in ["none", "null"]
                            for key in value_to_adapt
                        ]
                    ):
                        return {
                            k.rstrip(" "): _adapt_to_type(
                                None, v[0].lstrip(" "), v[1], param
                            )
                            for k, v in value_to_adapt.items()
                        }
                    else:
                        raise TypeError(
                            f"Since the previous value for '{param}' was not a dict, none of its keys' "
                            f"values can be inferred. Please force the type of all elements in the new "
                            f"value's dict."
                        )

            if (isinstance(previous_value, int) and force is None) or force == "int":
                return int(scalar_parsed)

            if (
                isinstance(previous_value, float) and force is None
            ) or force == "float":
                return float(scalar_parsed)

            if (isinstance(previous_value, bool) and force is None) or force == "bool":
                return scalar_parsed.strip(" ").lower() not in ["n", "no", "false"]

        to_merge = {k: _adapt_to_type(v[0], v[1], v[2], k) for k, v in to_merge.items()}

        if to_merge:
            print(f"Merging from command line : {to_merge}")
            self.merge(to_merge)

    @update_state("pre_processing;_name")
    def _pre_process_parameter(self, name, parameter):
        if self._main_config._pre_process_master_switch:
            total_name = ".".join(self._nesting_hierarchy + [name])
            transformation_dict = self.parameters_pre_processing()
            for key, item in transformation_dict.items():
                if self._compare_string_pattern(total_name, key):
                    try:
                        parameter = item(parameter)
                    except Exception:
                        print(f"ERROR while pre-processing param {key} :")
                        raise
        return parameter
