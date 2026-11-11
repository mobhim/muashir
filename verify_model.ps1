# Query the model of the Power BI Desktop instance that is currently open and print
# the headline measures, so they can be compared with reports/results.json.
#   powershell -File powerbi\verify_model.ps1
$ErrorActionPreference = 'Stop'
$dll = "$env:ProgramFiles\Microsoft Power BI Desktop\bin\Microsoft.PowerBI.AdomdClient.dll"
if (-not (Test-Path $dll)) { throw "Power BI Desktop client library not found: $dll" }
[void][Reflection.Assembly]::LoadFrom($dll)

$portFile = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\Power BI Desktop\AnalysisServicesWorkspaces" -Recurse -Filter 'msmdsrv.port.txt' -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $portFile) { throw 'No running Power BI Desktop model found. Open Muashir.pbip first.' }
$port = (Get-Content $portFile.FullName -Encoding Unicode).Trim()

$con = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection("Data Source=localhost:$port")
$con.Open()
$query = @'
EVALUATE ROW(
  "events", [عدد الإعلانات],
  "companies", [عدد الشركات],
  "seasons", [عدد المواسم],
  "spread_reaction", [الفرق عند الإعلان],
  "spread_drift60", [الفرق بعد الإعلان 60 يوم],
  "spread_drift60_beta", [الفرق بعد الإعلان 60 يوم (بيتا)],
  "rows_ar", COUNTROWS(fact_abnormal_return),
  "rows_path", COUNTROWS(fact_car_path)
)
'@
$cmd = $con.CreateCommand(); $cmd.CommandText = $query
$r = $cmd.ExecuteReader()
while ($r.Read()) { for ($i = 0; $i -lt $r.FieldCount; $i++) { "{0,-24} {1}" -f $r.GetName($i), $r.GetValue($i) } }
$r.Close(); $con.Close()
