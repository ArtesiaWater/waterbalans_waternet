"""
Script to run an EAG or GAF by name.

If Script fails, please check if data has been
extracted in data directory by running prepare_input_data.py

"""

import waterbalans as wb
import matplotlib as mpl
mpl.interactive(True)

# Run eag by name
e = wb.run_eag_by_name("2250-EAG-2", csvdir="../data/input_csv")

# Compare eag to Excel
wb.utils.compare_to_excel_balance(e, pickle_dir="../data/excel_pklz")
