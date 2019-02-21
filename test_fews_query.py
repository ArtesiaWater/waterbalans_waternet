from hkvfewspy import Pi
from pandas import date_range, Series, DataFrame, Timestamp, Timedelta
import numpy as np

pi = Pi()
pi.setClient(wsdl='http://localhost:8081/FewsPiService/fewspiservice?wsdl')

tmin = Timestamp("1996")
tmax = Timestamp("2016-11-30")

moduleInstanceId, locationId, parameterId, _ = "ImportCAW|66004cal|P.meting.dagcal|-999.0".split("|")

query = pi.setQueryParameters(prefill_defaults=True)
query.query["onlyManualEdits"] = False
query.parameterIds([parameterId])
query.moduleInstanceIds([moduleInstanceId])
query.locationIds([locationId])
query.startTime(tmin)
query.endTime(tmax)
query.clientTimeZone('Europe/Amsterdam')

df = pi.getTimeSeries(query, setFormat='df')
