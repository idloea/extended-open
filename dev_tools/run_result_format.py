from pathlib import Path
from dev_tools.result_format import gather_all_input_and_output_results

if __name__ == "__main__":
    results_folder_name = '20230608-104124'
    directory_string = f'results/{results_folder_name}'
    directory = Path(directory_string)
    input_json_file_name = 'input_case_data.json'
    output_json_file_name = 'output_case_data.json'
    all_input_and_output_results = gather_all_input_and_output_results(directory=directory,
                                                                       input_json_file_name=input_json_file_name,
                                                                       output_json_file_name=output_json_file_name)
    excel_file_name = f'{results_folder_name}.xlsx'
    excel_path_string = f'results/{excel_file_name}'
    excel_path = Path(excel_path_string)
    all_input_and_output_results.to_excel(excel_path)
