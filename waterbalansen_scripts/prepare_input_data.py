from util import unzip_changed_files

# Unzip changed files
unzip_changed_files(
    "../data/input_csv.zip",
    "../data/input_csv",
    check_time=True,
    check_size=True,
    debug=True,
)

# Unzip changed excel balance files for comparison
unzip_changed_files(
    "../data/excel_pklz.zip",
    "../data/excel_pklz",
    check_time=True,
    check_size=True,
    debug=True,
)
