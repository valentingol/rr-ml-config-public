import yaml


class YamlSection:
    def __init__(self, tag, content):
        self._tag = tag
        self._content = content

    def __eq__(self, other):
        return self.tag == other.tag and self.content == other.content

    def __contains__(self, item):
        return item in self._content

    def __getitem__(self, item):
        return self._content[item]

    def __setitem__(self, key, value):
        self._content[key] = value

    @property
    def tag(self):
        return self._tag

    @property
    def content(self):
        return self._content

    @staticmethod
    def from_yaml(loader, tag, node):
        data = YamlSection(tag, loader.__class__.construct_mapping(loader, node))
        return data

    @staticmethod
    def to_yaml(dumper, section):
        return dumper.represent_mapping(section.tag, section.content)

    @staticmethod
    def register_for_yaml():
        yaml.add_multi_constructor('', YamlSection.from_yaml)
        yaml.add_representer(YamlSection, YamlSection.to_yaml)
