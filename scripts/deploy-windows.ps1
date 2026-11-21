# 小家菜单 · Windows Server 一键部署
# 用法（管理员 PowerShell / 控制台 Web 终端里）：
#   powershell -NoProfile -ExecutionPolicy Bypass -Command "iwr https://ghproxy.net/https://raw.githubusercontent.com/kw081801-jpg/xiaojia-menu/main/scripts/deploy-windows.ps1 -UseBasicParsing | iex"
#
# 做四件事：拉代码 -> 装 Python（没有的话）-> 开防火墙 -> 注册开机任务并启动

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$AppDir = "C:\xiaojia-menu"
$TaskName = "XiaojiaMenu"
$ZipUrl = "https://ghproxy.net/https://github.com/kw081801-jpg/xiaojia-menu/archive/refs/heads/main.zip"
$PyUrl = "https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe"

function Say($m) { Write-Host "`n==> $m" -ForegroundColor Cyan }

# ---------- 1. 选端口 ----------
Say "检查端口"
$Port = 80
if ((Get-NetTCPConnection -LocalPort 80 -State Listen -ErrorAction SilentlyContinue)) {
  $Port = 8080
  Write-Host "80 被占用，改用 8080"
} else {
  Write-Host "使用 80"
}

# ---------- 2. 拉代码 ----------
Say "下载站点文件"
$zip = Join-Path $env:TEMP "xj-menu.zip"
Invoke-WebRequest -Uri $ZipUrl -OutFile $zip -UseBasicParsing
if (Test-Path $AppDir) { Remove-Item $AppDir -Recurse -Force }
$tmp = Join-Path $env:TEMP ("xj-" + [guid]::NewGuid().ToString("N"))
Expand-Archive -Path $zip -DestinationPath $tmp -Force
$inner = Get-ChildItem $tmp | Select-Object -First 1
Move-Item $inner.FullName $AppDir
Remove-Item $tmp,$zip -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "已放到 $AppDir"

# ---------- 3. Python ----------
Say "检查 Python"
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
  Say "安装 Python 3.12（约 60 秒）"
  $exe = Join-Path $env:TEMP "py-install.exe"
  Invoke-WebRequest -Uri $PyUrl -OutFile $exe -UseBasicParsing
  Start-Process -FilePath $exe -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait
  Start-Sleep -Seconds 3
  foreach ($c in $candidates) { if (Test-Path $c) { $py = $c; break } }
}
if (-not $py) { throw "Python 没装上，手动装一个再重跑" }
Write-Host "Python: $py  ($(& $py -V))"

# ---------- 4. 防火墙 ----------
Say "放行端口 $Port"
$ruleName = "Xiaojia Menu $Port"
Remove-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port | Out-Null

# ---------- 5. 开机任务 ----------
Say "注册开机任务 $TaskName"
$cmd = "`"$py`" `"$AppDir\server.py`" --port $Port"
schtasks /Delete /TN $TaskName /F 2>$null | Out-Null
schtasks /Create /TN $TaskName /TR $cmd /SC ONSTART /RU SYSTEM /RL HIGHEST /F | Out-Null
schtasks /Run /TN $TaskName | Out-Null
Start-Sleep -Seconds 4

# ---------- 6. 自检 ----------
Say "自检"
try {
  $r = Invoke-WebRequest "http://127.0.0.1:$Port/" -UseBasicParsing -TimeoutSec 10
  Write-Host ("首页 HTTP {0}" -f $r.StatusCode)
  foreach ($f in @("bear","penguin","katsu","tapioca","lizard")) {
    $c = (Invoke-WebRequest "http://127.0.0.1:$Port/images/friends/$f.png" -UseBasicParsing -TimeoutSec 10).StatusCode
    Write-Host ("  {0,-8} {1}" -f $f, $c)
  }
} catch {
  Write-Host "自检失败：$($_.Exception.Message)" -ForegroundColor Red
  Write-Host "看日志：Get-Content $AppDir\server.log -Tail 30"
  throw
}

$ip = (Invoke-WebRequest "https://ifconfig.me/ip" -UseBasicParsing -TimeoutSec 8).Content.Trim()
Write-Host ""
Write-Host "================ 部署完成 ================" -ForegroundColor Green
Write-Host "前台   http://$ip`:$Port/"
Write-Host "管理台 http://$ip`:$Port/admin.html"
Write-Host ""
Write-Host "还差一步：腾讯云控制台 -> 防火墙 -> 添加规则 TCP $Port"
Write-Host "数据：$AppDir\data.json   图片：$AppDir\images\uploads"
