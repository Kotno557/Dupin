from lib.dupin_python_lib.dupin_core import DupinPathSniffer, DupinInfoSniffer, database_init
from fastapi import FastAPI
from typing import Dict, List, Union
import sqlite3
import socket
import ipaddress
import uvicorn


VPN_NAT_ADDRESS = ipaddress.IPv4Network("104.44.0.0/16")

def vpn_path_clean_info_sniff(target_url: str) -> Dict[int, int]:
    path_sniffer: DupinPathSniffer = DupinPathSniffer(target_url)
    # ▼這邊先不要用ISP供應商NAT篩選判斷
    temp = []
    for ip in path_sniffer.sniff_result:
        if ipaddress.IPv4Address(ip) not in VPN_NAT_ADDRESS:
            temp.append(ip)
    path_sniffer.sniff_result : List[str] = temp #開啟VPN內部節點忽略
    info_sniffer: DupinInfoSniffer = DupinInfoSniffer(path_sniffer)
    return {"path": info_sniffer.info_result, "target_ip": path_sniffer.targit_ip, "draw_path": path_sniffer.draw_path}



app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello Dupin Vpn Search Site"}

@app.get('/sniff/{target_ip}')
async def sniff_path(target_ip):
    try:
        return vpn_path_clean_info_sniff(target_ip)
    except socket.gaierror:
        return {"message": "IP address or URL not valid"}

if __name__ == "__main__":
    database_init()
    conn: sqlite3.Connection = sqlite3.connect('local_database.db')
    cur: sqlite3.Cursor = conn.cursor()
    uvicorn.run("dupin_vpn_server:app", host="0.0.0.0", port=8000, reload=True)