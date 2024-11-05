"""
Script to run an EAG or GAF by name. Useful for quickly checking waterbalance
and comparing to Excel.

If Script fails, please check if data has been
extracted in data directory by running `prepare_input_data.py`.

Note: This script will not add outflow timeseries from other EAGs to
the current EAG! This script is therefore not suited to calculating
inflow for "Het Boezem Model". Use `update_and_run_all_fews.py` for that!

"""

import matplotlib as mpl
import waterbalans as wb

mpl.interactive(True)

# Run eag by name
e = wb.run_eag_by_name("3230-EAG-1", csvdir="../data/input_csv", log_level="INFO")
e.plot.dpi = 50

# Compare eag to Excel
wb.utils.compare_to_excel_balance(e, pickle_dir="../data/excel_pklz")
