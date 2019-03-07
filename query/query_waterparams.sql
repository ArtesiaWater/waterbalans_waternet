SELECT distinct
       ws.Id          AS EAGID,
       ws.code        AS EAGCode,
       1000000*ws.id  AS BakjeID,
       '1'            AS Laagvolgorde,
       wsp.PythonCode AS ParamCode,
       wspw.waarde    AS Waarde 
  FROM (((((Bakken b 
INNER JOIN BakTypen bt 
    ON bt.id = b.baktypeid) 
INNER JOIN Deelgebieden dg 
    ON dg.id = b.deelgebiedid) 
INNER JOIN Watersystemen ws 
    ON ws.id = dg.watersysteemid) 
INNER JOIN WatersysteemParamWaarden wspw 
    ON wspw.watersysteemId = ws.Id) 
INNER JOIN WatersysteemParams wsp 
    ON wsp.id = wspw.watersysteemparamid) 
 WHERE b.id in (select b.id 
  FROM bakken b 
INNER JOIN Bakparamwaarden bpw 
    ON bpw.bakid = b.id 
 WHERE bpw.bakparamid = 13 
   AND bpw.waarde > 0) 
   AND wsp.pythoncode <> '' 
   AND bt.code = 'Water' 
   AND wsp.pythoncode not like 'hTargetM%' 
   AND ws.id = 1260 
ORDER BY WS.Code