import socket
import sys
import os
import json
import re
from scapy.all import *
from scapy.layers.inet import *


debug_mod = True


def display_usage(error_message: str):
    print(f'Usage: python router_sniffer.py url\n\n{error_message}')


def check_argv():
    if len(sys.argv) != 2:
        display_usage('Invalid parameter length configuration.')
    else:
        try:
            target_ip_address = socket.gethostbyname(sys.argv[1])
            return target_ip_address
        except socket.gaierror:
            display_usage(
                'Invalid URL format or the IP address for the URL cannot be found.')


def debug_mod_mode():
    sys.argv = ['', 'goodinfo.tw']


def run_dublin_traceroute(targetarget_ip_address: str):
    print(
        f'Now is running Dublin-traceroute for {targetarget_ip_address}...', end='')
    os.system(f'dublin-traceroute -n 35 {targetarget_ip_address} > /dev/null')
    trace_data = load_trace_data()
    print('Done')
    return trace_data


def load_trace_data():
    with open('trace.json', 'r') as f:
        trace_data = json.load(f)
    return trace_data


def packet_track(ttl, target_ip_address, test_count=3, wait_time=2, debug_mod=True):
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
                # if debug_mod:
                #     print(
                #         f'Find IP = {response_packet.getlayer(IP).src}. By {t}')

    return list(res) if not len(res) else None


def snmp_helper(trace_data):
    ttl_history = {}
    for flow_id in trace_data['flows']:
        flow = trace_data['flows'][flow_id]
        if debug_mod == True:
            print(f'--{flow_id}--')
        hop_response_id = 0
        while hop_response_id < len(flow):
            if flow[hop_response_id]['received'] == None:
                ttl = flow[hop_response_id]['sent']['ip']['ttl']
                if ttl in ttl_history:
                    flow[hop_response_id]['received']['ip']['src'] = ttl_history[ttl]
                else:
                    # flow[hop_response_id]['received'] = packet_track(
                    #     ttl, flow[hop_response_id]['sent']['ip']['dst'], debug_mod=debug_mod)
                    # ttl_history[str(ttl)] = flow[hop_response_id]['received']
                    pass
                print(packet_track(ttl, flow[hop_response_id]['sent']['ip']['dst'], debug_mod=debug_mod))

            else:
                temp = flow[hop_response_id]['received']['ip']['src']
                flow[hop_response_id]['received'] == temp
                print(temp)

            #print(flow[hop_response_id]['received'])
            hop_response_id += 1
            # if hop_response_id == len(flow)-1:
            #     break

            # if (flow[hop_response_id]['received'] == None) and (flow[hop_response_id]['received'] != None):
            #     last_ip_address = flow[hop_response_id-1]['received']['ip']['src']
            #     missing_hop_ttl = flow[hop_response_id]['sent']['ip']['ttl']
            #     if debug_mod == True:
            #         print(
            #             f'icmp package analysis {missing_hop_ttl}...', end='')
            #     else:
            #         snmpwn_result = icmp_track(missing_hop_ttl)
            #         if snmpwn_result!=[]:
            #             flow[hop_response_id+1]['received'] = {'id':{'src':snmpwn_result}}
            #         snmp_helper_history_table[] = snmpwn_result

            #     if debug_mod == True:
            #         print(f'SUCCESSFUL Find ip: {snmpwn_result}' if snmpwn_result==[] else 'FAIL')

            # hop_response_id += 1

    if debug_mod == True:
        print('snmp help over')


def icmp_track(ttl, target_ip_address, test_count=3, wait_time=3):
    # 建立 ICMP 封包
    icmp_packet = IP(dst=target_ip_address, ttl=ttl) / ICMP()

    # 傳送封包並接收回傳的封包
    response_packet = sr1(icmp_packet, verbose=False, timeout=wait_time)
    response_packet.show()
    # 檢查是否有回傳的封包
    if response_packet is not None:
        # 印出回傳的封包資訊
        return response_packet
    else:
        print("No response received.")


if __name__ == '__main__':
    if debug_mod:
        debug_mod_mode()
    target_ip_address = check_argv()
    trace_data = run_dublin_traceroute(target_ip_address)
    trace_data_after_snmp_asistance = snmp_helper(trace_data)
    with open('trace_optimized.json', 'w') as f:
        f.write(json.dumps(trace_data_after_snmp_asistance))
    print("FINISH!")
