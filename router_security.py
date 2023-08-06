import requests
import sys
import os
import json
import time
import nmap
from functools import reduce


DEBUG_MOD = False
SECURITY_FILE = 'default_cleannetwork.json'
LOCAL_RECORD_FILE = 'local_ip_record.json'
INFO = None
CLEAN_LEVEL = {3: 'HIGH', 2: 'PASSABLE', 1: 'LOW', 0: 'UNKNOW', -1: 'DANGER'}
MIN_TIME = 86400

nm = nmap.PortScanner()


def get_router_telecom():
    global INFO
    # print(INFO)
    if INFO['asn'] == None:
        return INFO['company']['name']
    else:
        return INFO['asn']['org']



def get_router_brand(ip):
    nm = nmap.PortScanner()
    try:
        nm.scan(hosts=ip, arguments='-sU -sV -p 161 --script=snmp-info', timeout=10)
        for info in nm[ip]['udp'][161]['script']['snmp-info'].split('\n '):
            if 'enterprise: ' in info:
                brand = info[info.find('enterprise: ')+len('enterprise: '):]
        # RESULT['snmp'] = {'name':nm[IP]['udp'][161]['product'],'vendor':brand}
        return '_S '+brand

    except (nmap.nmap.PortScannerTimeout, KeyError) as e:
        print('SNMP detect Failed')
        try:
            nm.scan(hosts=ip, arguments='-O', timeout=20)
            # RESULT['os'] = {'name':nm[IP]['osmatch'][0]['name'],'vendor':nm[IP]['osmatch'][0]['osclass'][0]['vendor']}
            return '_O '+nm[ip]['osmatch'][0]['osclass'][0]['vendor']
        except:
            print('Os detect result None.')
            return None


def security_level_analysis(isp_name, enterprise_name):
    with open(SECURITY_FILE) as file_input:
        clean_network_list = json.load(file_input)
    # if DEBUG_MOD:
    #     print(clean_network_list)
    if isp_name in clean_network_list['isp']['clean']:
        if enterprise_name == None:
            return 1
        if enterprise_name[3:] in clean_network_list['hdm']['clean']:
            if '_O' in enterprise_name:
                return 2
            if '_S' in enterprise_name:
                return 3
        if enterprise_name[3:] in clean_network_list['hdm']['unclean']:
            return -1
        else:
            return 1

    elif isp_name in clean_network_list['isp']['unclean']:
        return -1
    else:
        if enterprise_name == None:
            return 0
        if enterprise_name[3:] in clean_network_list['hdm']['clean']:
            if '_O' in enterprise_name:
                return 1
            if '_S' in enterprise_name:
                return 2
        if enterprise_name[3:] in clean_network_list['hdm']['unclean']:
            return -1
        else:
            return 0


def ip_into_int(ip):
    return reduce(lambda x, y: (x << 8)+y, map(int, ip.split('.')))


def is_internal_ip(ip):
    ip = ip_into_int(ip)
    net_a = ip_into_int('10.255.255.255') >> 24
    net_b = ip_into_int('172.31.255.255') >> 20
    net_c = ip_into_int('192.168.255.255') >> 16
    return ip >> 24 == net_a or ip >> 20 == net_b or ip >> 16 == net_c


def main(ip):
    global INFO
    if is_internal_ip(ip):
        myip = requests.get(
            'https://api.bigdatacloud.net/data/client-ip').json()['ipString']
        telecom = requests.get(
            f'https://api.incolumitas.com/?q={myip}').json()['asn']['org']
        with open('local_database.json', 'r') as file:
            db = json.load(file)
            file.close()

        if (myip in db) and (ip in db[myip]['privete_node']) and (time.time()-db[myip]['privete_node'][ip]['time'] < MIN_TIME):
            brand = db[myip]['privete_node'][ip]['brand']
            telecom = db[myip]['privete_node'][ip]['telecom']
            print('Get record from local database')
        else:
            brand = get_router_brand(ip)
            db[myip]['privete_node'][ip] = {
                'time': time.time(), 'brand': brand, 'telecom': telecom}

            with open('local_database.json', 'w') as file:
                file.write(json.dumps(db))
                file.close()
    else:
        search = requests.get(f'http://144.24.84.156:5000/node?ip={ip}').json()
        if search != None and time.time()-float(search['time']) < MIN_TIME:
            print('by database record')
            telecom = search['telecom']
            brand = search['brand']
        else:
            INFO = requests.get(f'https://api.incolumitas.com/?q={ip}').json()
            if DEBUG_MOD:
                print(INFO)
            telecom = get_router_telecom()
            brand = get_router_brand(ip)
            requests.post(f'http://144.24.84.156:5000/node', data={
                          'ip': ip, 'time': str(time.time()), 'brand': brand, 'telecom': telecom})
    level = security_level_analysis(telecom, brand)
    print(
        f'Telecom: "{telecom}", Brand: "{brand}", Level: "{CLEAN_LEVEL[level]}"')
    return level


if __name__ == '__main__':
    main('220.128.13.129')
