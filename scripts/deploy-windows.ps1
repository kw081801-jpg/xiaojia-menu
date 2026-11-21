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
$PyMirrors = @(
  "https://mirrors.huaweicloud.com/python/3.12.10/python-3.12.10-amd64.exe",
  "https://mirrors.aliyun.com/python-release/windows/python-3.12.10-amd64.exe",
  "https://registry.npmmirror.com/-/binary/python/3.12.10/python-3.12.10-amd64.exe",
  "https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe"
)

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
$saved = $null
if (Test-Path (Join-Path $AppDir "data.json")) {
  $saved = Join-Path $env:TEMP ("xj-data-" + [guid]::NewGuid().ToString("N") + ".json")
  Copy-Item (Join-Path $AppDir "data.json") $saved
  Write-Host "keep existing data.json"
}
if (Test-Path $AppDir) { Remove-Item $AppDir -Recurse -Force }
$tmp = Join-Path $env:TEMP ("xj-" + [guid]::NewGuid().ToString("N"))
Expand-Archive -Path $zip -DestinationPath $tmp -Force
$inner = Get-ChildItem $tmp | Select-Object -First 1
Move-Item $inner.FullName $AppDir
Remove-Item $tmp, $zip -Recurse -Force -ErrorAction SilentlyContinue
if ($saved -and (Test-Path $saved)) {
  Copy-Item $saved (Join-Path $AppDir "data.json") -Force
  Remove-Item $saved -Force
  Write-Host "data.json restored"
}
Write-Host "files -> $AppDir"

Say "check python"
function Find-Python {
  $cands = @()
  foreach ($k in @("HKLM:\SOFTWARE\Python\PythonCore", "HKLM:\SOFTWARE\WOW6432Node\Python\PythonCore", "HKCU:\SOFTWARE\Python\PythonCore")) {
    if (Test-Path $k) {
      Get-ChildItem $k -ErrorAction SilentlyContinue | ForEach-Object {
        $ip = Get-ItemProperty "$($_.PSPath)\InstallPath" -ErrorAction SilentlyContinue
        if ($ip -and $ip.'(default)') { $cands += (Join-Path $ip.'(default)' "python.exe") }
      }
    }
  }
  foreach ($d in @("C:\Program Files\Python312", "C:\Program Files\Python311", "C:\Program Files\Python310",
                   "C:\Python312", "C:\Python311", "C:\Python310",
                   "$env:LOCALAPPDATA\Programs\Python\Python312", "$env:LOCALAPPDATA\Programs\Python\Python311")) {
    $p = Join-Path $d "python.exe"
    if (Test-Path $p) { $cands += $p }
  }
  foreach ($n in @("python.exe", "python3.exe", "py.exe")) {
    $w = Get-Command $n -ErrorAction SilentlyContinue
    if ($w) { $cands += $w.Source }
  }
  foreach ($c in ($cands | Select-Object -Unique)) {
    if ($c -like "*WindowsApps*") { continue }   # App Store stub, not a real python
    try {
      $v = & $c -c "import sys;print(sys.version.split()[0])" 2>&1
      if ($LASTEXITCODE -eq 0) { return $c }
    } catch { }
  }
  return $null
}

$py = Find-Python
if ($py) { Write-Host "found existing python: $py" }
if (-not $py) {
  Say "download python installer (trying cn mirrors first)"
  $exe = Join-Path $env:TEMP "py-install.exe"
  $got = $false
  foreach ($u in $PyMirrors) {
    try {
      Write-Host "  from $u"
      Invoke-WebRequest -Uri $u -OutFile $exe -UseBasicParsing -TimeoutSec 300
      if ((Get-Item $exe).Length -gt 20MB) { $got = $true; break }
      Write-Host "  too small, try next"
    } catch {
      Write-Host "  failed: $($_.Exception.Message)"
    }
  }
  if (-not $got) { throw "python installer download failed on all mirrors" }

  Say "install python 3.12 (silent, ~60s)"
  Start-Process -FilePath $exe -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_pip=0" -Wait
  Start-Sleep -Seconds 5
  $py = Find-Python
  if (-not $py) {
    # 有些安装包装到用户目录
    $alt = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
    if (Test-Path $alt) { $py = $alt }
  }
}
if (-not $py) { throw "python not installed" }
Write-Host "python: $py  $(& $py -V)"

Say "open firewall port $Port"
$ruleName = "Xiaojia Menu $Port"
Remove-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port | Out-Null

Say "register startup task"
$action = New-ScheduledTaskAction -Execute $py -Argument ('"{0}" --port {1}' -f (Join-Path $AppDir "server.py"), $Port) -WorkingDirectory $AppDir
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero)
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
Start-ScheduledTask -TaskName $TaskName
Write-Host "task $TaskName registered (at startup, running now)"
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
