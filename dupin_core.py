from typing import IO, Dict, Set, List, Tuple, Any
import requests
import socket
import json
import time
import sqlite3
import os


class DupinPathSniff:
    def __init__(self, targit_url: str) -> None:
        # init ip
        self.my_public_ip: str = requests.get('https://api.bigdatacloud.net/data/client-ip').json()['ipString']
        self.targit_ip: str = socket.gethostbyname(targit_url)

        # init database and history file
        self._local_database: sqlite3.Connection = sqlite3.connect('local_database.db')
        self._local_database_cur: sqlite3.Cursor = self._local_database.cursor()
        self.sniff_result: List[str]

        # use database then check result is already in it
        if self._check_path_history_exsist() == False: # if path_history_exsist will check db and load to sniff_result
            self.sniff_result = self._get_traceroute_result()
            self._save_sniff_result_to_local_database_and_result_json()
            
        self._local_database.commit()
        self._local_database.close()
        return 
            
    def _check_path_history_exsist(self) -> bool:
        self._local_database_cur.execute("SELECT * FROM path_record WHERE target_ip=?", (self.targit_ip,))
        results: List[Tuple[str]] = self._local_database_cur.fetchall()
        if len(results) < 1:
            return False
        
        if (time.time() - results[0][2] < 86400):
            self.sniff_result = json.loads(results[0][1])
            return True

        return False
    
    def _save_sniff_result_to_local_database_and_result_json(self) -> None:
        self._local_database_cur.execute("INSERT OR REPLACE INTO path_record (target_ip, path, last_update_time) VALUES (?, ?, ?)", (self.targit_ip, json.dumps(self.sniff_result), time.time(),))
        
    def _get_traceroute_result(self) -> List[str]:
        # declare vareable 
        traceroute_result: List[List[str]] = []

        # run dublin-traceroute
        os.system(f'sudo dublin-traceroute -n 5 {self.targit_ip} > /dev/null')

        # get result from trace.json
        trace_data: Set[str] = set()
        with open('trace.json', 'r') as dublin_result_json:
            dublin_result_json = json.load(dublin_result_json)
            # parse ip
            for i in dublin_result_json['flows']:
                for j in dublin_result_json['flows'][i]:
                    if j['received'] != None:
                        trace_data.add(j['received']['ip']['src'])
        return list(trace_data)
        
        

class DupinCleanSniff:
    def __init__(self, target_ip: str, clean_table: str = "local_database.db") -> None:
        pass

test = DupinPathSniff('8.8.8.8')
print(test.sniff_result)