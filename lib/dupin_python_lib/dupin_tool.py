from typing import List, Dict, Union
import requests
import ipaddress
import socket

def get_ip_coord(ip: str) -> List[float]:
    lookup_info: Dict = requests.get(f'https://api.incolumitas.com/?q={ip}&key=c3624c8ec4978dec').json()
    try:
        return (lookup_info["location"]["latitude"], lookup_info["location"]["longitude"])
    except KeyError:
        print(f"[ERROR] dupin_tool.py.get_ip_coord: {lookup_info}")
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