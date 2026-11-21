# 把整站推到阿里云 OSS（静态网站托管）
#
# 用法：
#   1. 装 ossutil：https://help.aliyun.com/zh/oss/developer-reference/ossutil
#      （Windows 下载 ossutil64.exe 放进 PATH，或改下面的 $Oss 路径）
#   2. 配置好 AK：ossutil config
#   3. 在仓库根目录执行：
#        powershell -ExecutionPolicy Bypass -File scripts/deploy-oss.ps1 -Bucket oss://你的bucket -Endpoint oss-cn-hangzhou.aliyuncs.com
#
# 页面是纯静态的，交互（搜索 / 分类 / 详情 / 抽签 / 换主题）全在浏览器里跑，不需要任何后端。

param(
  [Parameter(Mandatory = $true)][string]$Bucket,
  [string]$Endpoint = "oss-cn-hangzhou.aliyuncs.com",
  [string]$Oss = "ossutil64"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

if ($Bucket -notmatch "^oss://") { throw "Bucket 要写成 oss://名称 的形式" }

Write-Host "==> 上传到 $Bucket" -ForegroundColor Cyan
& $Oss cp -r "$root" $Bucket -f -e $Endpoint --exclude "_*" --exclude ".git/*"

Write-Host "==> 修正 Content-Type（OSS 默认会给 html/js 存成 application/octet-stream，浏览器会变成下载）" -ForegroundColor Cyan
& $Oss set-meta $Bucket -r -f -e $Endpoint --include "*.html" "Content-Type:text/html; charset=utf-8" "Content-Disposition:inline"
& $Oss set-meta $Bucket -r -f -e $Endpoint --include "*.js"   "Content-Type:application/javascript; charset=utf-8"
& $Oss set-meta $Bucket -r -f -e $Endpoint --include "*.css"  "Content-Type:text/css; charset=utf-8"
& $Oss set-meta $Bucket -r -f -e $Endpoint --include "*.webp" "Content-Type:image/webp"
& $Oss set-meta $Bucket -r -f -e $Endpoint --include "*.woff2" "Content-Type:font/woff2"
& $Oss set-meta $Bucket -r -f -e $Endpoint --include "*.svg"  "Content-Type:image/svg+xml"
& $Oss set-meta $Bucket -r -f -e $Endpoint --include "*.json" "Content-Type:application/json; charset=utf-8"

Write-Host ""
Write-Host "传完了。还要在控制台做两件事：" -ForegroundColor Yellow
Write-Host "  1. 基础设置 → 静态页面 → 默认首页填 index.html（默认 404 也填 index.html）"
Write-Host "  2. 权限管理 → 读写权限 → 公共读"
Write-Host "然后访问：http://<bucket>.$Endpoint/"
