import platform
assert platform.architecture()[0] == "32bit", "Error: script requires 32bit Python!"

import pyodbc
import pandas as pd
import os

outdir = (r"C:\Users\dbrak\Documents\01-Projects\17026004_WATERNET_Waterbalansen"
          r"\03data\DataExport_frompython2")

# %% Set up database connection
connStr = (r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
           r"DBQ=c:\Users\dbrak\Documents\01-Projects\17026004_WATERNET_Waterbalansen"
           r"\03data\balansen_20190314\DB\Waterstoffenbalans2.accdb;")
cnxn = pyodbc.connect(connStr)
cur = cnxn.cursor()

# %% Get EAG codes
#watersysteemid 1312
WatersysteemTabel = cur.execute("SELECT * FROM Watersystemen WHERE code not like '%?%' ORDER By ID")
Watersysteem_list = WatersysteemTabel.fetchall()

# %% Get opp files
for iWatersysteem in Watersysteem_list:

    GETOPPEXCLWATERSQL = ("SELECT ws.Id as EAGID, ws.code as EAGCode,1000000 * ws.id + b.id as BakjeID,b.omschrijving as BakjeOmschrijving,bt.pythoncode as BakjePyCode,bpw.waarde as OppWaarde "
                            "From ((((Bakken b "
                            "Inner Join BakTypen bt on bt.id = b.baktypeid) "
                            "Inner Join Deelgebieden dg on dg.id = b.deelgebiedid) "
                            "Inner Join Watersystemen ws on ws.id = dg.watersysteemid) "
                            "Inner Join BakParamWaarden bpw on bpw.bakId = b.Id) "
                            "Where bpw.bakparamid = 13 "
                            "and bpw.waarde > 0 "
                            "and bt.code <> 'Water' "
                            "and ws.id = {}".format(iWatersysteem[0]) + 
                            " ORDER BY WS.Code")
                
    df0 = pd.read_sql(GETOPPEXCLWATERSQL, cnxn)

    GETOPPWATERSQL = ("SELECT dg.watersysteemId as EAGID, ws.code as EAGCode,1000000 * dg.watersysteemId as BakjeID, 'Water' as BakjeOmschrijving, 'Water' as BakjePyCode, SUM(bpw.waarde) as OppWaarde "
                        "From ((((Bakken b "
                        "Inner Join BakTypen bt on bt.id = b.baktypeid) "
                        "Inner Join Deelgebieden dg on dg.id = b.deelgebiedid) "
                        "Inner Join Watersystemen ws on ws.id = dg.watersysteemid) "
                        "Inner Join BakParamWaarden bpw on bpw.bakId = b.Id) "
                        "Where bpw.bakparamid = 13 "
                        "and bpw.waarde > 0 "
                        "and bt.code = 'Water' "
                        "and ws.id = {}".format(iWatersysteem[0]) + 
                        " GROUP BY dg.watersysteemId, ws.code "
                        "ORDER By WS.Code")

                    
    df1 = pd.read_sql(GETOPPWATERSQL, cnxn)

    df = pd.concat([df0, df1], axis=0)

    if not df.empty:
        df.to_csv(os.path.join(outdir, "opp_{0}_{1}.csv".format(iWatersysteem[0], iWatersysteem[2])), sep=";")

for iWatersysteem in Watersysteem_list:
    GETBAKPARAMSQL = ("SELECT ws.Id as EAGID, ws.code as EAGCode,1000000 * ws.id + b.id as BakjeID, iif(bp.Code like '%Onder', 2, 1) as Laagvolgorde, bp.PythonCode as ParamCode, bpw.waarde as Waarde "
                    "From (((((Bakken b "
                    "Inner Join BakTypen bt on bt.id = b.baktypeid) "
                    "Inner Join Deelgebieden dg on dg.id = b.deelgebiedid) "
                    "Inner Join Watersystemen ws on ws.id = dg.watersysteemid) "
                    "Inner Join BakParamWaarden bpw on bpw.bakId = b.Id) "
                    "Inner join BakParams bp on bp.id = bpw.bakparamid) "
                    "Where bpw.bakparamid <> 13 "
                    "and bt.code <> 'Water' "
                    "and bp.pythoncode <> '' "
                    "and bp.pythoncode <> 'QKwel' "
                    "and b.id  in (select b.id from bakken b inner join Bakparamwaarden bpw on bpw.bakid = b.id where bpw.bakparamid = 13 and bpw.waarde > 0) "
                    "and ws.id = {}".format(iWatersysteem[0]) + 
                    " ORDER BY WS.Code ")
    df0 = pd.read_sql(GETBAKPARAMSQL, cnxn)
    
    GETWATERSYSTEEMPARAMSQL = ("SELECT distinct ws.Id as EAGID, ws.code as EAGCode,1000000 * ws.id as BakjeID,'1' as Laagvolgorde, wsp.PythonCode as ParamCode, wspw.waarde as Waarde "
                    "From (((((Bakken b "
                    "Inner Join BakTypen bt on bt.id = b.baktypeid) "
                    "Inner Join Deelgebieden dg on dg.id = b.deelgebiedid) "
                    "Inner Join Watersystemen ws on ws.id = dg.watersysteemid) "
                    "Inner Join WatersysteemParamWaarden wspw on wspw.watersysteemId = ws.Id) "
                    "Inner join WatersysteemParams wsp on wsp.id = wspw.watersysteemparamid) "
                    "Where b.id  in (select b.id from bakken b inner join Bakparamwaarden bpw on bpw.bakid = b.id where bpw.bakparamid = 13 and bpw.waarde > 0) "
                    "and wsp.pythoncode <> '' "
                    "and bt.code = 'Water' "
                    "and wsp.pythoncode not like 'hTargetM%'"
                    "and ws.id = {}".format(iWatersysteem[0]) + 
                    " ORDER BY WS.Code ")

    df1 = pd.read_sql(GETWATERSYSTEEMPARAMSQL, cnxn)

    df = pd.concat([df0, df1], axis=0)

    if not df.empty:
        df.to_csv(os.path.join(outdir, "param_{0}_{1}.csv".format(iWatersysteem[0], iWatersysteem[2])), sep=";")


for iWatersysteem in Watersysteem_list:
#    GETREEKSDEBIETSQL = ("SELECT distinct ws.Id as EAGID, "
#                    "ws.code as EAGCode, "
#                    "'-9999'  as BakjeID, "
#                    "'-9999' as Laagvolgorde, "
#                    "mpt.code as ClusterType, "
#                    "'ValueSeries' as ParamType, "
#                    "mppw.Waarde as Waarde, "
#                    "'' as WaardeAlfa, "
#                    "iif (mpp.Code like '%Zomer', '01-04', '01-10') as StartDag "
#                    "From (((((((Bakken b "
#                    "Inner Join BakTypen bt on bt.id = b.baktypeid) "
#                    "Inner Join Deelgebieden dg on dg.id = b.deelgebiedid) "
#                    "Inner Join Watersystemen ws on ws.id = dg.watersysteemid) "
#                    "Inner Join Meetpunten mp on mp.WatersysteemId = ws.id) "
#                    "Inner Join MeetpuntTypen mpt on mpt.Id = mp.meetpunttypeid) "
#                    "Inner Join MeetpuntParamWaarden mppw on mppw.MeetpuntId = mp.Id) "
#                    "Inner join MeetpuntParams mpp on mpp.id = mppw.meetpuntparamid) "
#                    "Where b.id  in (select b.id from bakken b inner join Bakparamwaarden bpw on bpw.bakid = b.id where bpw.bakparamid = 13 and bpw.waarde > 0) "
#                    "and bt.code = 'Water' "
#                    "and mppw.waarde > 0 "
#                    "and ws.id = {}".format(iWatersysteem[0]) + 
#                    " ORDER BY WS.Code ")
#    df0 = pd.read_sql(GETREEKSDEBIETSQL, cnxn)

    GETREEKSCHLORIDESQL = ("SELECT distinct ws.Id as EAGID, "
                   "ws.code as EAGCode, "
                    "1000000 * ws.id as BakjeID, "
                    "'-9999' as Laagvolgorde, "
                    "mpp.Pythoncode + mpt.Pythoncode  as ClusterType, "
                    "'-9999' as ParamType, "
                    "mppw.Waarde as Waarde, "
                    "'' as WaardeAlfa, "
                    "'' as StartDag "
                    "From (((((((Bakken b "
                    "Inner Join BakTypen bt on bt.id = b.baktypeid) "
                    "Inner Join Deelgebieden dg on dg.id = b.deelgebiedid) "
                    "Inner Join Watersystemen ws on ws.id = dg.watersysteemid) "
                    "Inner join Meetpunten mp on mp.watersysteemid = ws.id) "
                    "Inner Join MeetpuntParamWaarden mppw on mppw.meetpuntId = mp.Id) "
                    "Inner join MeetpuntParams mpp on mpp.id = mppw.meetpuntparamid) "
                    "Inner Join MeetpuntTypen mpt on mpt.id = mp.meetpunttypeid) "
                    "Where b.id  in (select b.id from bakken b inner join Bakparamwaarden bpw on bpw.bakid = b.id where bpw.bakparamid = 13 and bpw.waarde > 0) "
                    "and bt.code = 'Water' "
                    "and mpp.code = 'Cl' "
                    "and mpt.code not in ('Inlaat', 'Uitlaat', 'InlaatPeilbeheer') "
                    "and mpt.pythoncode is not null "
                    "and ws.id = {}".format(iWatersysteem[0]) + 
                    " ORDER BY WS.Code" )
    df1 = pd.read_sql(GETREEKSCHLORIDESQL, cnxn)


    GETREEKSEXCLWATERSQL = ("SELECT  " 
                    "t.EAGID as EAGID, " 
                    "t.EAGCode As EAGCode, " 
                    "t.BakjeID as BakjeID, " 
                    "t.Laagvolgorde as Laagvolgorde, " 
                    "t.ClusterType as ClusterType, " 
                    "IIF(t.Count > 1, 'Constant', 'ValueSeries') as ParamType, " 
                    "t.Waarde as Waarde, " 
                    "'' as WaardeAlfa,  " 
                    "IIF (t.count > 1, '',  iif (t.Code like '%Zomer', '01-04', '01-10')) as StartDag " 
                    "from ( " 
                    "SELECT ws.Id as EAGID, " 
                    "ws.code as EAGCode, " 
                    "1000000 * ws.id + b.id as BakjeID,  " 
                    "iif(bp.Code like '%Onder', 2, 1) as Laagvolgorde,  " 
                    "bp.PythonCode as ClusterType, " 
                    "bpw.waarde as Waarde, " 
                    "MAX(bp.code) as code, " 
                    "count(*) as Count " 
                    "From (((((Bakken b " 
                    "Inner Join BakTypen bt on bt.id = b.baktypeid) " 
                    "Inner Join Deelgebieden dg on dg.id = b.deelgebiedid) " 
                    "Inner Join Watersystemen ws on ws.id = dg.watersysteemid) " 
                    "Inner Join BakParamWaarden bpw on bpw.bakId = b.Id) "  
                    "Inner join BakParams bp on bp.id = bpw.bakparamid) " 
                    "Where bp.pythoncode in ('Qkwel','Qwegz') "
                    "and b.id  in (select b.id from bakken b inner join Bakparamwaarden bpw on bpw.bakid = b.id where bpw.bakparamid = 13 and bpw.waarde > 0) "
                    "and bt.code <> 'Water' "
                    "GROUP BY ws.Id, ws.code, ws.id, b.id, iif(bp.Code like '%Onder', 2, 1), bp.PythonCode, bpw.waarde "
                    "ORDER BY WS.Code "
                    ") as T "
                    "WHERE T.EAGID = {}".format(iWatersysteem[0]) 
                    )
    df2 = pd.read_sql(GETREEKSEXCLWATERSQL, cnxn)
    
    GETREEKSWATERSQL = ("SELECT  " 
                    "t.EAGID as EAGID, " 
                    "t.EAGCode As EAGCode, " 
                    "t.BakjeID as BakjeID, " 
                    "t.Laagvolgorde as Laagvolgorde, " 
                    "t.ClusterType as ClusterType, " 
                    "IIF(t.Count > 1, 'Constant', 'ValueSeries') as ParamType, " 
                    "t.Waarde as Waarde, " 
                    "'' as WaardeAlfa,  " 
                    "IIF (t.count > 1, '',  iif (t.Code like '%Zomer', '01-04', '01-10')) as StartDag " 
                    "from ( " 
                    "SELECT DISTINCT ws.Id as EAGID, " 
                    "ws.code as EAGCode, " 
                    "1000000 * ws.id as BakjeID,  " 
                    "iif(bp.Code like '%Onder', 2, 1) as Laagvolgorde,  " 
                    "bp.PythonCode as ClusterType, " 
                    "bpw.waarde as Waarde, " 
                    "MAX(bp.code) as code, " 
                    "count(*) as Count " 
                    "From (((((Bakken b " 
                    "Inner Join BakTypen bt on bt.id = b.baktypeid) " 
                    "Inner Join Deelgebieden dg on dg.id = b.deelgebiedid) " 
                    "Inner Join Watersystemen ws on ws.id = dg.watersysteemid) " 
                    "Inner Join BakParamWaarden bpw on bpw.bakId = b.Id) "  
                    "Inner join BakParams bp on bp.id = bpw.bakparamid) " 
                    "Where bp.pythoncode in ('Qkwel','Qwegz') "
                    "and b.id  in (select b.id from bakken b inner join Bakparamwaarden bpw on bpw.bakid = b.id where bpw.bakparamid = 13 and bpw.waarde > 0) "
                    "and bt.code = 'Water' "
                    "GROUP BY ws.Id, ws.code, ws.id, b.id, iif(bp.Code like '%Onder', 2, 1), bp.PythonCode, bpw.waarde "
                    "ORDER BY WS.Code "
                    ") as T "
                    "WHERE T.EAGID = {}".format(iWatersysteem[0]) 
                    )
    df3 = pd.read_sql(GETREEKSWATERSQL, cnxn)

    GETREEKSWATERHTARGETSQL = (" SELECT DISTINCT ws.Id as EAGID, "
                    "ws.code as EAGCode, "
                    "1000000 * ws.id as BakjeID, "
                    "'1' as Laagvolgorde, "
                    "wsp.PythonCode as ClusterType, "
                    "'ValueSeries' as ParamType, " 
                    "wspw.waarde as Waarde, "
                    "'' as WaardeAlfa, "
                    "iif (wsp.Code like '%1', '15-03', iif(wsp.Code like '%2', '01-05', iif(wsp.code like '%3', '15-08', '01-10'))) as StartDag "
                    "From (((((Bakken b "
                    "Inner Join BakTypen bt on bt.id = b.baktypeid) "
                    "Inner Join Deelgebieden dg on dg.id = b.deelgebiedid) "
                    "Inner Join Watersystemen ws on ws.id = dg.watersysteemid) "
                    "Inner Join WatersysteemParamWaarden wspw on wspw.watersysteemId = ws.Id) "
                    "Inner join WatersysteemParams wsp on wsp.id = wspw.watersysteemparamid) "
                    "Where wsp.pythoncode like 'hTarget%'  and wsp.code like '%Periode%' "
                    "and b.id  in (select b.id from bakken b inner join Bakparamwaarden bpw on bpw.bakid = b.id where bpw.bakparamid = 13 and bpw.waarde > 0) "
                    "and bt.code = 'Water' "
                    "and ws.id = {}".format(iWatersysteem[0]) + 
                    " GROUP BY ws.Id, ws.code, ws.id, b.id, wsp.pythonCode, wspw.waarde, wsp.code "
                    "ORDER BY WS.Code "
                    )

    df4 = pd.read_sql(GETREEKSWATERHTARGETSQL, cnxn)

    df = pd.concat([df1, df2, df3, df4], axis=0)

    if not df.empty:
        df.to_csv(os.path.join(outdir, "reeks_{0}_{1}.csv".format(iWatersysteem[0], iWatersysteem[2])), sep=";")


for iWatersysteem in Watersysteem_list:
    GETSERIESSQL = ("TRANSFORM max(r.waarde) "
            "SELECT r.datum as datum "
            "From  "
            "((Registraties r "
            "INNER JOIN Meetpunten mp on mp.id = r.meetpuntId) "
            "INNER JOIN MeetpuntTypen mpt on mpt.id = mp.meetpunttypeid) "
            "WHERE mp.watersysteemid = {}".format(iWatersysteem[0]) +
            " GROUP BY r.datum "
            "PIVOT mpt.pythoncode + Cstr(mp.volgorde) + '|' + mp.Omschrijving" )
    
    df = pd.read_sql(GETSERIESSQL, cnxn)

    if not df.empty:
        df.to_csv(os.path.join(outdir, "series_{0}_{1}.csv".format(iWatersysteem[0], iWatersysteem[2])), sep=";")


cnxn.close()
