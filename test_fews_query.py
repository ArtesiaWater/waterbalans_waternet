from hkvfewspy import Pi
from pandas import date_range, Series, DataFrame, Timestamp, Timedelta
import numpy as np

pi = Pi()
# pi.setClient(wsdl='http://localhost:8081/FewsPiService/fewspiservice?wsdl')  # 2017.01
pi.setClient(wsdl='http://localhost:8080/FewsWebServices/fewspiservice?wsdl')  # 2017.02


# Test ophalen van neerslag reeks.
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
query.version("1.24")
df = pi.getTimeSeries(query, setFormat='df')

# Proberen CL tijdreeks op te halen? Try a query for CL:
tmin = Timestamp("2000-01-01 00:00")
tmax = Timestamp("2017-01-01 00:00")
query = pi.setQueryParameters(prefill_defaults=True)
query.query["onlyManualEdits"] = False
query.parameterIds(["CL"])
query.locationIds(["WIN001"])
query.startTime(tmin)
query.endTime(tmax)
query.version("1.24")
query.forecastSearchCount(1)
query.useDisplayUnits(False)
query.showThresholds(True)
query.omitMissing(True)

# Dit werkt nu!
df2 = pi.getTimeSeries(query, setFormat='df')  

#%% Test pi capabilities

# Lijst met locaties ophalen
locations  = pi.getLocations(setFormat="gdf")

# Lijst met parameters
parameters = pi.getParameters()

# Lijst met filters
filters = pi.getFilters()

# Parameters ophalen voor verschillende filters:
parameters = pi.getParameters(filterId=filters.PI_service_intern.id)
parameters = pi.getParameters(filterId=filters.polder_meetpunt_actief.id)
