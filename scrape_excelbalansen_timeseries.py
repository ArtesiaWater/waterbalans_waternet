import os
import pandas as pd
import tqdm

# time start
t0 = pd.datetime.now()

exceldir = r"C:\Users\dbrak\Documents\01-Projects\17026004_WATERNET_Waterbalansen\03data\balansen"
excelfiles = [i for i in os.listdir(
    exceldir) if i.endswith(".xls") or i.endswith(".xlsx")]

cols1 = "A:F"
rows1 = [14, 34]
nrows1 = rows1[1] - rows1[0]
cols2 = "A:R"
rows2 = [75, ]
sheetname = "uitgangspunten"

log = open("scraper.log", "w")

for f in tqdm.tqdm(excelfiles):
    # for f in excelfiles:
    # if not "EAG" in f:
    # if not "GAF" in f:
    #     continue

    # # temporary mask
    # if not f.startswith("3200-EAG-2"):
    #     continue
    try:
        # print("Processing {} ...".format(f))
        xls = pd.ExcelFile(os.path.join(exceldir, f))
        table = pd.read_excel(xls, skiprows=rows1[0], header=[0], index=[0],
                              usecols=cols1, sheet_name=sheetname, nrows=nrows1)
        series = pd.read_excel(xls, skiprows=rows2[0], header=[0], index=[0],
                               usecols=cols2, sheet_name=sheetname)

        wbalance = pd.read_excel(xls, skiprows=10, header=[0],
                                 index=None, usecols="A,AJ,CH:DB", sheet_name="REKENHART")
        wbalance.drop(index=wbalance.iloc[:2].index, inplace=True)
        wbalance.rename(columns={'post': "datetime"}, inplace=True)
        wbalance.set_index("datetime", inplace=True)
        wbalance = wbalance.loc[wbalance.index.dropna()]
        wbalance.drop(columns=[icol for icol in wbalance.columns if icol.startswith(
            "Unnamed:")], inplace=True)

        # wbalance.drop(columns=[ic for ic in wbalance.columns if str(ic).startswith("0")], inplace=True)

        series.rename(columns={'Unnamed: 0': "datetime"}, inplace=True)
        series.set_index("datetime", inplace=True)
        name = f.split("_")[0]

        table.to_pickle(os.path.join(exceldir, name +
                                     "_table.pklz"), compression="zip")
        series.to_pickle(os.path.join(exceldir, name +
                                      "_series.pklz"), compression="zip")
        wbalance.to_pickle(os.path.join(
            exceldir, name + "_wbalance.pklz"), compression="zip")

        print(f + ";" + ";".join([str(j).strip("\n").replace("\n", " ")
                                  for j in series.dropna(axis=1, how="all").columns]), file=log)
    except Exception as e:
        print("Error! {0} was not scraped due to {1}:{2}".format(
            f, e.__class__.__name__, e), file=log)
        continue

log.close()
print("Time elapsed: {0:.2f} minutes".format(
    (pd.datetime.now() - t0).total_seconds()/60.))
