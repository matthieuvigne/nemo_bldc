from setuptools import setup, find_namespace_packages
from pathlib import Path

setup(
    name='nemo_bldc',
    version='1.0.0',
    description='A tool to evaluate and compare brushless motors',
    long_description=Path('README.md').read_text('utf8'),
    author="Matthieu Vigne",
    license="MIT",
    packages=find_namespace_packages('src'),
    package_dir={'': 'src'},
    package_data={
        "nemo_bldc.ressources": ["*.glade", "*.json"],
        "nemo_bldc.doc": ["*.pdf"]
    },
    install_requires=[
        "pycairo", # Can cause issues if not installed before PyGObject - use pip and not setuptools to run install
        "pytest",
        "scipy",
        "numpy",
        "matplotlib",
        "PyGObject"],
    entry_points={
          'console_scripts': [
             'nemo_bldc = nemo_bldc.nemo:nemo_main'
          ]
      },
    include_package_data=True,
    zip_safe=False)
