from typing import IO, Dict, Set, List, Tuple, Any, Union
from lib.dupin_python_lib.dupin_tool import get_ip_coord
from datetime import datetime
import requests
import socket
import json
import time
import sqlite3
import os
import subprocess
import ipaddress
import nmap
import math
import networkx 

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
        self.draw_path: List[List[float]]

        # use database then check result is already in it
        if self._check_path_history_exsist() == False: # if path_history_exsist then check db and load to sniff_result
            self.sniff_result = self._get_traceroute_result()
            self._save_sniff_result_to_local_database_and_result_json()
            
        self._local_database.commit()
        self._local_database.close() 

            
    def _check_path_history_exsist(self) -> bool:
        self._local_database_cur.execute("SELECT * FROM path_record WHERE target_ip=? AND start_ip=?", (self.targit_ip, self.my_public_ip,))
        results: List[Tuple[str]] = self._local_database_cur.fetchall()
        if len(results) < 1:
            return False
        
        if (time.time() - results[0][2] < math.inf):
            self.sniff_result = json.loads(results[0][1])
            self.draw_path = json.loads(results[0][4])
            print(f'get {self.targit_ip} path from DB')
            return True

        return False
    
    def _save_sniff_result_to_local_database_and_result_json(self) -> None:
        self._local_database_cur.execute("INSERT OR REPLACE INTO path_record (target_ip, path, last_update_time, start_ip, draw_path ) VALUES (?, ?, ?, ?, ?)", (self.targit_ip, json.dumps(self.sniff_result), time.time(), self.my_public_ip, json.dumps(self.draw_path)))
        
    def _get_traceroute_result(self) -> List[str]:

        # run dublin-traceroute
        os.system(f'sudo dublin-traceroute -n 3 {self.targit_ip} -b > /dev/null')

        # get result from trace.json
        trace_data: Set[str] = set()

        
        path: List[List[str]] = [self.my_public_ip]
        with open('trace.json', 'r') as dublin_result_json:
            dublin_result_json = json.load(dublin_result_json)
            # parse ip
            for i in dublin_result_json['flows']:
                path.append([])
                for j in dublin_result_json['flows'][i]:
                    if j['received'] != None and j['received'] != self.targit_ip:
                        path[-1].append(j['received']['ip']['src'])
                        trace_data.add(j['received']['ip']['src'])
                print(path[-1])
        path.append(self.targit_ip)

        self.draw_path: List[Tuple[float]] = list(filter(lambda coord: coord != None, list(dict.fromkeys(map(get_ip_coord, max(path, key=len))))))
        self.draw_path = list(map(list, self.draw_path))
        
        print(self.draw_path)
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
        count = 1
        node_len = len(travel_path)
        for ip in travel_path:
            print(f'info scaning {ip} ({count}/{node_len})')
            count += 1
            self._sniff_ip_info(ip)

        # write and close database
        self._local_database.commit()
        self._local_database.close()

    def _sniff_ip_info(self, ip: str) -> None:
        # variable define
        isp: str = ''
        hdm: str
        os: str
        get_by_database: bool = False
        
        # first check for database
        self._local_database_cur.execute('SELECT * FROM info_record WHERE target_ip=?', (ip,))
        search_result: List[Tuple[Union[str, float]]] =  self._local_database_cur.fetchall()
        if len(search_result) > 0 and time.time() - search_result[0][1] < 10604800:
            print(f'get {ip} information from DB')
            # data available in database 
            isp = search_result[0][2]
            hdm = search_result[0][3]
            os = search_result[0][4]
            get_by_database = True
        else:
            # find isp
            lookup_info: Dict = requests.get(f'https://api.incolumitas.com/?q={ip}&key=c3624c8ec4978dec').json()
            isp = '' if ('company' not in lookup_info and 'asn' not in lookup_info) else lookup_info['company']['name'] if lookup_info['asn'] == None else lookup_info['asn']['org']
            
            # find hdm
            print("find hdm...")
            hdm = self._sniff_ip_hdm(ip)

            # find os 
            print("find os...")
            os = self._sniff_ip_os(ip)


        # save result to info_result
        self.info_result[ip] = (isp, hdm, os)

        # save result to sqlite
        """
        對於公網IP 全部存在 公共的資料庫上 (暫定，目前先存在本地端資料庫即可)
        if self._clean_table_name == 'default_clean_table.json':
            # if this is use default table
            pass
        """
        if not get_by_database:
            self._local_database_cur.execute('INSERT OR REPLACE INTO info_record (target_ip, last_update_time, isp, hdm, os) VALUES (?, ?, ?, ?, ?)', (ip, time.time(), isp, hdm, os,))
            self._local_database.commit()


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
        except Exception as e:
            print('SNMP detect Failed')
            print(e)
            return ''
    
    def _sniff_ip_os(self, ip: str) -> str:
        # using nmap -O get os
        nm: nmap.PortScanner = nmap.PortScanner()
        try:
            nm.scan(hosts=ip, arguments='-O --osscan-guess', timeout=40, sudo=True)
            return nm[ip]['osmatch'][0]['osclass'][0]['vendor']
        except Exception as e:
            print('OS detect Failed')
            print(e)
            return ''


class DupinLevelGrader:
    def __init__(self, info_sniffer_result: Dict[str, Tuple[str]],
     clean_table: Dict, weight_table: Dict) -> None:
        # return variable and clean table define
        self.info_result = info_sniffer_result
        self.weight_result = {}
        self.path_clean_result: Dict[int, int] = {-1: 0, 0: 0, 1: 0, 2: 0, 3: 0}
        self._clean_table: Dict = clean_table
        self._weight_table: Dict = weight_table
        # grade every ip
        self.weight_sum: int = 0 
        for ip in info_sniffer_result:
            clean_level = self._count_clean_level(info_sniffer_result[ip][0], info_sniffer_result[ip][1], info_sniffer_result[ip][2])
            self.path_clean_result[clean_level] += 1
            self.weight_result[ip] = str(clean_level)
            self.weight_sum += self._weight_table[str(clean_level)]
   



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
        

class DupinVchainConnecter:
    def __init__(self, target_url: str, vpn_table_name: str = 'User-defined files/vpn/default_vpn_table.json', clean_table_name: str = 'User-defined files/clean/default_clean_table.json', weight_table_name: str = 'User-defined files/weight/default_node_weight_table.json'):
        # temp and result variable define
        self.target_url: str = target_url
        self.target_ip: str = socket.gethostbyname(target_url)
        self.my_public_ip: str = requests.get('https://api.bigdatacloud.net/data/client-ip').json()['ipString']
        self.clean_table_name: str = clean_table_name
        with open(vpn_table_name) as vpn_node_json:
            self.vpn_table: List[Dict[str,str]] = json.load(vpn_node_json)
        with open(f'{weight_table_name}') as weight_table_json:
            self.weight_table: Dict[str, int] = json.load(weight_table_json)
        
        # create node-node weight graph
        self.node_weight_graph: List[List[int]] = self._create_path_graph()
        
        # using Dijkstra algo to find weight smallest path
        self.connection_path: List[int]
        self.connection_weight: int
        self.connection_weight, self.connection_path = self._dijkstra_shortest_path(self.node_weight_graph)

        # VPN-chaining with weight smallest path !active by user using DupinVchainConnecter.connect()
        
    def _create_path_graph(self) -> List[List[int]]:
        vpn_num: int = len(self.vpn_table) + 2 # local and target
        weight_result: List = [[math.inf for _ in range(vpn_num)] for _ in range(vpn_num)]
        for i in range(0, vpn_num - 1):
            for j in range(i + 1, vpn_num):
                while True:
                    try:
                        if i == 0:
                            if j != vpn_num - 1:
                                # weight_result[i][j] = j scan L
                                print(f'L -> {self.vpn_table[j - 1]["ip"]}')
                                #weight_result[i][j] = requests.get(f'http://{self.vpn_table[j - 1]["ip"]}:8000/sniff/{self.my_public_ip}', timeout = 40).json()
                                weight_result[i][j] = DupinInfoSniffer(DupinPathSniffer(self.vpn_table[j - 1]["ip"])).info_result
                            else:
                                # weight_result[i][j] = L scan D
                                print('L -> R')
                                weight_result[i][j] = DupinInfoSniffer(DupinPathSniffer(self.target_ip)).info_result
                        else:
                            if j != vpn_num - 1:
                                # weight_result[i][j] = i scan j
                                print(f'http://{self.vpn_table[i - 1]["ip"]}:8000/sniff/{self.vpn_table[j - 1]["ip"]}')
                                weight_result[i][j] = requests.get(f'http://{self.vpn_table[i - 1]["ip"]}:8000/sniff/{self.vpn_table[j - 1]["ip"]}', timeout = 40).json()
                            else:
                                # weight_result[i][j] = i scan D
                                print(f'http://{self.vpn_table[i - 1]["ip"]}:8000/sniff/{self.target_ip}')
                                weight_result[i][j] = requests.get(f'http://{self.vpn_table[i - 1]["ip"]}:8000/sniff/{self.target_ip}', timeout = 40).json()
                        break
                    except Exception as e:
                        print(e)
                        continue
                weight_result[i][j] = DupinLevelGrader(weight_result[i][j], clean_table_name=self.clean_table_name).path_clean_result
                weight_result[i][j] = self._wight_transform(weight_result[i][j])
                weight_result[j][i] = weight_result[i][j]

        print(weight_result)
        """
            [L, 1, 2, 3, 4, D]
            [X, V, V, V, V, V]
            [X, X, V, V, V, V]
            [X, X, X, V, V, V]
            [X, X, X, X, V, V]
            [X, X, X, X, X, V]
            [X, X, X, X, X, X]
        """

        return weight_result
        
    def _wight_transform(self, path_clean_result: Dict[int, int]) -> int:
        path_wight: int = 0
        for clean_level in path_clean_result:
            if path_clean_result[clean_level] > 0:
                path_wight += self.weight_table[str(clean_level)] * path_clean_result[clean_level]
        return path_wight

    def _dijkstra_shortest_path(self, weight_arr: List[List[int]]) -> Tuple[int, List[int]]:
        n: int = len(weight_arr)
        graph: networkx.Graph = networkx.Graph()

        for i in range(n):
            for j in range(i + 1, n):
                graph.add_edge(i, j, weight=weight_arr[i][j])

        shortest_path: List[int] = networkx.shortest_path(graph, source=0, target=n-1, weight='weight')
        shortest_distance: int = networkx.shortest_path_length(graph, source=0, target=n-1, weight='weight')

        return shortest_distance, shortest_path

    def connect(self) -> None:
        
        # variable and VPN server table define
        current_directory: str = os.getcwd()
        path_len: int = len(self.connection_path)
        
        # if path len <= 2, that means directly connection to target url is the best path
        if path_len <= 2:
            print("VPN connection does not provide a cleaner connection path; please connect directly to the target website")
            return
        
        # esle then generate vpnchain.sh file
        vpn_variable_setting: str = '#!/bin/bash\n'
        for i in range(1, path_len - 1):
            vpn_variable_setting += f'config[{path_len - 1 - i}]={current_directory}/vpn_node_ovpn_fold/{self.vpn_table[self.connection_path[i - 1]]["ovpn_name"]}\n'
        connect_sh_file_name: str = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{self.target_ip.replace(".", "_")}_connect.sh'
        with open('lib/VPN-Chain/vpnchain_template.txt') as template, open(f'lib/VPN-Chain/{connect_sh_file_name}', 'w') as connect_file:
            connect_file.write(vpn_variable_setting)
            for line in template:
                connect_file.write(line)
            
        # connect by connection.sh file
        subprocess.call(f'sudo chmod 777 ./{connect_sh_file_name}', shell=True, cwd='lib/VPN-Chain')
        subprocess.call(f'sudo ./{connect_sh_file_name}', shell=True, cwd='lib/VPN-Chain')

        

## Some Public fuction to asist all program

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
            target_ip TEXT,
            path TEXT,
            last_update_time REAL,
            start_ip TEXT,
            draw_path TEXT,
            UNIQUE(target_ip, start_ip)
        );
    """)
    conn.commit()

    cursor.close()
    conn.close()

def connect_by_vpn_sh_file(file_name: str) -> None:
    pass