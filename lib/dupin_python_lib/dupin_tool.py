from typing import List, Dict, Union
import requests
import ipaddress
import networkx

IPINFO_ACCESS_TOKEN = '6c37228d8bfabd'

def get_ip_coord(ip: str) -> List[float]:
    lookup_info: Dict = requests.get(f'https://ipinfo.io/{ip}/json?token=6c37228d8bfabd').json()
    try:
        return tuple(map(float, lookup_info["loc"].split(',')))
    except KeyError:
        print(f"[ERROR] dupin_tool.py.get_ip_coord: {lookup_info}")
        print(ip)
        return None

def ip_level_convert(level: str|int) -> str:
    if type(level) == str:
        table: Dict = {
            "-1": "DANGER",
            "0": "UNKNOWN",
            "1": "LOW",
            "2": "PASSABLE",
            "3": "SAFE"
        }
    else:
        table: Dict = {
            -1: "DANGER",
            0: "UNKNOWN",
            1: "LOW",
            2: "PASSABLE",
            3: "SAFE"
        }
    return table[level]

def check_private_ip(ip: str) -> bool:
    ip_obj: Union[ipaddress.IPv4Address, ipaddress.IPv6Address] = ipaddress.ip_address(ip)
    return ip_obj.is_private

    
def shortest_path(vpn_resault: Dict, target_url: str) -> List[str]:
    graph: networkx.Graph = networkx.Graph()
    for ip in vpn_resault:
        for ip2 in vpn_resault[ip]:
            graph.add_edge(ip, ip2, weight=vpn_resault[ip][ip2]["path_weight"])

    return {
        "shortest_path": networkx.shortest_path(graph, source="localhost", target=target_url, weight='weight'),
        "shortest_distance": networkx.shortest_path_length(graph, source="localhost", target=target_url, weight='weight'),
    }

def clean_table_parser(clean_table: Dict) -> Dict :
    res = {
        "hdm":{
            "clean": [],
            "unclean": []
        },
        "isp":{
            "clean": [],
            "unclean": []
        }
    }

    for type in clean_table:
        for clean in clean_table[type]:
            for coun_cate in clean_table[type][clean]:
                for item in clean_table[type][clean][coun_cate]:
                    res[type][clean].append(item)

    return res

VPN_NAT_ADDRESS = {
    ipaddress.IPv4Network("104.44.0.0/16") : {
        "isp": "Microsoft Corporation",
        "hdm": "ciscoSystems",
        "os": "Cisco"
    },
    ipaddress.IPv4Network("13.104.0.0/14") : {
        "isp": "Microsoft Corporation",
        "hdm": "ciscoSystems",
        "os": "Cisco"
    }
}