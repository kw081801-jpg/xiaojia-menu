#!/usr/bin/env bash
# 腾讯云轻量应用服务器一键部署：Ubuntu 20.04+ / Debian 11+ / CentOS Stream 8+
#
#   curl -O https://raw.githubusercontent.com/kw081801-jpg/xiaojia-menu/main/scripts/deploy-tencent.sh
#   sudo bash deploy-tencent.sh
#
# 想换目录/端口/密码：
#   sudo APP_DIR=/www/xiaojia PORT=80 XJ_ADMIN_PASSWORD=你的密码 bash deploy-tencent.sh
#
# 说明：默认用 ghproxy 镜像拉 GitHub（大陆服务器直连 github 经常超时）。
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/xiaojia-menu}"
PORT="${PORT:-8080}"
REPO="${REPO:-https://ghproxy.net/https://github.com/kw081801-jpg/xiaojia-menu.git}"
PASSWORD="${XJ_ADMIN_PASSWORD:-xiaojia}"
SERVICE="xiaojia-menu"

say() { printf "\n\033[1;36m==> %s\033[0m\n" "$*"; }
die() { printf "\n\033[1;31m!! %s\033[0m\n" "$*" >&2; exit 1; }

[ "$(id -u)" = "0" ] || die "请用 root 跑：sudo bash $0"

# ---------- 1. 依赖 ----------
say "检查 python3 / git"
if command -v apt-get >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y -qq python3 git curl >/dev/null
elif command -v dnf >/dev/null 2>&1; then
  dnf install -y -q python3 git curl >/dev/null
elif command -v yum >/dev/null 2>&1; then
  yum install -y -q python3 git curl >/dev/null
else
  die "没识别出包管理器，请手动装 python3 和 git"
fi
python3 -V

# ---------- 2. 代码 ----------
say "拉代码到 $APP_DIR"
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" pull --ff-only || true
else
  mkdir -p "$(dirname "$APP_DIR")"
  git clone --depth 1 "$REPO" "$APP_DIR"
fi
cd "$APP_DIR"
[ -f server.py ] || die "$APP_DIR 里没有 server.py，检查 REPO 是否拉对了"

# ---------- 3. systemd ----------
say "写 systemd 服务 $SERVICE"
cat > "/etc/systemd/system/$SERVICE.service" <<EOF
[Unit]
Description=Xiaojia Menu
After=network.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR
Environment=XJ_ADMIN_PASSWORD=$PASSWORD
ExecStart=$(command -v python3) $APP_DIR/server.py --port $PORT
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now "$SERVICE" >/dev/null
sleep 2
systemctl is-active "$SERVICE" >/dev/null || { journalctl -u "$SERVICE" -n 30 --no-pager; die "服务没起来，看上面的日志"; }

# ---------- 4. 系统防火墙 ----------
say "本机防火墙放行 $PORT"
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q active; then
  ufw allow "$PORT"/tcp >/dev/null || true
elif command -v firewall-cmd >/dev/null 2>&1 && firewall-cmd --state >/dev/null 2>&1; then
  firewall-cmd --permanent --add-port="$PORT"/tcp >/dev/null
  firewall-cmd --reload >/dev/null
fi

# ---------- 5. 自检 ----------
say "自检"
code=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/")
echo "首页 HTTP $code"
for f in bear penguin katsu tapioca lizard; do
  c=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/images/friends/$f.png")
  printf "  %-8s %s\n" "$f" "$c"
done
curl -s "http://127.0.0.1:$PORT/api/menu" | head -c 60; echo

IP=$(curl -s --max-time 5 https://ifconfig.me || echo "<你的公网IP>")
cat <<EOF

$(printf '\033[1;32m部署完成\033[0m')
  前台：http://$IP:$PORT/
  管理台：http://$IP:$PORT/admin.html    （密码：$PASSWORD）

还差一步：腾讯云控制台 → 轻量应用服务器 → 你的实例 → 防火墙 → 添加规则
  应用类型「自定义」 TCP  $PORT  来源 0.0.0.0/0

之后想换密码：sudo systemctl edit --full $SERVICE 改 Environment 行，再 restart。
EOF
