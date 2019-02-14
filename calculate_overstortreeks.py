"""
Genereren overstortreeks als volgt:
Iedere tijdstap moet de neerslag worden ingelezen. Deze uurneerslag wordt 
gesommeerd met het verschil tussen berging (in) en POC (uit). Het bergingsbakje 
wordt gevuld, maar wordt ook continu leeggepompt. Als de neerslagintensiteit 
groter is dan de de pompovercapaciteit (POC), loopt de bak over en stort er een 
volume (in mm) over. Dit komt dus in het oppervlaktewater terecht.
De hemelwaterstelsels functioneren ongeveer op dezelfde manier, met als verschil 
dat er geen fysieke pomp is, maar meestal trekt de eerste millimeter de grond in 
(onverhard) of in maaiveld depressies (plassen op straat), en komt niet tot 
afstroming (door verdamping). Dit is in dit model te beschouwen als een bakje met 
een geringe berging en een klein pompje (verdamping).

Voor de overstorten (Combined Sewer Overflows, CSO) gebruiken we nu even de volgende defaults:
    B = 5 mm
    POC = 0.5 mm/h

Voor de hemelwaterstelsels gebruik ik de volgende waarden:
    B = 1 mm
    POC = 0.1 mm/h
    
Dit zijn ruwe aannames die voor iedere locatie verfijnd moeten worden door kalibratie.

"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from pastas.read import KnmiStation


def calculate_cso(prec, Bmax, POCmax, alphasmooth=0.1):
    """Calculate Combined Sewer Overflow timeseries based 
    on hourly precipitation series.
    
    Parameters
    ----------
    prec : pd.Series
        hourly precipitation
    Bmax : float
        maximum storage capacity in meters
    POCmax : float
        maximum pump (over) capacity
    alphasmooth : float, optional
        factor for exponential smoothing (the default is 0.1)
    
    Returns
    -------
    pd.Series
        timeseries of combined sewer overflows (cso)
    
    """

    p_smooth = prec.ewm(alpha=alphasmooth, adjust=False).mean()
    b = p_smooth.copy()
    poc = p_smooth.copy()
    cso = p_smooth.copy()
    vol = p_smooth.copy()

    for i in range(1, len(p_smooth.index)):
        vol.iloc[i] = p_smooth.iloc[i] + b.iloc[i-1] - poc.iloc[i-1]
        b.iloc[i] = np.min([vol.iloc[i], Bmax])
        poc.iloc[i] = np.min([b.iloc[i], POCmax])
        cso.iloc[i] = np.max([vol.iloc[i] - Bmax, 0.0])

    cso_daily = cso.resample("D").sum()
    
    return cso_daily


tmin = pd.datetime(1990, 1, 1, 0, 0)
tmax = pd.datetime.now()

stns = [240, 260]  # Schiphol, De Bilt

knmidata = []
for istn in stns:
    print("Downloading", istn, "...")
    prec = KnmiStation.download(stns=istn, interval="hour", start=tmin, end=tmax, vars="RH")
    knmidata.append(prec)
print("Calculating CSO ...")

Bmax = 5*1e-3 # Maximale berging in het stelsel
POCmax = 0.5*1e-3 # Pompovercapaciteit in m/h

for j in range(2):
    cso_daily = calculate_cso(knmidata[j].data.RH, Bmax, POCmax, alphasmooth=0.1)
    cso_daily.to_pickle(r"G:/My Drive/k/01-Projecten/17026004_WATERNET_Waterbalansen/05pyfiles/_{}_cso_timeseries.pklz".format(stns[j]), compression="zip")
    print("Finished ", j)
# ovst_daily.plot()
# ovst_daily.resample('M').sum().plot('bar', color='C0', width=1.0)
# plt.show()
