from lib.dupin_python_lib.dupin_core import DupinPathSniffer, DupinInfoSniffer, DupinLevelGrader, database_init
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
    # path_sniffer.sniff_result : List[str] = [ip for ip in path_sniffer if ipaddress.IPv4Address(ip) not in ip_network]
    info_sniffer: DupinInfoSniffer = DupinInfoSniffer(path_sniffer)
    return info_sniffer.info_result



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
    uvicorn.run("vpn_node_dupin:app", host="0.0.0.0", port=8000, reload=True)