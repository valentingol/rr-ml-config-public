import os
import yaml
import pytest
from rr.ml.config import YamlSection


@pytest.fixture
def yaml_content():
    return 'gpu: false \n' \
           'image_file_paths: ["/shared/input"] \n' \
           'marching_cubes_resolution: 64 \n' \
           'pred_landmarks: false \n' \
           '--- !pifu \n' \
           'load_netG_checkpoint_path: "./checkpoints/test/netG_latest"'


@pytest.fixture
def tmp_file_name(tmpdir):
    filename = tmpdir / 'tmp_output.yaml'
    yield filename
    # uncomment the following lines if you want the file to be removed at the end of a test
    if os.path.exists(filename):
        os.remove(filename)


# @pytest.mark.skip("just temp test")
def test_write_read_yaml(yaml_content, tmp_file_name):
    YamlSection.register_for_yaml()
    print('TEST')
    # create yaml file
    yaml_config_orig = list(yaml.load_all(yaml_content, Loader=yaml.FullLoader))

    # store yaml file
    with open(tmp_file_name, "w") as s:
        yaml.dump_all(yaml_config_orig, s)

    # load yaml file and compare with original
    with open(tmp_file_name) as s:
        yaml_config_loaded = list(yaml.load_all(s, Loader=yaml.FullLoader))
        for section_orig, section_loaded in zip(yaml_config_orig, yaml_config_loaded):
            assert section_orig == section_loaded
