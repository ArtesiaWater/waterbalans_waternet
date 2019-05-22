import waterbalans as wb
import matplotlib as mpl
mpl.interactive(True)

e = wb.run_eag_by_name("2330-GAF")
wb.utils.compare_to_excel_balance(e)
