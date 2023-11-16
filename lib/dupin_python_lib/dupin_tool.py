from typing import List, Dict, Union
import requests
import ipaddress
import socket

def get_ip_coord(ip: str) -> List[float]:
    lookup_info: Dict = requests.get(f'https://ipinfo.io/{ip}/json?token=6c37228d8bfabd').json()
    try:
        return tuple(lookup_info["loc"].split(','))
    except KeyError:
        print(f"[ERROR] dupin_tool.py.get_ip_coord: {lookup_info}")
        print(ip)
        return None

def ip_level_convert(level: str|int) -> str:
    if type(level) == str:
        table: Dict = {
            "-1": "DANGER",
            "0": "UNKNOW",
            "1": "LOW",
            "2": "PASSABLE",
            "3": "SAFE"
        }
    else:
        table: Dict = {
            -1: "DANGER",
            0: "UNKNOW",
            1: "LOW",
            2: "PASSABLE",
            3: "SAFE"
        }
    return table[level]

def check_private_ip(ip: str) -> bool:
    ip_obj: Union[ipaddress.IPv4Address, ipaddress.IPv6Address] = ipaddress.ip_address(ip)
    return ip_obj.is_private