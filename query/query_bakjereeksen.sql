SELECT t.EAGID                                                              AS EAGID,
       t.EAGCode                                                            AS EAGCode,
       t.BakjeID                                                            AS BakjeID,
       t.Laagvolgorde                                                       AS Laagvolgorde,
       t.ClusterType                                                        AS ClusterType,
       IIF(t.Count > 1, 'Constant', 'ValueSeries')                          AS ParamType,
       t.Waarde                                                             AS Waarde, 
       ''                                                                   AS WaardeAlfa,
       IIF (t.count > 1, '', iif (t.Code like '%Zomer', '01-04', '01-10'))  AS StartDag 
  FROM ( SELECT 
       ws.Id                                                                AS EAGID,
       ws.code                                                              AS EAGCode,
       1000000*ws.id + b.id                                                 AS BakjeID,
       iif(bp.Code like '%Onder', 2, 1)                                     AS Laagvolgorde,
       bp.PythonCode                                                        AS ClusterType,
       bpw.waarde                                                           AS Waarde,
       MAX(bp.code)                                                         AS code,
       count(*)                                                             AS Count 
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
 WHERE bp.pythoncode in ('Qkwel','Qwegz') 
   AND b.id in (select b.id 
  FROM bakken b 
INNER JOIN Bakparamwaarden bpw 
    ON bpw.bakid = b.id 
 WHERE bpw.bakparamid = 13 
   AND bpw.waarde > 0) 
   AND bt.code <> 'Water' 
GROUP BY ws.Id,
       ws.code,
       ws.id,
       b.id,
       iif(bp.Code like '%Onder', 2, 1),
       bp.PythonCode,
       bpw.waarde 
ORDER BY WS.Code )           AS T 
 WHERE T.EAGID = 1210