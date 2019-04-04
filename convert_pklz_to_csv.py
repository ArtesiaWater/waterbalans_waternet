import os
import pandas as pd
import tqdm
from util import unzip_changed_files


datadir = r"./data/excel_pklz"
unzip_changed_files("./data/excel_pklz.zip", datadir, check_time=True,
                    check_size=True)

files = [i for i in os.listdir(datadir) 
         if i.endswith("_series.pklz") or i.endswith("stoffen.pklz")]

for f in tqdm.tqdm(files, desc="Process series pklz"):
    df = pd.read_pickle(os.path.join(datadir, f), compression="zip")
    df.to_csv(os.path.join(datadir, f.replace(".pklz", ".csv")))
