import os

import pandas as pd
import tqdm


def scrape_excel_to_pklz(exceldir):
    excelfiles = [
        i for i in os.listdir(exceldir) if i.endswith(".xls") or i.endswith(".xlsx")
    ]

    cols1 = "A:F"
    rows1 = [14, 34]
    nrows1 = rows1[1] - rows1[0]
    cols2 = "A:U"
    rows2 = [
        75,
    ]
    sheetname = "uitgangspunten"

    log = open("scraper.log", "w")

    for f in tqdm.tqdm(excelfiles):
        try:
            xls = pd.ExcelFile(os.path.join(exceldir, f))

            # read stofconcentraties table
            table = pd.read_excel(
                xls,
                skiprows=rows1[0],
                header=[0],
                index=[0],
                usecols=cols1,
                sheet_name=sheetname,
                nrows=nrows1,
            )
            # read timeseries water quantity (and three at the end for chloride)
            series = pd.read_excel(
                xls,
                skiprows=rows2[0],
                header=[0],
                index=[0],
                usecols=cols2,
                sheet_name=sheetname,
            )
            # read Chloride and Phosphate etc.
            series_stoffen = pd.read_excel(
                xls,
                skiprows=rows2[0],
                header=[0],
                index=None,
                usecols="W:AH,AJ:AK",
                sheet_name=sheetname,
            )
            # read water balance from REKENHART sheet
            wbalance = pd.read_excel(
                xls,
                skiprows=10,
                header=[0],
                index=None,
                usecols="A,AJ,CH:DB",
                sheet_name="REKENHART",
            )
            wbalance.drop(index=wbalance.iloc[:2].index, inplace=True)
            wbalance.rename(columns={"post": "datetime"}, inplace=True)
            wbalance.set_index("datetime", inplace=True)
            wbalance = wbalance.loc[wbalance.index.dropna()]
            wbalance.drop(
                columns=[
                    icol for icol in wbalance.columns if icol.startswith("Unnamed:")
                ],
                inplace=True,
            )

            # wbalance.drop(columns=[ic for ic in wbalance.columns if str(ic).startswith("0")], inplace=True)

            series.rename(columns={"Unnamed: 0": "datetime"}, inplace=True)
            series.set_index("datetime", inplace=True)
            name = f.split("_")[0]

            table.to_pickle(
                os.path.join(exceldir, name + "_table.pklz"), compression="zip"
            )
            series.to_pickle(
                os.path.join(exceldir, name + "_series.pklz"), compression="zip"
            )
            series_stoffen.to_pickle(
                os.path.join(exceldir, name + "_series_stoffen.pklz"), compression="zip"
            )
            wbalance.to_pickle(
                os.path.join(exceldir, name + "_wbalance.pklz"), compression="zip"
            )

            print(
                f
                + ";"
                + ";".join(
                    [
                        str(j).strip("\n").replace("\n", " ")
                        for j in series.dropna(axis=1, how="all").columns
                    ]
                ),
                file=log,
            )
        except Exception as e:
            print(
                "Error! {0} was not scraped due to {1}:{2}".format(
                    f, e.__class__.__name__, e
                ),
                file=log,
            )
            continue
    log.close()


def convert_pklz_to_csv(datadir):
    files = [
        i
        for i in os.listdir(datadir)
        if i.endswith("_series.pklz") or i.endswith("stoffen.pklz")
    ]

    for f in tqdm.tqdm(files, desc="Process series pklz"):
        df = pd.read_pickle(os.path.join(datadir, f), compression="zip")
        df.to_csv(os.path.join(datadir, f.replace(".pklz", ".csv")))


if __name__ == "__main__":
    exceldir = (
        r"C:\Users\dbrak\Documents\01-Projects\17026004_WATERNET_Waterbalansen"
        r"\03data\balansen"
    )

    scrape_excel_to_pklz(exceldir)
    convert_pklz_to_csv(exceldir)
