#!/usr/bin/env bash
set -e

cat << 'EOF' > /etc/sysctl.d/99-v7l-bbr.conf
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_fin_timeout = 20
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_max_syn_backlog = 16384
net.core.somaxconn = 32768
net.ipv4.tcp_rmem = 4096 87380 67108864
net.ipv4.tcp_wmem = 4096 65536 67108864
fs.file-max = 1000000
vm.swappiness = 10
EOF

sysctl --system > /dev/null 2>&1 || true

if command -v iptables > /dev/null 2>&1; then
  iptables -I INPUT -p tcp --dport 22 -j ACCEPT || true
  iptables -I INPUT -p tcp --dport 80 -j ACCEPT || true
  iptables -I INPUT -p tcp --dport 443 -j ACCEPT || true
  iptables -I INPUT -p tcp --dport 8443 -j ACCEPT || true
  iptables -I INPUT -p udp --dport 443 -j ACCEPT || true
  iptables -I INPUT -p udp --dport 8443 -j ACCEPT || true
  if command -v netfilter-persistent > /dev/null 2>&1; then
    netfilter-persistent save || true
  fi
fi

if command -v ufw > /dev/null 2>&1; then
  ufw allow 22/tcp || true
  ufw allow 80/tcp || true
  ufw allow 443/tcp || true
  ufw allow 8443/tcp || true
  ufw allow 443/udp || true
  ufw allow 8443/udp || true
fi

cat << 'EOF' > /usr/local/bin/oracle-keepalive.sh
#!/usr/bin/env bash
while true; do
  sha256sum /dev/urandom | head -c 64 > /dev/null
  sleep 45
done
EOF
chmod +x /usr/local/bin/oracle-keepalive.sh

cat << 'EOF' > /etc/systemd/system/oracle-keepalive.service
[Unit]
Description=Oracle Cloud Always-Free Idle Reclaim Prevention Daemon
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/oracle-keepalive.sh
Restart=always
RestartSec=10
Nice=19
CPUWeight=20

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload > /dev/null 2>&1 || true
systemctl enable --now oracle-keepalive.service > /dev/null 2>&1 || true

echo "Oracle Cloud Always-Free VPS Optimization Complete."
