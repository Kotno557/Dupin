from lib.dupin_python_lib.dupin_core import DupinPathSniffer, DupinInfoSniffer, database_init
from fastapi import FastAPI
from typing import Dict, List, Union
import sqlite3
import socket
import uvicorn


def vpn_path_clean_info_sniff(target_url: str) -> Dict[int, int]:
    path_sniffer: DupinPathSniffer = DupinPathSniffer(target_url)
    info_sniffer: DupinInfoSniffer = DupinInfoSniffer(path_sniffer.sniff_result)
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