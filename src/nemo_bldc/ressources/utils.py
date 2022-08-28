import pkg_resources
import json

from ..physics.motor import Motor

def get_ressource_path(filename:str):
    return pkg_resources.resource_filename(__name__, filename)

def load_motor_library(source_file: str):
    '''
    Load a motor library json file.
    '''
    library = {}
    with open(source_file, "r") as f:
        data = json.load(f)
        for k, d in data.items():
            try:
                library[k] = Motor.FromDict(d)
            except KeyError:
                print(f"Warning: failed to load {k}")
    return library

DEFAULT_LIBRARY = load_motor_library(get_ressource_path("motor_library.json"))