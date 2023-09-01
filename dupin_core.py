from typing import IO, Dict, Set, List, Tuple, Any, Union
import requests
import socket
import json
import time
import sqlite3
import os

import ipaddress
import nmap

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
            print(f'get {self.targit_ip} path from DB')
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
        os.remove('trace.json')

        return list(trace_data)
        
        

class DupinCleanSniffer:
    def __init__(self, travel_path: List[str], clean_table_name: str = 'default_table.json') -> None:
        # this is a variable to check detail clean level result
        self.clean_level_statistics: Dict[int ,int]
        self.detail_clean_level_list: Dict[str, Tuple[str, str, str, int]] = {}
        self._clean_table_name: str = clean_table_name

        # init database
        self._local_database: sqlite3.Connection = sqlite3.connect('local_database.db')
        self._local_database_cur: sqlite3.Cursor = self._local_database.cursor()

        # return variable and clean table define
        self.path_clean_result: Dict[int, List[str]] = {-1: [], 0: [], 1: [], 2: [], 3: []}
        with open(clean_table_name, 'r') as clean_table_json:
            self._clean_table: Dict = json.load(clean_table_json)

        # sniff every ip address
        for ip in travel_path:
            self._sniff_ip_clean_level(ip)

        # statistics result
        self._get_clean_statistics()

        # write and close database
        self._local_database.commit()
        self._local_database.close()

    def _sniff_ip_clean_level(self, ip: str) -> None:
        # variable define
        is_address_private: bool = self._check_private_ip(ip)
        isp: str = ''
        hdm: str
        os: str
        get_by_database: bool = False
        
        # first check for database
        self._local_database_cur.execute('SELECT * FROM clean_record WHERE target_ip=? AND table_name=?', (ip, self._clean_table_name, ))
        search_result: List[Tuple[Union[str, float]]] =  self._local_database_cur.fetchall()
        if len(search_result) > 0 and time.time() - search_result[0][2] < 604800:
            print(f'get {ip} information from DB')
            # data available in database 
            isp = search_result[0][3]
            hdm = search_result[0][4]
            os = search_result[0][5]
            get_by_database = True
        else:
            # find isp
            if is_address_private == False:
                lookup_info: Dict = requests.get(f'https://api.incolumitas.com/?q={ip}').json()
                isp = lookup_info['company']['name'] if lookup_info['asn'] == None else lookup_info['asn']['org']
            
            # find hdm
            hdm = self._sniff_ip_hdm(ip)

            # find os 
            os = self._sniff_ip_os(ip)

        # find clean level by isp, hdm, os
        level: int = self._count_clean_level(isp, hdm, os)

        # save result to detail_clean_level_list
        self.detail_clean_level_list[(ip, self._clean_table_name)] = (isp, hdm, os, level)

        # save result to path_clean_result
        self.path_clean_result[level].append(ip)

        # save result to sqlite
        """
        對於公網IP 全部存在 公共的資料庫上 (暫定，目前先存在本地端資料庫即可)
        if self._clean_table_name == 'default_table.json':
            # if this is use default table
            pass
        """
        if not get_by_database:
            self._local_database_cur.execute('INSERT OR REPLACE INTO clean_record (target_ip, table_name, last_update_time, isp, hdm, os) VALUES (?, ?, ?, ?, ?, ?)', (ip, self._clean_table_name, time.time(), isp, hdm, os,))


    def _check_private_ip(self, ip: str) -> bool:
        ip_obj: Union[ipaddress.IPv4Address, ipaddress.IPv6Address] = ipaddress.ip_address(ip)
        return ip_obj.is_private
    def _sniff_ip_hdm(self, ip: str) -> str:
        # using nmap --script=snmp-info get hdm
        nm: nmap.PortScanner = nmap.PortScanner()
        try:
            nm.scan(hosts=ip, arguments='-sU -sV -p 161 --script=snmp-info', timeout=10, sudo=True)
            for info in nm[ip]['udp'][161]['script']['snmp-info'].split('\n '):
                if 'enterprise: ' in info:
                    brand = info[info.find('enterprise: ')+len('enterprise: '):]
            return brand
        except:
            # print('SNMP detect Failed')
            return ''
    
    def _sniff_ip_os(self, ip: str) -> str:
        # using nmap -O get os
        nm: nmap.PortScanner = nmap.PortScanner()
        try:
            nm.scan(hosts=ip, arguments='-O', timeout=20, sudo=True)
            return nm[ip]['osmatch'][0]['osclass'][0]['vendor']
        except:
            # print('OS detect Failed')
            return ''
    
    def _count_clean_level(self, isp: str, hdm: str, os: str) -> int:
        # isp_level -1 = dirty; 0 = unknow; 1 = clean 
        isp_level: int

        # set isp_level
        if isp in self._clean_table['isp']['clean']:
            isp_level = 1
        elif isp in self._clean_table['isp']['unclean']:
            return -1
        else:
            isp_level = 0

        # level count
        if hdm in self._clean_table['hdm']['clean']:
            return 3 if isp_level == 1 else 2
        elif os in self._clean_table['hdm']['clean']:
            return 2 if isp_level == 1 else 1
        elif hdm or os in self._clean_table['hdm']['unclean']:
            return -1
        else:
            return 1 if isp_level == 1 else 0
    
    def _get_clean_statistics(self) -> None:
        # return result like {-1: 0, 0: 5, 1: 10, 2: 4, 3: 2}
        res_statistics: Dict[int, int] = {}
        for key, value in self.path_clean_result.items():
            res_statistics[key] = len(value)
        
        self.clean_level_statistics = res_statistics

        
            

# test code
# test = DupinPathSniff('dublin-traceroute.net')
# print(test.sniff_result)
# testClean = DupinCleanSniffer(test.sniff_result)
# print(testClean.clean_level_statistics)
# print(testClean.detail_clean_level_list)