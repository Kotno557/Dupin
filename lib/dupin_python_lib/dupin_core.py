from typing import IO, Dict, Set, List, Tuple, Any, Union
import requests
import socket
import json
import time
import sqlite3
import os

import ipaddress
import nmap

class DupinPathSniffer:
    def __init__(self, targit_url: str) -> None:
        # init ip
        self.my_public_ip: str = requests.get('https://api.bigdatacloud.net/data/client-ip').json()['ipString']
        self.targit_ip: str = socket.gethostbyname(targit_url)
        print(f'Sniffing {targit_url}({self.targit_ip})...')

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
            
    def _check_path_history_exsist(self) -> bool:
        self._local_database_cur.execute("SELECT * FROM path_record WHERE target_ip=?", (self.targit_ip,))
        results: List[Tuple[str]] = self._local_database_cur.fetchall()
        if len(results) < 1:
            return False
        
        if (time.time() - results[0][2] < 86400):
            self.sniff_result = json.loads(results[0][1])
            #print(f'get {self.targit_ip} path from DB')
            return True

        return False
    
    def _save_sniff_result_to_local_database_and_result_json(self) -> None:
        self._local_database_cur.execute("INSERT OR REPLACE INTO path_record (target_ip, path, last_update_time) VALUES (?, ?, ?)", (self.targit_ip, json.dumps(self.sniff_result), time.time(),))
        
    def _get_traceroute_result(self) -> List[str]:
        # declare vareable 
        traceroute_result: List[List[str]] = []

        # run dublin-traceroute
        os.system(f'sudo dublin-traceroute -n 5 {self.targit_ip} -b > /dev/null')

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
        
        
class DupinInfoSniffer:
    def __init__(self, path_sniffer: DupinPathSniffer) -> None:
        # define I/O variable
        travel_path: List[str] = path_sniffer.sniff_result
        self.info_result: Dict[str, Tuple[str, str, str]] = {}

        # init database
        self._local_database: sqlite3.Connection = sqlite3.connect('local_database.db')
        self._local_database_cur: sqlite3.Cursor = self._local_database.cursor()

        # sniff every ip address
        for ip in travel_path:
            self._sniff_ip_info(ip)

        # write and close database
        self._local_database.commit()
        self._local_database.close()

    def _sniff_ip_info(self, ip: str) -> None:
        # variable define
        is_address_private: bool = self._check_private_ip(ip)
        isp: str = ''
        hdm: str
        os: str
        get_by_database: bool = False
        
        # first check for database
        self._local_database_cur.execute('SELECT * FROM info_record WHERE target_ip=?', (ip,))
        search_result: List[Tuple[Union[str, float]]] =  self._local_database_cur.fetchall()
        if len(search_result) > 0 and time.time() - search_result[0][1] < 604800:
            #print(f'get {ip} information from DB')
            # data available in database 
            isp = search_result[0][2]
            hdm = search_result[0][3]
            os = search_result[0][4]
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


        # save result to info_result
        self.info_result[ip] = (isp, hdm, os)

        # save result to sqlite
        """
        對於公網IP 全部存在 公共的資料庫上 (暫定，目前先存在本地端資料庫即可)
        if self._clean_table_name == 'default_table.json':
            # if this is use default table
            pass
        """
        if not get_by_database:
            self._local_database_cur.execute('INSERT OR REPLACE INTO info_record (target_ip, last_update_time, isp, hdm, os) VALUES (?, ?, ?, ?, ?)', (ip, time.time(), isp, hdm, os,))


    def _check_private_ip(self, ip: str) -> bool:
        ip_obj: Union[ipaddress.IPv4Address, ipaddress.IPv6Address] = ipaddress.ip_address(ip)
        return ip_obj.is_private

    def _sniff_ip_hdm(self, ip: str) -> str:
        # using nmap --script=snmp-info get hdm
        nm: nmap.PortScanner = nmap.PortScanner()
        try:
            nm.scan(hosts=ip, arguments='-sU -sV -p 161 --script=snmp-info', timeout=15, sudo=True)
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
            nm.scan(hosts=ip, arguments='-O', timeout=40, sudo=True)
            return nm[ip]['osmatch'][0]['osclass'][0]['vendor']
        except:
            # print('OS detect Failed')
            return ''


class DupinLevelGrader:
    def __init__(self, info_sniffer: DupinInfoSniffer, clean_table_name: str = 'default_table.json') -> None:
        # return variable and clean table define
        self.path_clean_result: Dict[int, int] = {-1: 0, 0: 0, 1: 0, 2: 0, 3: 0}
        with open(clean_table_name, 'r') as clean_table_json:
            self._clean_table: Dict = json.load(clean_table_json)

        # grade every ip
        info_sniffer_result: Dict[str, Tuple[str, str, str]] = info_sniffer.info_result
        for isp, hdm, os in info_sniffer_result.values():
            self.path_clean_result[self._count_clean_level(isp, hdm, os)] += 1



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
            return 3 if isp_level == 1 else 1
        elif hdm or os in self._clean_table['hdm']['unclean']:
            return -1
        else:
            return 2 if isp_level == 1 else 0
        

def database_init():

    if os.path.isfile('local_database.db'):
        return 

    conn = sqlite3.connect('local_database.db')
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE info_record (
            target_ip TEXT PRIMARY KEY,
            last_update_time REAL,
            isp TEXT,
            hdm TEXT,
            os TEXT
        );
    """)
    conn.commit()

    cursor.execute("""
        CREATE TABLE path_record (
            target_ip TEXT PRIMARY KEY,
            path TEXT,
            last_update_time REAL
        );
    """)
    conn.commit()

    cursor.close()
    conn.close()