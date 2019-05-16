# %%
import warnings
"""

Dit script bevat de automatische simulatie van waterbalansen op
EAG-niveau voor alle EAGs. De volgende drie invoerbestanden worden
per EAG gebruikt:

- Modelstructuur (opp)
- Tijdreeksen
- Parameters

"""
# %%
import os
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

import pandas as pd
from pandas.core.common import SettingWithCopyWarning

import waterbalans as wb

pd.options.mode.chained_assignment = 'raise'

warnings.filterwarnings(action='error', category=FutureWarning)
# warnings.filterwarnings(action='error', message="SettingWithCopyWarning")
warnings.filterwarnings(action='error', message="warning:")

# %%
mpl.interactive(True)

# Set database url connection
# wb.pi.setClient(wsdl='http://localhost:8081/FewsPiService/fewspiservice?wsdl')

# Get all files
csvdir = r"C:/Users/dbrak/Documents/01-Projects/17026004_WATERNET_Waterbalansen/03data/DataExport_frompython2"
files = [i for i in os.listdir(csvdir) if i.endswith(".csv")]
eag_df = pd.DataFrame(data=files, columns=["filenames"])
eag_df["ID"] = eag_df.filenames.apply(lambda s: s.split("_")[2].split(".")[0])
eag_df["type"] = eag_df.filenames.apply(lambda s: s.split("_")[0])
eag_df.drop_duplicates(subset=["ID", "type"], keep="first", inplace=True)
file_df = eag_df.pivot(index="ID", columns="type", values="filenames")
file_df.dropna(how="any", axis=0, inplace=True)

f = open("info.log", "w")

tmin = "2000"
tminp = "2010"
tmax = "2015"


eag_list = []
# Loop over files
for i, (fbuckets, fparams, freeks) in file_df.iterrows():
    # if not i == successful_eags[3]:
    if not i in ["3201-EAG-1"]:  # "3050-EAG-1"
        continue
    try:
        buckets = pd.read_csv(os.path.join(csvdir, fbuckets), delimiter=";",
                              decimal=",")
        buckets["OppWaarde"] = pd.to_numeric(buckets.OppWaarde)
        name = i
        eag_id = i.split("-")[-1]

        # Aanmaken van modelstructuur en de bakjes.
        e = wb.create_eag(eag_id, name, buckets)

        # Lees de tijdreeksen in
        reeksen = pd.read_csv(os.path.join(csvdir, freeks), delimiter=";",
                              decimal=",")
        if i == "3200-EAG-2":  # hard-coded drop of (seemingly empty) series
            reeksen.drop(0, inplace=True)
        e.add_series_from_database(reeksen)

        # Simuleer de waterbalans
        params = pd.read_csv(os.path.join(csvdir, fparams), delimiter=";",
                             decimal=",")
        params.rename(columns={"ParamCode": "Code"}, inplace=True)
        params["Waarde"] = pd.to_numeric(params.Waarde)

        # Add missing data manually for MengRiool
        if "MengRiool" in buckets.BakjePyCode.values:
            try:
                enam = reeksen.loc[reeksen.ClusterType ==
                                   "Verdamping", "WaardeAlfa"].iloc[0]
                enam = enam.split("|")[1]
                if "66002" in enam:
                    stn = 240  # Schiphol
                elif "66003" in enam:
                    stn = 260  # De Bilt

                BakjeID_mengriool = buckets.loc[buckets.BakjePyCode ==
                                                "MengRiool", "BakjeID"].iloc[0]

                # knmi station
                newline = params.iloc[-1].copy()
                newline.loc["BakjeID"] = BakjeID_mengriool
                newline.loc["Code"] = "KNMIStation"
                newline.loc["Waarde"] = stn
                newline.name += 1
                params.append(newline)

                # Bmax
                newline = params.iloc[-1].copy()
                newline.loc["BakjeID"] = BakjeID_mengriool
                newline.loc["Code"] = "Bmax"
                newline.loc["Waarde"] = 5e-3
                newline.name += 1
                params.append(newline)

                # POCmax
                newline = params.iloc[-1].copy()
                newline.loc["BakjeID"] = BakjeID_mengriool
                newline.loc["Code"] = "POCmax"
                newline.loc["Waarde"] = 0.5e-3
                newline.name += 1
                params.append(newline)

            except IndexError as ex:
                print("Failed running {} because: '{}: {}'".format(i, type(ex).__name__, "Verdamping is missing."),
                      file=f)
                # raise(ex)
                # continue

        # Simulate
        e.simulate(params=params, tmin=tmin, tmax=tmax)

        b = e.water.validate()
        print(e.name, "Water balance closed: ", b, file=f)

        eag_list.append(e)

        # Plot balancee
        ax = e.plot.aggregated(freq="M", tmin=tminp, tmax=tmax)

        # Plot water level
        ax6 = e.plot.water_level(label_obs=True)

        # Calculate and plot the chloride concentration
        # params_cl = params.loc[params.Code == "ClInit", :]
        # C = e.calculate_chloride_concentration(params=params_cl)

        # ax2 = e.plot.chloride(C, tmin=tminp, tmax=tmax)
        ax3 = e.plot.chloride_fractions(tmin=tminp, tmax=tmax)

        ax4 = e.plot.gemaal(tmin=tminp, tmax=tmax)
        ax5 = e.plot.gemaal_cumsum(
            tmin=tminp, tmax=tmax, period="month", inlaat=True)

    except Exception as ex:
        print("Failed running {} because: '{}: {}'".format(i, type(ex).__name__, ex),
              file=f)
        raise(ex)

f.close()
plt.show()

# ax7 = e.plot.plot_series(reeksen, mask="Peil")
# ax8 = e.plot.plot_series(reeksen, mask="Gemaal")
