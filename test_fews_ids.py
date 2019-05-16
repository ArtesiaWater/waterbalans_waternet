import pandas as pd
import hkvfewspy as fewspy

excelf = (r"G:\My Drive\k\01projekt\17026004_WATERNET_Waterbalansen"
          r"\03data\Parameters_uit_excel\oppervlakken en parameters_v7_dbrakenhoff.xlsm")

fewscodes = pd.read_excel(excelf, sheet_name="FEWS", index_col=[0], header=[0])
fewscodes.drop(columns=["Balans"], inplace=True)

pi = fewspy.Pi()
pi.setClient(
    wsdl='http://localhost:8080/FewsWebServices/fewspiservice?wsdl')  # 2017.02

tmin = pd.Timestamp("1996")
# tmax = pd.Timestamp("2016-11-30")  # works
tmax = pd.Timestamp("2019-01-01")  # fails

fewsids = fewscodes.melt().dropna(how="any")["value"].unique()

result = pd.DataFrame(index=fewsids, columns=["Succeed"])

f = open("fews_test_2019.log", "w")
count = 0

for fews_waarde_alfa in fewsids:
    if "|" not in fews_waarde_alfa:
        print("Skipped (no pipes)!", file=f)
        continue
    elif fews_waarde_alfa.count("|") > 3:
        print("Multiple FEWS series found...", file=f)
        fews_waardes = fews_waarde_alfa.split("||")
        for fews_waarde_alfa in fews_waardes:
            print(fews_waarde_alfa + "; ", end="", file=f)
            filterId, moduleInstanceId, locationId, parameterId = fews_waarde_alfa.split(
                "|")
            query = pi.setQueryParameters(prefill_defaults=True)
            query.query["onlyManualEdits"] = False
            query.moduleInstanceIds([moduleInstanceId])
            query.parameterIds([parameterId])
            query.locationIds([locationId])
            # query.filterId(filterId)
            query.useDisplayUnits(False)
            query.startTime(tmin)
            query.endTime(tmax)
            query.version("1.24")
            count += 1
            try:
                df = pi.getTimeSeries(query, setFormat='df')
                result.loc[fews_waarde_alfa, "Succeed"] = 1
                print("Success", file=f)
            except Exception as e:
                print("Error {}".format(e), file=f)
                result.loc[fews_waarde_alfa, "Succeed"] = 0
    else:
        print(fews_waarde_alfa + "; ", end="", file=f)
        filterId, moduleInstanceId, locationId, parameterId = fews_waarde_alfa.split(
            "|")
        query = pi.setQueryParameters(prefill_defaults=True)
        query.query["onlyManualEdits"] = False
        query.moduleInstanceIds([moduleInstanceId])
        query.parameterIds([parameterId])
        query.locationIds([locationId])
        # query.filterId(filterId)
        query.startTime(tmin)
        query.endTime(tmax)
        query.version("1.24")
        count += 1
        try:
            df = pi.getTimeSeries(query, setFormat='df')
            result.loc[fews_waarde_alfa, "Succeed"] = 1
            print("Success", file=f)
        except Exception as e:
            print("Error {}".format(e), file=f)
            result.loc[fews_waarde_alfa, "Succeed"] = 0

print("--------------------", file=f)
print(
    "Total_successes; {0} / {1}".format(result.loc[:, "Succeed"].sum(),
                                        count), file=f)
f.close()

# # fews_waarde_alfa = 'meteo_meetstation_KNMI|ImportCAW|66004cal|P.meting.dagcal'
# try:
#     fews_waarde_alfa = 'meteo_meetstation_KNMI|ImportCAW|66004cal|P.meting.dagcal'
#     filterId, moduleInstanceId, locationId, parameterId = fews_waarde_alfa.split(
#         "|")
#     query = pi.setQueryParameters(prefill_defaults=True)
#     # query.query["onlyManualEdits"] = False
#     query.moduleInstanceIds([moduleInstanceId])
#     query.parameterIds([parameterId])
#     query.locationIds([locationId])
#     # query.filterId(filterId)
#     query.startTime(tmin)
#     query.endTime(tmax)
#     query.version("1.24")
#     df = pi.getTimeSeries(query, setFormat='df')
# except Exception as e:
#     print(e)
