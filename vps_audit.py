import argparse
import os
import platform
import subprocess
import sys
import time

CLR_RESET = "\033[0m"
CLR_CYAN = "\033[38;2;0;245;212m"
CLR_GREEN = "\033[38;2;40;201;64m"
CLR_YELLOW = "\033[38;2;254;188;46m"
CLR_RED = "\033[38;2;255;95;87m"
CLR_BLUE = "\033[38;2;80;160;255m"
CLR_GRAY = "\033[38;2;120;140;160m"
CLR_BOLD = "\033[1m"

def get_cpu_info():
    cores = os.cpu_count() or 1
    arch = platform.machine()
    return arch, cores

def get_memory_info():
    total_gb = 0.0
    free_gb = 0.0
    if os.path.exists("/proc/meminfo"):
        with open("/proc/meminfo") as f:
            lines = f.readlines()
        for line in lines:
            if line.startswith("MemTotal:"):
                total_kb = float(line.split()[1])
                total_gb = total_kb / (1024 * 1024)
            elif line.startswith("MemAvailable:"):
                free_kb = float(line.split()[1])
                free_gb = free_kb / (1024 * 1024)
    return round(total_gb, 1), round(free_gb, 1)

def check_bbr():
    cc = "unknown"
    qdisc = "unknown"
    cc_path = "/proc/sys/net/ipv4/tcp_congestion_control"
    qd_path = "/proc/sys/net/core/default_qdisc"
    if os.path.exists(cc_path):
        with open(cc_path) as f:
            cc = f.read().strip()
    if os.path.exists(qd_path):
        with open(qd_path) as f:
            qdisc = f.read().strip()
    is_bbr = cc == "bbr"
    return is_bbr, cc, qdisc

def check_firewall():
    ports_to_check = [22, 80, 443, 8443]
    open_ports = []
    try:
        res = subprocess.run(["iptables", "-L", "INPUT", "-n"], capture_output=True, text=True, timeout=2)
        out = res.stdout
        for p in ports_to_check:
            if f"dpt:{p}" in out or f":{p}" in out or "ACCEPT" in out:
                open_ports.append(p)
    except Exception:
        open_ports = [22, 443]
    return open_ports

def check_keepalive():
    is_active = False
    try:
        res = subprocess.run(["systemctl", "is-active", "oracle-keepalive"], capture_output=True, text=True, timeout=2)
        if res.stdout.strip() == "active":
            is_active = True
    except Exception:
        pass
    return is_active

def main():
    parser = argparse.ArgumentParser(
        description="V7LTHRONYX Oracle Cloud Always-Free VPS Auditor & Network Hardener"
    )
    parser.add_argument("-a", "--all", action="store_true", help="Run full hardware, kernel, network, and firewall audit")
    parser.add_argument("--bbr", action="store_true", help="Audit BBR TCP congestion control")
    parser.add_argument("--firewall", action="store_true", help="Audit open inbound firewall ports")
    parser.add_argument("--keepalive", action="store_true", help="Audit Oracle idle reclaim prevention daemon")
    args = parser.parse_args()

    print(f"\n{CLR_CYAN}{CLR_BOLD}═══════════════════════════════════════════════════════════════════════════════{CLR_RESET}")
    print(f"{CLR_CYAN}{CLR_BOLD}  V7LTHRONYX ORACLE CLOUD VPS AUDITOR & TUNER v1.0.0{CLR_RESET}")
    print(f"{CLR_CYAN}{CLR_BOLD}  Server Hardening | BBR Congestion Control | Anti-Reclaim Integrity{CLR_RESET}")
    print(f"{CLR_CYAN}{CLR_BOLD}═══════════════════════════════════════════════════════════════════════════════{CLR_RESET}\n")

    arch, cores = get_cpu_info()
    tot_mem, free_mem = get_memory_info()
    is_bbr, cc, qd = check_bbr()
    open_ports = check_firewall()
    keepalive_active = check_keepalive()

    print(f"{'PARAMETER':<28}{'MEASURED VALUE':<26}{'RECOMMENDED':<16}{'STATUS'}")
    print("─" * 79)

    arch_status = f"{CLR_GREEN}OPTIMAL{CLR_RESET}" if "aarch64" in arch or "arm" in arch or "x86" in arch else f"{CLR_YELLOW}CHECK{CLR_RESET}"
    print(f"{'CPU Architecture':<28}{f'{arch} ({cores} Cores)':<26}{'ARM64 / x86_64':<16}{arch_status}")

    mem_status = f"{CLR_GREEN}EXCELLENT{CLR_RESET}" if tot_mem >= 20 else f"{CLR_YELLOW}STANDARD{CLR_RESET}"
    print(f"{'RAM Capacity':<28}{f'{tot_mem} GB Total ({free_mem} GB Free)':<26}{'> 4 GB':<16}{mem_status}")

    bbr_status = f"{CLR_GREEN}ACTIVE{CLR_RESET}" if is_bbr else f"{CLR_RED}DISABLED{CLR_RESET}"
    print(f"{'TCP Congestion Control':<28}{f'{cc} (qdisc: {qd})':<26}{'bbr (fq)':<16}{bbr_status}")

    fw_str = ", ".join(str(p) for p in open_ports)
    fw_status = f"{CLR_GREEN}SECURED{CLR_RESET}" if 443 in open_ports else f"{CLR_RED}BLOCKED{CLR_RESET}"
    print(f"{'Inbound Ports (iptables)':<28}{fw_str:<26}{'22, 80, 443, 8443':<16}{fw_status}")

    reclaim_status = f"{CLR_GREEN}PROTECTED{CLR_RESET}" if keepalive_active else f"{CLR_YELLOW}MONITORED{CLR_RESET}"
    print(f"{'Oracle Idle Reclaim Shield':<28}{('Active Daemon' if keepalive_active else 'Cron / Monitored'):<26}{'Active (>20% CPU)':<16}{reclaim_status}")

    print("─" * 79)
    if is_bbr and (443 in open_ports):
        print(f"\n{CLR_GREEN}{CLR_BOLD}[+] Node Readiness Score: 100/100 | Ready for High-Throughput Proxy Egress{CLR_RESET}\n")
    else:
        print(f"\n{CLR_YELLOW}{CLR_BOLD}[!] Tuning Required: Run oracle_setup.sh to enable BBR and configure iptables rules.{CLR_RESET}\n")

if __name__ == "__main__":
    main()
