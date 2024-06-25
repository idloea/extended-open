import os
from os.path import normpath


def create_results_folder(results_path: str):
    path_string = normpath(results_path)
    if not os.path.isdir(path_string):
        os.makedirs(path_string)
