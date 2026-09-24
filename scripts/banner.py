import os
import sys
import re
from datetime import datetime

# Enable ANSI colors and UTF-8 in Windows terminal
if sys.platform == "win32":
    os.system("")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ANSI TrueColor palette
CYAN   = "\033[38;2;80;220;240m"
MINT   = "\033[38;2;152;195;121m"
GREEN  = "\033[38;2;152;195;121m"
KEY    = "\033[38;2;160;205;105m"
BORDER = "\033[38;2;75;105;125m"
WHITE  = "\033[97m"
AMBER  = "\033[38;2;255;165;95m"
RESET  = "\033[0m"

def visible_len(s):
    return len(re.sub(r'\033\[[0-9;]*m', '', s))

def make_box_row(key, val_str, inner_w=62):
    prefix = f"{KEY}{key:<8}{RESET} {WHITE}{val_str}{RESET}"
    vis = visible_len(prefix)
    padding = " " * max(0, inner_w - vis)
    return f"{BORDER}│{RESET} {prefix}{padding} {BORDER}│{RESET}"

def make_box_top(title, inner_w=62):
    t_vis = len(title)
    left_dashes = "─" * 14
    right_dashes = "─" * max(0, inner_w - 16 - t_vis)
    return f"{BORDER}┌{left_dashes} {GREEN}{title}{RESET} {BORDER}{right_dashes}┐{RESET}"

def make_box_bottom(inner_w=62):
    return f"{BORDER}└{'─' * (inner_w + 2)}┘{RESET}"

date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Big Bold ASCII Art: Team HEXARK
hexark_art = [
    f"{CYAN}  ██╗  ██╗███████╗██╗  ██╗ █████╗ ██████╗ ██╗  ██╗{RESET}",
    f"{CYAN}  ██║  ██║██╔════╝╚██╗██╔╝██╔══██╗██╔══██╗██║ ██╔╝{RESET}",
    f"{MINT}  ███████║█████╗   ╚███╔╝ ███████║██████╔╝█████╔╝ {RESET}",
    f"{MINT}  ██╔══██║██╔══╝   ██╔██╗ ██╔══██║██╔══██╗██╔═██╗ {RESET}",
    f"{MINT}  ██║  ██║███████╗██╔╝ ██╗██║  ██║██║  ██║██║  ██╗{RESET}",
    f"{CYAN}  ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝{RESET}"
]

INNER_W = 64

print()
for line in hexark_art:
    print(line)
print()

# Session Card
print(f"  {make_box_top('Session / SIH 2026', INNER_W)}")
print(f"  {make_box_row('TEAM', 'HEXARK // Smart India Hackathon 2026', INNER_W)}")
print(f"  {make_box_row('PROJECT', 'Veyra Sentinel — Atmospheric Forecast Reliability Layer', INNER_W)}")
print(f"  {make_box_row('PROBLEM', 'PS 26079 // Know When Weather Forecasts May Fail', INNER_W)}")
print(f"  {make_box_row('DATE', date_str, INNER_W)}")
print(f"  {make_box_bottom(INNER_W)}")
print()

# Services Card
print(f"  {make_box_top('Services & Endpoints', INNER_W)}")
print(f"  {make_box_row('BACKEND', 'http://127.0.0.1:8000  [FastAPI Predictive Engine]', INNER_W)}")
print(f"  {make_box_row('FRONTEND', 'http://127.0.0.1:5173  [React Sentinel Dashboard]', INNER_W)}")
print(f"  {make_box_row('DOCS', 'http://127.0.0.1:8000/docs [Swagger OpenAPI 3.1]', INNER_W)}")
print(f"  {make_box_bottom(INNER_W)}")
print()

# Motto & Color Dots
print(f"  {AMBER}Team HEXARK // Know When Forecasts May Fail.{RESET}")
print()
print("  \033[90m● \033[36m● \033[35m● \033[34m● \033[33m● \033[32m● \033[31m● \033[37m●\033[0m")
print()
