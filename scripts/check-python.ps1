# 诊断：这台 Windows 上到底有没有 Python、是哪个
# 用法：
#   iwr https://ghproxy.net/https://raw.githubusercontent.com/kw081801-jpg/xiaojia-menu/main/scripts/check-python.ps1 -UseBasicParsing | iex
# 输出纯英文，不会乱码

Write-Host "== 1. PATH 里的 python / py / python3 =="
foreach ($n in @("python.exe", "python3.exe", "py.exe")) {
  $w = Get-Command $n -ErrorAction SilentlyContinue
  if ($w) { Write-Host ("  {0,-12} {1}" -f $n, $w.Source) } else { Write-Host ("  {0,-12} (not found)" -f $n) }
}

Write-Host "== 2. py launcher 列表 =="
try { & py -0p 2>&1 | ForEach-Object { Write-Host "  $_" } } catch { Write-Host "  py launcher not available" }

Write-Host "== 3. 常见安装目录 =="
$dirs = @(
  "C:\Program Files\Python312", "C:\Program Files\Python311", "C:\Program Files\Python310",
  "C:\Python312", "C:\Python311", "C:\Python310",
  "C:\ProgramData\Anaconda3", "C:\ProgramData\miniconda3",
  "$env:LOCALAPPDATA\Programs\Python\Python312",
  "$env:LOCALAPPDATA\Programs\Python\Python311",
  "$env:LOCALAPPDATA\Microsoft\WindowsApps"
)
foreach ($d in $dirs) {
  if (Test-Path $d) {
    $exes = Get-ChildItem $d -Filter "python*.exe" -ErrorAction SilentlyContinue | Select-Object -First 3
    foreach ($e in $exes) {
      $isStub = $e.FullName -like "*WindowsApps*"
      Write-Host ("  {0} {1}" -f $e.FullName, $(if ($isStub) { "(store stub, may not be real)" } else { "" }))
    }
  }
}

Write-Host "== 4. 注册表 =="
foreach ($k in @("HKLM:\SOFTWARE\Python\PythonCore", "HKLM:\SOFTWARE\WOW6432Node\Python\PythonCore", "HKCU:\SOFTWARE\Python\PythonCore")) {
  if (Test-Path $k) {
    Get-ChildItem $k | ForEach-Object {
      $ip = (Get-ItemProperty "$($_.PSPath)\InstallPath" -ErrorAction SilentlyContinue)
      if ($ip) { Write-Host ("  {0} -> {1}" -f $_.PSChildName, $ip.'(default)') }
    }
  }
}

Write-Host "== 5. 实测能不能跑 =="
$cands = @()
foreach ($n in @("python.exe", "python3.exe", "py.exe")) {
  $w = Get-Command $n -ErrorAction SilentlyContinue
  if ($w) { $cands += $w.Source }
}
Get-ChildItem "C:\Program Files" -Filter "Python3*" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
  $p = Join-Path $_.FullName "python.exe"
  if (Test-Path $p) { $cands += $p }
}
if (Test-Path "C:\Python312\python.exe") { $cands += "C:\Python312\python.exe" }

$found = $false
foreach ($c in ($cands | Select-Object -Unique)) {
  try {
    $v = & $c -c "import sys;print(sys.version.split()[0])" 2>&1
    if ($LASTEXITCODE -eq 0) {
      Write-Host ("  OK  {0}  ->  {1}" -f $c, $v)
      $found = $true
    } else {
      Write-Host ("  BAD {0}  (exit {1})" -f $c, $LASTEXITCODE)
    }
  } catch {
    Write-Host ("  BAD {0}  ({1})" -f $c, $_.Exception.Message)
  }
}
if (-not $found) { Write-Host "  no working python found" -ForegroundColor Yellow }
