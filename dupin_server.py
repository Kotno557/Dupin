from lib.dupin_python_lib.dupin_core import DupinPathSniffer, DupinInfoSniffer, DupinLevelGrader, DupinVchainConnecter, database_init
from fastapi import FastAPI
from pydantic import BaseModel
import sys

class SniffItem(BaseModel):
    target_url: str

class SniffItem(BaseModel):
    target_url: str


app = FastAPI()

# 只是個根目錄，確保這裡還活著
@app.get('/')
async def root():
    return {"message": "Hello Dupin server Site, there is nothing."}


# 輸入：
# 1. 乾淨表檔案位置 String
# 2. VPN表檔案位置 String
# 3. 權重檔案位置 String 
# 4. 目的端url String
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
@app.get('')
async def something():
    pass



if __name__ == "__main__":
    database_init()
    conn: sqlite3.Connection = sqlite3.connect('local_database.db')
    cur: sqlite3.Cursor = conn.cursor()
    uvicorn.run("vpn_node_dupin:app", host="localhost", port=8000, reload=True)