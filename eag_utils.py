#%%
"""
Dit script bevat de automatische simulatie van waterbalansen op
EAG-niveau voor alle EAGs. De volgende drie invoerbestanden worden 
per EAG gebruikt:

- Modelstructuur (opp)
- Tijdreeksen
- Parameters

"""
#%%
import os
import sys
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pandas.core.common import SettingWithCopyWarning
import waterbalans as wb
pd.options.mode.chained_assignment = 'raise'

import warnings
warnings.filterwarnings(action='error', category=FutureWarning)


def run_eag(fbuckets, fparams, freeks, csvdir=None, tmin="2000", tmax="2018"):

    if csvdir is None:
        csvdir = ""

    # Set database url connection
    wb.pi.setClient(wsdl='http://localhost:8081/FewsPiService/fewspiservice?wsdl')

    buckets = pd.read_csv(os.path.join(csvdir, fbuckets), delimiter=";",
                                       decimal=",")
    buckets["OppWaarde"] = pd.to_numeric(buckets.OppWaarde)
    name = os.path.basename(fbuckets).split("_")[2].split(".")[0]
    eag_id = name.split("-")[-1]
    
    # Aanmaken van modelstructuur en de bakjes.
    e = wb.create_eag(eag_id, name, buckets)

    # Lees de tijdreeksen in
    reeksen = pd.read_csv(os.path.join(csvdir, freeks), delimiter=";",
                          decimal=",")
    e.add_series(reeksen)

    # Simuleer de waterbalans
    params = pd.read_csv(os.path.join(csvdir, fparams), delimiter=";",
                            decimal=",")
    params.rename(columns={"ParamCode": "Code"}, inplace=True)
    params["Waarde"] = pd.to_numeric(params.Waarde)
    
    # Add missing series manually for MengRiool
    if "MengRiool" in buckets.BakjePyCode.values:
        try:
            enam = reeksen.loc[reeksen.ClusterType == "Verdamping", "WaardeAlfa"].iloc[0]
            enam = enam.split("|")[1]
            if "66002" in enam:
                stn = 240  # Schiphol
            elif "66003" in enam:
                stn = 260  # De Bilt
            
            BakjeID_mengriool = buckets.loc[buckets.BakjePyCode == "MengRiool", "BakjeID"].iloc[0]
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
            print("Failed running {} because: '{}: {}'".format(name, type(ex).__name__, 
                                                               "Verdamping missing"))
            # raise(ex)

    # Simulate
    e.simulate(params=params, tmin=tmin, tmax=tmax)

    return e


def eag_modelstructure(fbuckets, csvdir=None):
    if csvdir is None:
        csvdir = ""
    buckets = pd.read_csv(os.path.join(csvdir, fbuckets), delimiter=";",
                                       decimal=",")
    structure = buckets.BakjePyCode.value_counts()
    structure.name = buckets.EAGCode.iloc[0]
    return structure

# Get all files
csvdir = r"C:/Users\dbrak/Documents/01-Projects/17026004_WATERNET_Waterbalansen/03data/DataExport_frompython2"
files = os.listdir(csvdir)
eag_df = pd.DataFrame(data=files, columns=["filenames"])
eag_df["ID"] = eag_df.filenames.apply(lambda s: s.split("_")[2].split(".")[0])
eag_df["type"] = eag_df.filenames.apply(lambda s: s.split("_")[0])
eag_df.drop_duplicates(subset=["ID", "type"], keep="first", inplace=True)
file_df = eag_df.pivot(index="ID", columns="type", values="filenames")
file_df.dropna(how="any", axis=0, inplace=True)

summary = pd.DataFrame(index=file_df.index, columns=["Water", "Verhard", "Onverhard", 
                                                     "Drain", "MengRiool"])

for fb in file_df.opp:
    structure = eag_modelstructure(fb, csvdir=csvdir)
    summary.loc[structure.name] = structure
