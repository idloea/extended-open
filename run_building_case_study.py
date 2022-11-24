from building_case_study import run

if __name__ == "__main__":
    yaml_files = ['01_january_no_flexibility.yaml',
                  '02_february_no_flexibility.yaml',
                  '03_march_no_flexibility.yaml',
                  '04_april_no_flexibility.yaml',
                  '05_may_no_flexibility.yaml',
                  '06_june_no_flexibility.yaml',
                  '07_july_no_flexibility.yaml',
                  '08_august_no_flexibility.yaml',
                  '09_september_no_flexibility.yaml',
                  '10_october_no_flexibility.yaml',
                  '11_november_no_flexibility.yaml',
                  '12_december_no_flexibility.yaml'
                  ]
    run(yaml_files=yaml_files)
