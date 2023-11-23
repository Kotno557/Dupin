from lib.dupin_python_lib.dupin_core import DupinPathSniffer, DupinInfoSniffer, DupinLevelGrader, DupinVchainConnecter, database_init
from lib.dupin_python_lib.dupin_tool import get_ip_coord, ip_level_convert, shortest_path, clean_table_parser
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
            CLEAN_TABLE = clean_table_parser(json_data)
            print("[INFO] dupin_server.upload: Upload CLEAN_TABLE")
        if file_type == 2:
            VPN_TABLE = json_data
            print("[INFO] dupin_server.upload: Upload VPN_TABLE")
        if file_type == 3:
            WEIGHT_TABLE = json_data
            print("[INFO] dupin_server.upload: Upload WEIGHT_TABLE")
        return {"data": json_data}
    except Exception as e:
        print(f"[ERROR] dupin_server.upload: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=400)
    

# 本地與目的地連線路徑探測
@app.get('/direct_path_check')
async def direct_path_check(url: str):
    path_node = DupinPathSniffer(url)
    target_ip = path_node.targit_ip
    target_coord: List[float, float] = get_ip_coord(target_ip)
    sniffer = DupinLevelGrader(DupinInfoSniffer(path_node).info_result, CLEAN_TABLE, WEIGHT_TABLE)
    res: Dict = {
        "target": {"ip": target_ip, "coord": target_coord}, 
        "node": {}, 
        "summary": {ip_level_convert(i): sniffer.path_clean_result[i] for i in range(-1, 4)},
        "weight": sniffer.weight_sum,
        "draw_path" : path_node.draw_path
    }
    for key, value in sniffer.info_result.items():
        res["node"][key] = {
            "isp": value[0],
            "hdm": value[1], 
            "os": value[2], 
            "country": value[3],
            "level": ip_level_convert(sniffer.weight_result[key]), 
            "single_weight": sniffer._weight_table[sniffer.weight_result[key]],
        }

    return res

# 本地與目的地連線路徑探測（VPN參與）
# TO DO: 還要有推薦路徑資訊!!!
@app.get('/vpn_path_check')
async def vpn_path_check(target_url: str):
    res: Dict = {"localhost": {}}

    vpn_table_keys = list(VPN_TABLE.keys())
    table_len = len(vpn_table_keys)
    sniffer: DupinLevelGrader = None
    for i in range(0, table_len):
        now_ip: str = vpn_table_keys[i]
        res[now_ip] = {}
        for j in range(i + 1, table_len + 1):
            next_ip: str = vpn_table_keys[j] if j < table_len else target_url
            while True:
                try:
                    path_sniffer = requests.get(f'http://{now_ip}:8000/sniff/{next_ip}', timeout = 40).json()
                    sniffer: DupinLevelGrader = DupinLevelGrader(path_sniffer["path"], CLEAN_TABLE, WEIGHT_TABLE)
                    break
                except Exception as e:
                    if e.__str__() == "Expecting value: line 1 column 1 (char 0)":
                        print("[ERROR] dupin_server.py.vpn_path_check: VPN server can not connect")
                        break
                    else:
                        print(f"[INFO] dupin_server.py.vpn_path_check: Waiting {now_ip} return resault")
                        continue
            res[now_ip][next_ip] = {
                "info": {},
                "level": sniffer.weight_result, 
                "path_weight": sniffer.weight_sum, 
                "target_ip": path_sniffer["target_ip"],
                "draw_path": path_sniffer["draw_path"]
            }
            for key, value in sniffer.info_result.items():
                res[now_ip][next_ip]["info"][key] = {
                    "isp": value[0],
                    "hdm": value[1], 
                    "os": value[2],
                    "country": value[3],
                    "level": ip_level_convert(sniffer.weight_result[key]), 
                    "single_weight": sniffer._weight_table[sniffer.weight_result[key]]
                }
            
    # for localhost
    for i in range(0, table_len + 1):
        next_ip: str = vpn_table_keys[i] if i < table_len else target_url
        path_sniffer = DupinPathSniffer(next_ip)
        sniffer: DupinLevelGrader = DupinLevelGrader(DupinInfoSniffer(path_sniffer).info_result, CLEAN_TABLE, WEIGHT_TABLE)
        res["localhost"][next_ip] = {
            "info": {}, 
            "level": sniffer.weight_result, 
            "path_weight": sniffer.weight_sum, 
            "target_ip": path_sniffer.targit_ip,
            "draw_path": path_sniffer.draw_path
        }
        for key, value in sniffer.info_result.items():
            res["localhost"][next_ip]["info"][key] = {
                "isp": value[0],
                "hdm": value[1], 
                "os": value[2], 
                "country": value[3],
                "level": ip_level_convert(sniffer.weight_result[key]), 
                "single_weight": sniffer._weight_table[sniffer.weight_result[key]],
                "draw_path": path_sniffer.draw_path
            }
            

    return {"res": res, "shortest_info": shortest_path(res, target_url)}



# 輸入：
# 1. 連線順序
# 輸出：
# 1. 本地到目的端的傳輸路徑、個節點設備資訊與整條路的權重 JSON
# 2. VPN節點介入的所有兩兩路徑的傳輸路徑個節點設備資訊與各路徑的權重, 還有，最小權重路徑（最乾淨路徑）資訊 JSON
@app.post('/connect')
async def connect(target_url: str, path_list: List[str]):
    ip_now: str = requests.get('https://checkip.amazonaws.com').text.strip()
    for i in range(0, len(path_list)):
        try:
            path_list[i] = VPN_TABLE[path_list[i]]["ovpn_path"]
        except KeyError:
            print("[ERROR] dupin_server.py:connect: Request IP of VPN not in VPN_TABLE")
            return {"mag": "ERROR"}
    
    vpn_variable_setting: str = '#!/bin/bash\n'
    num = 1
    for i in range(len(path_list) - 1, -1, -1):
        vpn_variable_setting += f"config[{num}]={path_list[i]}\n"
        num += 1
    print(f"target = {target_url}, from = {ip_now}, path = {path_list}, time = {time.strftime('%Y%m%d-%H%M%S')}")
    with open('lib/VPN-Chain/vpnchain_template.txt') as template, open(f'lib/VPN-Chain/connect.sh', 'w') as connect_file:
        connect_file.write(vpn_variable_setting)
        for line in template:
            connect_file.write(line)

    subprocess.call(f'sudo chmod 777 ./connect.sh', shell=True, cwd='lib/VPN-Chain')

    try:
        subprocess.call(f'sudo ./connect.sh', shell=True, cwd='lib/VPN-Chain')
    except Exception as e:
        print(e+"!!!!")
    
    return {"msg": "ok"}


# 輸出：斷線是否成功資訊
@app.get('/disconnect')
async def disconnect():
    try:
        subprocess.call(f'sudo ./disconnect.sh', shell=True, cwd='lib/VPN-Chain')
    except Exception as e:
        print(e)
        return {"error": str(e)}
    return {"msg": "ok"}


# 輸出：所有廠牌列表，包括國家資訊
@app.get('/brand_list')
async def brand_list():
    with open('lib/dupin_python_lib/cleaTable.json','r') as table:
        res = json.load(table)

    return res

@app.get('/ip')
async def ip():
    ip: str = requests.get('https://checkip.amazonaws.com').text.strip()
    return {"ip": ip}

@app.post('/save_history')
async def save_history(history_data: Dict):
    with open('lib/dupin_python_lib/history.json', 'w') as table:
        json.dump(history_data, table, indent=4)

    return {"msg":"success"}

if __name__ == "__main__":
    database_init()
    conn: sqlite3.Connection = sqlite3.connect('local_database.db')
    cur: sqlite3.Cursor = conn.cursor()
    uvicorn.run("dupin_server:app", host="localhost", port=8000, reload=True)