import json
import os
from pathlib import Path
import pandas as pd


def get_dataframe_from_directory_with_json_files(directory: Path, json_file_name: str) -> pd.DataFrame:
    folders = os.listdir(directory)
    dataframe = pd.DataFrame()
    for folder in folders:
        folder_path = Path(directory / str(folder))
        data_path = folder_path / json_file_name
        with open(data_path, 'r') as json_file:
            json_data = json.load(json_file)
        data = pd.json_normalize(json_data)
        data['FolderName'] = folder
        dataframe = pd.concat([dataframe, data], ignore_index=True)

    return dataframe


def gather_all_input_and_output_results(directory: Path, input_json_file_name: str,
                                        output_json_file_name: str) -> pd.DataFrame:
    input_dataframe = get_dataframe_from_directory_with_json_files(directory=directory,
                                                                   json_file_name=input_json_file_name)
    output_dataframe = get_dataframe_from_directory_with_json_files(directory=directory,
                                                                    json_file_name=output_json_file_name)
    output_dataframe.drop('FolderName', axis=1, inplace=True)
    input_and_output_dataframe = pd.concat([input_dataframe, output_dataframe], axis=1)
    df = input_and_output_dataframe.set_index('FolderName')
    return df

