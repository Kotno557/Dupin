from lib.dupin_python_lib.dupin_core import DupinPathSniffer, DupinInfoSniffer, DupinLevelGrader, DupinVchainConnecter, database_init
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import sys
import sqlite3
from typing import List, Dict
import json

class SniffItem(BaseModel):
    target_url: str


app = FastAPI()

# 只是個根目錄，確保這裡還活著
@app.get('/')
async def root():
    return {"message": "Hello Dupin server Site, there is nothing."}


# 本地與目的地連線路徑探測
@app.get('/direct_path_check')
async def direct_path_check(url: str = '127.0.0.1'):
    sniffer = DupinLevelGrader(DupinInfoSniffer(DupinPathSniffer(url)).info_result)
    return {"info": sniffer.info_result, "level": sniffer.weight_result, "path_weight": sniffer.weight_sum}

# 本地與目的地連線路徑探測（VPN參與）
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
@app.post('/connect')
async def connect(target_ip):
    pass


# 輸出：斷線是否成功資訊
@app.get('/disconnect')
async def disconnect():
    pass


# 輸出：所有廠牌列表，包括國家資訊
@app.get('/brand_list')
async def get_brand_list():
    pass



if __name__ == "__main__":
    database_init()
    conn: sqlite3.Connection = sqlite3.connect('local_database.db')
    cur: sqlite3.Cursor = conn.cursor()
    uvicorn.run("dupin_server:app", host="localhost", port=8000, reload=True)