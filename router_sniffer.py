import socket
import sys
import json
import requests
import time
from scapy.all import *
from scapy.layers.inet import IP, ICMP, TCP, UDP


DEBUG_MOD = False
MAIN_TARGET = None


def packet_track(ttl, target_ip_address, test_count=3, wait_time=2):
    # 回傳可能的IP集合
    res = set()
    # 建立 ICMP 封包
    trace_type = [ICMP(), TCP(flags='S'), UDP()]
    for t in trace_type:
        packet = IP(dst=target_ip_address, ttl=ttl) / t
        for i in range(test_count):
            # 傳送封包並接收回傳的封包
            response_packet = sr1(packet, verbose=False, timeout=wait_time)
            # 檢查是否有回傳的封包
            if response_packet is not None:
                # 印出回傳的封包資訊
                res.add(response_packet.getlayer(IP).src)
    if DEBUG_MOD:
        print(f'TTL {ttl} 為封包探測找到的結果 {list(res)} (只是猜測)')

    return list(res) if len(res) != 0 else None


def snmp_helper(trace_data):
    # 儲存 TTL 與 IP 位址的對應關係
    ttl_history = {}
    # 針對每一條路徑追蹤資料進行處理
    for flow_id in trace_data['flows']:
        flow = trace_data['flows'][flow_id]
        if DEBUG_MOD:
            print(f'--{flow_id}--')

        # 針對每一個跳躍回應進行處理
        for hop_response_id in range(0, len(flow)):
            ttl = hop_response_id+1
            receive_ip = None if not flow[hop_response_id]['received'] else flow[hop_response_id]['received']['ip']['src']
            # 如果沒有回應，則嘗試從 TTL 對應的 IP 位址紀錄中取得結果
            # 目前先不開紀錄，確保封包探測的準確率提高
            if receive_ip == None:
                # if ttl in ttl_history:
                #     trace_data['flows'][flow_id][hop_response_id]=ttl_history[ttl]
                # else:
                #     trace_data['flows'][flow_id][hop_response_id]=packet_track(ttl, MAIN_TARGET)
                trace_data['flows'][flow_id][hop_response_id] = None
            # 如果有回應，則直接將 IP 位址紀錄到路徑追蹤資料中
            else:
                temp = trace_data['flows'][flow_id][hop_response_id]['received']['ip']['src']
                trace_data['flows'][flow_id][hop_response_id] = temp
                if DEBUG_MOD:
                    print(f'TTL {ttl} 為 Dublin-traceroute 找到的結果為 {temp}')
    if DEBUG_MOD:
        print(trace_data)
    return trace_data


def run_dublin_traceroute():
    # 執行 Dublin-traceroute
    print(f'Executing Dublin-traceroute on {MAIN_TARGET}...', end='')
    os.system(f'dublin-traceroute -n 5 {MAIN_TARGET} > /dev/null')
    # 讀取路徑追蹤資料
    with open('trace.json', 'r') as f:
        trace_data = json.load(f)
        print('Done')
        return trace_data


def check_argv():
    # 檢查命令列參數是否正確
    if len(sys.argv) != 2:
        print(f'Usage: python router_sniffer.py url\n\n命令列參數設定不正確。')
    else:
        try:
            # 將參數轉換為 IP 位址
            target_ip_address = socket.gethostbyname(sys.argv[1])
            return target_ip_address
        except socket.gaierror:
            # 如果無法轉換，則顯示錯誤訊息
            print(f'Usage: python router_sniffer.py url\n\n網址格式不正確或是找不到該網址的 IP 位址。')


def main(ip):
    global MAIN_TARGET
    MAIN_TARGET = ip
    myip = requests.get(
        'https://api.bigdatacloud.net/data/client-ip').json()['ipString']
    # 從命令列參數檢查目標 IP 位址
    with open('local_database.json', 'r') as file:
        db = json.load(file)
        file.close()

    if (myip in db) and (MAIN_TARGET in db[myip]['path_record']) and (time.time()-db[myip]['path_record'][MAIN_TARGET]['time'] < 86400):
        with open('trace_optimized.json', 'w') as f:
            f.write(db[myip]['path_record'][MAIN_TARGET]['path'])
        print("By database record.")
    else:
        # 執行 Dublin Traceroute，取得路徑追蹤資料
        trace_data = run_dublin_traceroute()
        # 透過 SNMP 協助最佳化路徑追蹤資料
        trace_data_after_snmp_asistance = snmp_helper(trace_data)
        # 將最佳化後的路徑追蹤資料寫入 JSON 檔案
        with open('trace_optimized.json', 'w') as f:
            f.write(json.dumps(trace_data_after_snmp_asistance))
            f.close()

        if myip not in db:
            db[myip] = {'path_record': {MAIN_TARGET: {'time': time.time(), 'path': json.dumps(
                trace_data_after_snmp_asistance)}}, 'privete_node': {}, 'result': {}}

        with open('local_database.json', 'w') as f:
            f.write(json.dumps(db))
            f.close()

    # 印出完成訊息
    print('File saved in ./trace_optimized.json')


if __name__ == '__main__':
    main('8.8.8.8')
