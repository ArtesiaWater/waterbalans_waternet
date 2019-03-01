from hkvfewspy import Pi
from pandas import date_range, Series, DataFrame, Timestamp, Timedelta
import numpy as np

pi = Pi()
pi.setClient(wsdl='http://localhost:8081/FewsPiService/fewspiservice?wsdl')

tmin = Timestamp("1996")
tmax = Timestamp("2016-11-30")  # works
# tmax = Timestamp("2016-12-01")  # fails

moduleInstanceId, locationId, parameterId, _ = "ImportCAW|66004cal|P.meting.dagcal|-999.0".split("|")

query = pi.setQueryParameters(prefill_defaults=True)
query.query["onlyManualEdits"] = False
query.parameterIds([parameterId])
query.locationIds([locationId])
query.startTime(tmin)
query.endTime(tmax)
df = pi.getTimeSeries(query, setFormat='df')

#%% Test pi capabilities
# Lijst met locaties ophalen
locations  = pi.getLocations(setFormat="gdf")

# Lijst met filters (wat dat ook mogen zijn)
filters = pi.getFilters()

# Lijst met parameters
parameters = pi.getParameters()

# Proberen CL tijdreeks op te halen?
# Try a query for CL
query = pi.setQueryParameters(prefill_defaults=True)
query.query["onlyManualEdits"] = False
query.parameterIds(["CL"])
query.locationIds(["WIN001"])

# geeft nu nog een of andere vage error over user permissions of dat er geen timeseries is
df2 = pi.getTimeSeries(query, setFormat='df')  

# Parameters ophalen voor verschillende filters:
parameters = pi.getParameters(filterId=filters.meteo_meetstation_KNMI.id)
parameters = pi.getParameters(filterId=filters.polder_meetpunt_actief.id)  
