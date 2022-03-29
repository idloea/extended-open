import os
import yaml

case_path = 'Data/cases'


def load_case(case_file: str):
    with open(os.path.join(case_path, case_file)) as file:
        case = yaml.safe_load(file)
    return case
