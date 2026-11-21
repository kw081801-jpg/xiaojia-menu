# Xiaojia Menu - Windows Server deploy (ASCII output on purpose: consoles often run GBK)
# Run in an admin PowerShell / web terminal:
#   iwr https://ghproxy.net/https://raw.githubusercontent.com/kw081801-jpg/xiaojia-menu/main/scripts/deploy-windows.ps1 -UseBasicParsing | iex
#
# Steps: fetch code -> install Python if missing -> open firewall -> register startup task

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$AppDir = "C:\xiaojia-menu"
$TaskName = "XiaojiaMenu"
$ZipUrl = "https://ghproxy.net/https://github.com/kw081801-jpg/xiaojia-menu/archive/refs/heads/main.zip"
$PyUrl = "https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe"

function Say($m) { Write-Host ""; Write-Host "==> $m" -ForegroundColor Cyan }

Say "check port"
$Port = 80
if (Get-NetTCPConnection -LocalPort 80 -State Listen -ErrorAction SilentlyContinue) {
  $Port = 8080
  Write-Host "port 80 busy, using 8080"
} else {
  Write-Host "using port 80"
}

Say "download site files"
$zip = Join-Path $env:TEMP "xj-menu.zip"
Invoke-WebRequest -Uri $ZipUrl -OutFile $zip -UseBasicParsing
if (Test-Path $AppDir) { Remove-Item $AppDir -Recurse -Force }
$tmp = Join-Path $env:TEMP ("xj-" + [guid]::NewGuid().ToString("N"))
Expand-Archive -Path $zip -DestinationPath $tmp -Force
$inner = Get-ChildItem $tmp | Select-Object -First 1
Move-Item $inner.FullName $AppDir
Remove-Item $tmp, $zip -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "files -> $AppDir"

Say "check python"
$py = $null
$candidates = @(
  "C:\Program Files\Python312\python.exe",
  "C:\Program Files\Python311\python.exe",
  "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
)
foreach ($c in $candidates) { if (Test-Path $c) { $py = $c; break } }
if (-not $py) {
  $w = Get-Command python.exe -ErrorAction SilentlyContinue
  if ($w) { $py = $w.Source }
}
if (-not $py) {
  Say "install python 3.12 (~60s)"
  $exe = Join-Path $env:TEMP "py-install.exe"
  Invoke-WebRequest -Uri $PyUrl -OutFile $exe -UseBasicParsing
  Start-Process -FilePath $exe -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait
  Start-Sleep -Seconds 3
  foreach ($c in $candidates) { if (Test-Path $c) { $py = $c; break } }
}
if (-not $py) { throw "python not installed" }
Write-Host "python: $py  $(& $py -V)"

Say "open firewall port $Port"
$ruleName = "Xiaojia Menu $Port"
Remove-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port | Out-Null

Say "register startup task"
$cmd = "`"$py`" `"$AppDir\server.py`" --port $Port"
schtasks /Delete /TN $TaskName /F 2>$null | Out-Null
schtasks /Create /TN $TaskName /TR $cmd /SC ONSTART /RU SYSTEM /RL HIGHEST /F | Out-Null
schtasks /Run /TN $TaskName | Out-Null
Start-Sleep -Seconds 5

Say "self check"
try {
  $r = Invoke-WebRequest "http://127.0.0.1:$Port/" -UseBasicParsing -TimeoutSec 10
  Write-Host ("index HTTP {0}" -f $r.StatusCode)
  foreach ($f in @("bear", "penguin", "katsu", "tapioca", "lizard")) {
    $c = (Invoke-WebRequest "http://127.0.0.1:$Port/images/friends/$f.png" -UseBasicParsing -TimeoutSec 10).StatusCode
    Write-Host ("  {0,-8} {1}" -f $f, $c)
  }
} catch {
  Write-Host ("self check FAILED: {0}" -f $_.Exception.Message) -ForegroundColor Red
  Write-Host "log: Get-Content $AppDir\server.log -Tail 30"
  throw
}

Write-Host ""
Write-Host "================ DEPLOYED ================" -ForegroundColor Green
Write-Host "front : http://<public-ip>:$Port/"
Write-Host "admin : http://<public-ip>:$Port/admin.html"
Write-Host "port  : $Port   (open it in Tencent Cloud console firewall)"
Write-Host "data  : $AppDir\data.json"
Write-Host "=========================================="
