SELECT ws.Id                            AS EAGID,
       ws.code                          AS EAGCode,
       1000000 * ws.id + b.id           AS BakjeID,
       iif(bp.Code like '%Onder', 2, 1) AS Laagvolgorde,
       bp.PythonCode                    AS ParamCode,
       bpw.waarde                       AS Waarde 
  FROM (((((Bakken b 
INNER JOIN BakTypen bt 
    ON bt.id = b.baktypeid) 
INNER JOIN Deelgebieden dg 
    ON dg.id = b.deelgebiedid) 
INNER JOIN Watersystemen ws 
    ON ws.id = dg.watersysteemid) 
INNER JOIN BakParamWaarden bpw 
    ON bpw.bakId = b.Id) 
INNER JOIN BakParams bp 
    ON bp.id = bpw.bakparamid) 
 WHERE bpw.bakparamid <> 13 
   AND bt.code <> 'Water' 
   AND bp.pythoncode <> '' 
   AND bp.pythoncode <> 'QKwel' 
   AND b.id in (select b.id 
  FROM bakken b 
INNER JOIN Bakparamwaarden bpw 
    ON bpw.bakid = b.id 
 WHERE bpw.bakparamid = 13 
   AND bpw.waarde > 0) 
   AND ws.id = 1260 
ORDER BY WS.Code
