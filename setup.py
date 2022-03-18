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
    version=version,
    description='Reactive Reality Machine Learning Config System',
    url='https://gitlab.com/reactivereality/public/rr-ml-config-public',
    author='Reactive Reality AG',
    packages=['rr.ml.config'],
    package_dir={'rr.ml.config': 'rr-ml-config'},
    install_requires=["pyyaml"]
)
