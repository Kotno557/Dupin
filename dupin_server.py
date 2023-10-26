from lib.dupin_python_lib.dupin_core import DupinPathSniffer, DupinInfoSniffer, DupinLevelGrader, DupinVchainConnecter, database_init
from lib.dupin_python_lib.dupin_tool import get_ip_coord, ip_level_convert
from fastapi import FastAPI, Query, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import sys
import sqlite3
from typing import List, Dict
import json
import requests
import subprocess
import time 

CLEAN_TABLE = {}
VPN_TABLE = {}
WEIGHT_TABLE = {}



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 只是個根目錄，確保這裡還活著
@app.get('/')
async def root():
    return {"info": "The site is alive Uwu"}

@app.post('/upload/{file_type}')
async def upload(file_type: int, file: UploadFile):
    global CLEAN_TABLE
    global VPN_TABLE
    global WEIGHT_TABLE
    try:
        file_content = await file.read()
        json_data = json.loads(file_content)
        if file_type == 1:
            CLEAN_TABLE = json_data
        if file_type == 2:
            VPN_TABLE = json_data
        if file_type == 3:
            WEIGHT_TABLE = json_data
        print(CLEAN_TABLE, VPN_TABLE, WEIGHT_TABLE)
        return {"data": json_data}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)
    

# 本地與目的地連線路徑探測
@app.get('/direct_path_check')
async def direct_path_check(url: str = 'goodinfo.tw'):
    path_node = DupinPathSniffer(url)
    target_ip = path_node.targit_ip
    target_coord: List[float, float] = get_ip_coord(target_ip)
    sniffer = DupinLevelGrader(DupinInfoSniffer(path_node).info_result, CLEAN_TABLE, WEIGHT_TABLE)
    res: Dict = {
        "target": {"ip": target_ip, "coord": target_coord}, 
        "node": {}, 
        "summary": {ip_level_convert(i): sniffer.path_clean_result[i] for i in range(-1, 4)},
        "weight": sniffer.weight_sum
        }
    for key, value in sniffer.info_result.items():
        res["node"][key] = {
            "isp": value[0],
            "hdm": value[1], 
            "os": value[2], 
            "level": ip_level_convert(sniffer.weight_result[key]), 
            "single_weight": sniffer._weight_table[sniffer.weight_result[key]]
        }

    return res

# 本地與目的地連線路徑探測（VPN參與）
# TO DO: 還要有推薦路徑資訊!!!
@app.get('/vpn_path_check')
async def vpn_path_check(target_ip: str = '127.0.0.1', 
vpn_file_path: str = 'User-defined files/vpn/default_vpn_table.json',
clean_table_path: str = 'User-defined files/clean/default_clean_table.json',
weight_table_path: str = 'User-defined files/weight/default_node_weight_table.json'):

    with open(vpn_file_path, 'r') as vpn_file:
        vpn_list: List[Dict[str, str]] = json.load(vpn_file)
    
    res: Dict = {"localhost": {}, target_ip: {}}
    for i in range(0, len(vpn_list)):
        now_ip: str = vpn_list[i]["ip"]
        res[now_ip] = {}
        for j in range(i + 1, len(vpn_list) + 1):
            next_ip: str = vpn_list[j]["ip"] if j < len(vpn_list) else target_ip
            while True:
                try:
                    sniffer: DupinLevelGrader = DupinLevelGrader(requests.get(f'http://{now_ip}:8000/sniff/{next_ip}', timeout = 40).json(), clean_table_path, weight_table_path)
                    break
                except Exception as e:
                    print(e)
                    continue
            res[now_ip][next_ip] = {"info": sniffer.info_result, "level": sniffer.weight_result, "path_weight": sniffer.weight_sum}
            res[next_ip][now_ip] = res[now_ip][next_ip]
    
    for i in range(0, len(vpn_list) + 1):
        next_ip: str = vpn_list[i]["ip"] if i < len(vpn_list) else target_ip
        sniffer: DupinLevelGrader = DupinLevelGrader(DupinInfoSniffer(DupinPathSniffer(next_ip)).info_result, clean_table_path, weight_table_path)
        res["localhost"][next_ip] = {"info": sniffer.info_result, "level": sniffer.weight_result, "path_weight": sniffer.weight_sum}
        res[next_ip]["localhost"] = res["localhost"][next_ip]

    return res



# 輸入：
# 1. 連線順序
# 輸出：
# 1. 本地到目的端的傳輸路徑、個節點設備資訊與整條路的權重 JSON
# 2. VPN節點介入的所有兩兩路徑的傳輸路徑個節點設備資訊與各路徑的權重, 還有，最小權重路徑（最乾淨路徑）資訊 JSON
@app.get('/make_connect_file')
async def make_connect_file(target_ip, vpn_file_path: str = 'User-defined files/vpn/default_vpn_table.json', path_list: List[str] = Query(None)):
    with open(vpn_file_path, 'r') as vpn_file:
        vpn_list: List[Dict[str, str]] = json.load(vpn_file)
    
    for i in range(0, len(path_list)):
        for item in vpn_list:
            if item["ip"] == path_list[i]:
                path_list[i] = item["ovpn_path"]
    
    vpn_variable_setting: str = '#!/bin/bash\n'
    num = 1
    for i in range(len(path_list) - 1, -1, -1):
        vpn_variable_setting += f"config[{num}]={path_list[i]}\n"
        num += 1
    connect_sh_file_name: str = f'{time.strftime("%Y%m%d-%H%M%S")}_{target_ip.replace(".", "_")}_connect.sh'
    with open('lib/VPN-Chain/vpnchain_template.txt') as template, open(f'lib/VPN-Chain/{connect_sh_file_name}', 'w') as connect_file:
        connect_file.write(vpn_variable_setting)
        for line in template:
            connect_file.write(line)

    subprocess.call(f'chmod 777 ./{connect_sh_file_name}', shell=True, cwd='lib/VPN-Chain')
    return {"msg": "ok", "file": connect_sh_file_name}


@app.get('/connect')
async def connect(file_name: str = None):
    # 因為我們確保連線檔案都是在上一個函式中建立的，所以這邊用檔名即可
    try:
        subprocess.call(f'./{file_name}', shell=True, cwd='lib/VPN-Chain')
    except Exception as e:
        print(e+"!!!!")
    
    return {"msg": "ok"}


# 輸出：斷線是否成功資訊
@app.get('/disconnect')
async def disconnect():
    try:
        subprocess.call(f'./disconnect.sh', shell=True, cwd='lib/VPN-Chain')
    except Exception as e:
        print(e)
        return {"error": str(e)}
    return {"msg": "ok"}


# 輸出：所有廠牌列表，包括國家資訊
@app.get('/brand_list')
async def get_brand_list():
    pass



if __name__ == "__main__":
    database_init()
    conn: sqlite3.Connection = sqlite3.connect('local_database.db')
    cur: sqlite3.Cursor = conn.cursor()
    uvicorn.run("dupin_server:app", host="localhost", port=8000, reload=True)