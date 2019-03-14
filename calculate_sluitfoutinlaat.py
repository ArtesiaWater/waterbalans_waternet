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
mpl.interactive(True)

# %%
# Set database url connection
# wb.pi.setClient(wsdl='http://localhost:8081/FewsPiService/fewspiservice?wsdl')

# %%
# Get all files
csvdir = r"C:/Users/dbrak/Documents/01-Projects/17026004_WATERNET_Waterbalansen/03data/DataExport_frompython2"
files = [i for i in os.listdir(csvdir) if i.endswith(".csv")]
eag_df = pd.DataFrame(data=files, columns=["filenames"])
eag_df["ID"] = eag_df.filenames.apply(lambda s: s.split("_")[2].split(".")[0])
eag_df["type"] = eag_df.filenames.apply(lambda s: s.split("_")[0])
eag_df.drop_duplicates(subset=["ID", "type"], keep="first", inplace=True)
file_df = eag_df.pivot(index="ID", columns="type", values="filenames")
file_df.dropna(how="any", axis=0, inplace=True)

# %%
eag_list = []
# Loop over files
for i, (fbuckets, fparams, freeks) in file_df.iterrows():
    # if not i in successful_eags:
    if not i == "3260-EAG-1":  # "2501-EAG-2":
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
        e.add_series(reeksen)

        # Simuleer de waterbalans
        params = pd.read_csv(os.path.join(csvdir, fparams), delimiter=";",
                             decimal=",")
        params.rename(columns={"ParamCode": "Code"}, inplace=True)
        params["Waarde"] = pd.to_numeric(params.Waarde)

        # Simulate
        e.simulate(params=params, tmin="2000", tmax="2015-12-31")

        # plot result
        e.plot.aggregated(tmin="2010", tmax="2015")

        # save eag in list
        eag_list.append(e)

        # Calculate and plot the fluxes as a bar plot
        fluxes = e.aggregate_fluxes()

        diff = e.series["Gemaal"] - -1*fluxes["berekende uitlaat"]
        diff.loc[diff <= 0.0] = 0.0
        inlaat_monthly = diff.resample("M").mean()
        inlaat_monthly_sum = diff.resample("M").sum()

        # Get difference Gemaal and berekende uitlaat
        fig, ax0 = plt.subplots(1, 1)
        gemaal = e.series.Gemaal.groupby(by=[e.series.Gemaal.index.year,
                                             e.series.Gemaal.index.month]).cumsum()
        grouper = [fluxes.index.year, fluxes.index.month]
        calculated_out = fluxes["berekende uitlaat"].groupby(
            by=grouper).cumsum()
        ax0.fill_between(gemaal.index, 0.0, -gemaal,
                         label="Gemaal", color="C1")
        ax0.plot(calculated_out.index, calculated_out,
                 "b-", label="Berekende uitlaat")
        ax0.legend(loc="best")

        com = fluxes["berekende uitlaat"].resample("M").sum()
        gm = e.series.Gemaal.resample("M").sum()

        gm_in = -1*gm - inlaat_monthly_sum
        ax0.plot(gm_in.index, gm_in, marker="o", ls="")

        fig, ax1 = plt.subplots(1, 1)
        # diff.dropna(inplace=True)

        ax1.plot(diff.index, diff)

        inlaat_monthly = diff.resample("M").mean()

        plt.figure()
        inlaat_monthly.plot(kind="bar", width=1.0, color="C0")
        inlaat_monthly.resample("D").bfill().plot(color="k", lw=3, ax=ax1)

        inlaat_sluitfout = inlaat_monthly.resample("D").bfill()

        e.add_timeseries(inlaat_sluitfout, name="Inlaat Sluitfout")
        e.simulate(params=params, tmin="2000", tmax="2015")

        e.plot.aggregated(tmin="2010", tmax="2015")

    except Exception as ex:
        print("Failed running {} because: '{}: {}'".format(
            i, type(ex).__name__, ex))

plt.show()
