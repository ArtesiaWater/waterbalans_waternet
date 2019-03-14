# %%
import warnings
import os
import sys
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shutil
from pandas.core.common import SettingWithCopyWarning
import waterbalans as wb
from util import unzip_changed_files
mpl.interactive(True)

# Set warnings to error
pd.options.mode.chained_assignment = 'raise'
warnings.filterwarnings(action='error', category=FutureWarning)
# warnings.filterwarnings(action='error', message="SettingWithCopyWarning")
# warnings.filterwarnings(action='error', message="warning:")

starttime = pd.datetime.now()

##########################################
# User options

name = "GAF"  # which EAG to run

# overwrite FEWS precipitation and evaporation with series from Excel file
use_excel_PE = True
# True if you want to add missing series from Excel balance, specify exact names below
add_missing_series = True
# whether or not to simulate using the waterlevel series
use_waterlevel_series = False

# add KNMI series for prec/evap to comparison between FEWS/Excel
plot_knmi_comparison = False

tmin = "1996"  # start simulation time for Python
tminp = "1996"  # tmin for in plots, can be different from simulation tmin
tmax = "2016-11-30"  # end simulation time for Python

savefig = False  # save figures to outputdir
do_postproc = False  # create all figures
excel_compare = True  # compare output to Excel

##########################################

# Create directory for saving output
if not os.path.exists("./comparison"):
    os.mkdir("./comparison")
if not os.path.exists(os.path.join("./comparison", name)):
    print("Creating directory for ... {}".format(name))
    outputdir = os.path.join("./comparison", name)
    os.mkdir(outputdir)
else:
    outputdir = os.path.join("./comparison", name)

# copy script to outputdir for reproducibility
try:
    os.remove(os.path.join(outputdir, os.path.basename(__file__)))
except (FileNotFoundError, NameError):
    pass
try:
    shutil.copy(__file__, outputdir)
except NameError:
    __file__ = r"./run_and_compare_gaf.py"
    os.remove(os.path.join(outputdir, os.path.basename(__file__)))
    shutil.copy(__file__, outputdir)

# %%
# Set database url connection
# wb.pi.setClient(wsdl='http://localhost:8081/FewsPiService/fewspiservice?wsdl')

# Get all files
# unzip_changed_files("./data/input_csv.zip", "./data/input_csv",
#                     check_time=True, check_size=True, debug=True)
csvdir = r"./data/input_csv"
files = [i for i in os.listdir(csvdir) if i.endswith(".csv")]
eag_df = pd.DataFrame(data=files, columns=["filenames"])
eag_df["ID"] = eag_df.filenames.apply(lambda s: s.split("_")[2].split(".")[0])
eag_df["type"] = eag_df.filenames.apply(lambda s: s.split("_")[0])
eag_df.drop_duplicates(subset=["ID", "type"], keep="last", inplace=True)
file_df = eag_df.pivot(index="ID", columns="type", values="filenames")
file_df.dropna(how="any", axis=0, inplace=True)
1/0
# Excel directory
unzip_changed_files("./data/excel_pklz.zip", "./data/excel_pklz", check_time=True,
                    check_size=True)
exceldir = r"./data/excel_pklz"

# Get CSV files
fbuckets, fparams, freeks, _ = file_df.loc[name]
buckets = pd.read_csv(os.path.join(csvdir, fbuckets), delimiter=";")
buckets["OppWaarde"] = pd.to_numeric(buckets.OppWaarde)
eag_id = name.split("-")[-1]

# Aanmaken van modelstructuur en de bakjes.
e = wb.create_eag(eag_id, name, buckets,
                  use_waterlevel_series=use_waterlevel_series)

# Lees de tijdreeksen in
reeksen = pd.read_csv(os.path.join(csvdir, freeks), delimiter=";",
                      decimal=",")

# add default series
e.add_series(reeksen, tmin=tmin, tmax=tmax)

# read missing series 'reeks' and add as inflow to EAG
excelseries = pd.read_pickle(os.path.join(
    exceldir, "{}_series.pklz".format(name)), compression="zip")
valid_index = excelseries.index.dropna()
excelseries = excelseries.loc[valid_index]

# Sometimes one of the columns in excel series is not float. Convert those columns manually
for icol in excelseries:
    if excelseries[icol].dtype == "O":
        excelseries[icol] = pd.to_numeric(excelseries[icol], errors="coerce")

tmin = pd.Timestamp(tmin)
# pick earliest tmax to avoid FutureWarnings about KeyErrors
tmax = np.min([pd.Timestamp(tmax), excelseries.index[-1]])

if add_missing_series:
    column_names = {}
    columns = ["neerslag", "verdamping", "peil",
               "Gemaal1", "Gemaal2", "Gemaal3", "Gemaal4",
               "Inlaat voor calibratie", "gemengd gerioleerd stelsel",
               "Inlaat1", "Inlaat2", "Inlaat3", "Inlaat4",
               "Uitlaat1", "Uitlaat2", "Uitlaat3", "Uitlaat4"]
    # Gemaal
    colmask = [True if icol.startswith(
        "Gemaal") else False for icol in columns]
    gemaal_series = excelseries.loc[:, colmask]
    gemaal_series = gemaal_series.dropna(how="all", axis=1)
    gemaal = gemaal_series.sum(axis=1)
    e.add_timeseries(gemaal, name="Gemaal", tmin=tmin, tmax=tmax,
                     fillna=True, method=0.0)

    # Inlaat
    colmask = [True if icol.startswith(
        "Inlaat") else False for icol in columns]
    inlaat_series = excelseries.loc[:, colmask]
    inlaat_series = inlaat_series.drop("Inlaat\nvoor calibratie", axis=1)
    # inlaat_series = inlaat_series.dropna(how="all", axis=1)
    for jcol in range(inlaat_series.shape[1]):
        if inlaat_series.iloc[:, jcol].dropna().empty:
            continue
        if not "Inlaat{}".format(jcol+1) in column_names.keys():
            column_names.update(
                {"Inlaat{}".format(jcol+1): inlaat_series.columns[jcol]})
        e.add_timeseries(inlaat_series.iloc[:, jcol], name="Inlaat{}".format(jcol+1),
                         tmin=tmin, tmax=tmax, fillna=True, method=0.0)

    # Uitlaat
    colmask = [True if icol.startswith(
        "Uitlaat") else False for icol in columns]
    uitlaat_series = excelseries.loc[:, colmask]
    # uitlaat_series = uitlaat_series.dropna(how="all", axis=1)
    for jcol in range(uitlaat_series.shape[1]):
        if uitlaat_series.iloc[:, jcol].dropna().empty:
            continue
        if not "Uitlaat{}".format(jcol+1) in column_names.keys():
            column_names.update(
                {"Uitlaat{}".format(jcol+1): uitlaat_series.columns[jcol]})
        e.add_timeseries(-1*uitlaat_series.iloc[:, jcol], name="Uitlaat{}".format(jcol+1),
                         tmin=tmin, tmax=tmax, fillna=True, method=0.0)

    # Peil
    colmask = [True if icol.lower().startswith(
        "peil") else False for icol in columns]
    peil = excelseries.loc[:, colmask]
    e.add_timeseries(peil, name="Peil", tmin=tmin, tmax=tmax,
                     fillna=True, method="ffill")

# Overwrite FEWS Neerslag/Verdamping with Excel series
if use_excel_PE:
    if e.series.index[0] in excelseries.index and e.series.index[-1] in excelseries.index:
        e.series.loc[:, "Neerslag"] = excelseries.loc[e.series.index,
                                                      excelseries.columns[0]].fillna(0.0) * 1e-3
        e.series.loc[:, "Verdamping"] = excelseries.loc[e.series.index,
                                                        excelseries.columns[1]].fillna(0.0) * 1e-3
    else:
        e.series.loc[e.series.loc[tmin:tmax].index, "Neerslag"] = excelseries.loc[e.series.loc[tmin:tmax].index,
                                                                                  excelseries.columns[0]].fillna(0.0) * 1e-3
        e.series.loc[e.series.loc[tmin:tmax].index, "Verdamping"] = excelseries.loc[e.series.loc[tmin:tmax].index,
                                                                                    excelseries.columns[1]].fillna(0.0) * 1e-3

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
    except IndexError:
        # No Verdamping in reeksen.csv probably
        if "Schiphol" in excelseries.columns[1]:
            enam = "66002"
        else:
            enam = "66003"
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

    # Add q_cso series to EAG, will only be used for MengRiool bucket
    colmask = [True if icol.startswith(
        "gemengd gerioleerd") else False for icol in columns]
    csoseries = excelseries.loc[:, colmask] / 100**2  # series is in m3/d/ha
    e.add_timeseries(csoseries, name="q_cso", tmin=tmin,
                     tmax=tmax, fillna=True, method=0.0)

    # Set MengRiool bucket to use eag_series and not pre-calculated one
    b = e.get_buckets(buckettype="MengRiool")
    b[0].use_eag_cso_series = True

# Simulate
e.simulate(params=params, tmin=tmin, tmax=tmax)

b = e.water.validate()
print(e.name, "Water balance closed: ", b)

postruntime = pd.datetime.now()
print("Time elapsed simulate: {0:.1f} s".format(
    (postruntime - starttime).total_seconds()))

if do_postproc:

    # Plot balances
    ax = e.plot.aggregated(freq="M", tmin=tminp, tmax=tmax)
    if savefig:
        ax.figure.savefig(os.path.join(outputdir, "bar_aggregate_fluxes.png"), dpi=150,
                          bbox_inches="tight")

    ax = e.plot.aggregated(freq="M", tmin=tminp, tmax=tmax, add_gemaal=True)
    if savefig:
        ax.figure.savefig(os.path.join(outputdir, "bar_aggregate_fluxes-wgemaal.png"), dpi=150,
                          bbox_inches="tight")

    # Plot water level
    ax = e.plot.water_level(label_obs=True)
    if savefig:
        ax.figure.savefig(os.path.join(outputdir, "line_waterlevel.png"), dpi=150,
                          bbox_inches="tight")

    # Plot gemaal and calculated out/inflow
    ax = e.plot.gemaal(tmin=tminp, tmax=tmax)
    if savefig:
        ax.figure.savefig(os.path.join(outputdir, "line_outflow-wgemaal.png"), dpi=150,
                          bbox_inches="tight")

    ax = e.plot.gemaal_cumsum(tmin=tminp, tmax=tmax,
                              period="month", inlaat=True)
    if savefig:
        ax.figure.savefig(os.path.join(outputdir, "linecumsum_outflow-wgemaal-winlaat.png"), dpi=150,
                          bbox_inches="tight")

    # Calculate and plot the chloride concentration
    params_cl = params.loc[params.Code == "ClInit", :]
    C = e.calculate_chloride_concentration(params=params_cl)

    # Plot Chloride
    ax = e.plot.chloride(C, tmin=tminp, tmax=tmax)
    if savefig:
        ax.figure.savefig(os.path.join(outputdir, "line_chlorideconc.png"), dpi=150,
                          bbox_inches="tight")
    ax = e.plot.chloride_fractions(tmin=tmin, tmax=tmax, chloride_conc=C)
    if savefig:
        ax.figure.savefig(os.path.join(outputdir, "linestack_chloride-fractions.png"), dpi=150,
                          bbox_inches="tight")

if plot_knmi_comparison:
    # Neerslag + Verdamping
    fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(16, 7), dpi=150, sharex=True)
    ax0.plot(excelseries.index, excelseries.iloc[:, 0], label="neerslag Excel")
    ax0.plot(e.series.Neerslag.index, e.series.Neerslag *
             1e3, label="neerslag FEWS")

    ax1.plot(excelseries.index,
             excelseries.iloc[:, 1], label="verdamping Excel")
    ax1.plot(e.series.Verdamping.index, e.series.Verdamping *
             1e3, label="verdamping FEWS")

    import pastas as ps
    # prec
    prec = ps.read.KnmiStation.download(start=tmin, end=tmax, stns=563,
                                        vars='RD', interval='daily')
    ax0.plot(prec.data.index.floor(freq="D") - pd.Timedelta(days=1), prec.data.RD*1e3,
             label="neerslag KNMI", ls="dashed")
    # evap
    evap = ps.read.KnmiStation.download(start=tmin, end=tmax, stns=240,
                                        vars='EV24', interval='daily')
    ax1.plot(evap.data.index.floor(freq="D") - pd.Timedelta(days=1), evap.data.EV24*1e3,
             label="verdamping KNMI", ls="dashed")

    for iax in [ax0, ax1]:
        iax.grid(b=True)
        iax.legend(loc="best")

    if savefig:
        fig.savefig(os.path.join(outputdir, "line_evap-prec-comparison.png"), dpi=150,
                    bbox_inches="tight")

postproctime = pd.datetime.now()
if do_postproc:
    print("Time elapsed postproc: {0:.1f} seconds".format(
        (postproctime - postruntime).total_seconds()))

if excel_compare:
    # %% Compare to Excel
    # Read Excel Balance Data (see scrape_excelbalansen.py for details)
    excelbalance = pd.read_pickle(os.path.join(exceldir, "{}_wbalance.pklz".format(e.name)),
                                  compression="zip")
    for icol in excelbalance.columns:
        excelbalance.loc[:, icol] = pd.to_numeric(
            excelbalance[icol], errors="coerce")

    # Waterbalance comparison
    fig = e.plot.compare_fluxes_to_excel_balance(excelbalance, showdiff=True)
    if savefig:
        fig.savefig(os.path.join(outputdir, "comparison_fluxes_excel_python.png"), dpi=150,
                    bbox_inches="tight")

    ax = e.plot.compare_waterlevel_to_excel(excelbalance)
    if savefig:
        ax.figure.savefig(os.path.join(outputdir, "line_waterlevel_comparison_excel.png"), dpi=150,
                          bbox_inches="tight")

    print("Time elapsed excel comparison: {0:.1f} seconds".format(
        (pd.datetime.now() - postruntime).total_seconds()))

if savefig:
    plt.close("all")
