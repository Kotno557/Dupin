import router_security
import router_sniffer
import socket
import time 
import requests
import json

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def check_argv(href):
    try:
        # 將參數轉換為 IP 位址
        target_ip_address = socket.gethostbyname(href)
        return target_ip_address
    except socket.gaierror:
        # 如果無法轉換，則顯示錯誤訊息
        print(f'Usage: python router_sniffer.py url\n\n網址格式不正確或是找不到該網址的 IP 位址。')

def load_node():
    s = set()
    with open('trace_optimized.json') as file:
        l = json.load(file)
        for i in l['flows']:
            for j in l['flows'][i]:
                if j != None:
                    s.add(j)
    return list(s)

def sort_by_level(arr):
    sorted_arr = sorted(arr, key=lambda x: x['level'])
    return sorted_arr

def main():
    ip = check_argv('baidu.com')
    with open('local_database.json', 'r') as file:
        db = json.load(file)
        file.close()
    myip = requests.get('https://api.bigdatacloud.net/data/client-ip').json()['ipString']

    # 等VPN探測完成結果
    # if (myip in db) and (ip in db[myip]['path_record']) and (time.time()-db[myip]['path_record'][ip]['time'] < 86400):
    if False:
        vpn_S = db[myip]['path_record'][ip]['result']['s']
        vpn_E = db[myip]['path_record'][ip]['result']['e']
        script = db[myip]['path_record'][ip]['result']['script_name']
        clean = db[myip]['path_record'][ip]['result']['clean_level']
        # print(f'The router path clean level from here to {ip} found from database in one day history is: {bcolors.BOLD}{router_security.CLEAN_LEVEL[int(search["clean_level"])]}{bcolors.ENDC}')
    else:
        print('Doing router_sniffer ... ')
        router_sniffer.main(ip)
        nodes = load_node()
        nodes.append(ip)
        path_level = []
        print('Doing router_security ... ')
        for i in nodes:
            print(f'Scanning {i}...')
            path_level.append({'ip':i,'level':router_security.main(i)})
        path_level = sort_by_level(path_level)
        summary = {-1:0,0:0,1:0,2:0,3:0}
        for i in path_level:
            summary[i['level']]+=1
        print(f'Summary: HIGH Level: {bcolors.OKBLUE}{summary[3]}{bcolors.ENDC} node, PASSABLE Level: {bcolors.OKGREEN}{summary[2]}{bcolors.ENDC} node, LOW Level: {bcolors.WARNING}{summary[1]}{bcolors.ENDC} node, UNKNOW Level: {bcolors.HEADER }{summary[0]}{bcolors.ENDC} node, DANGER Level: {bcolors.FAIL}{summary[-1]}{bcolors.ENDC} node.')

        print(f'The total router path clean level from here to {ip} is: "{router_security.CLEAN_LEVEL[path_level[0]["level"]]}"')




if __name__ == '__main__':
    main()