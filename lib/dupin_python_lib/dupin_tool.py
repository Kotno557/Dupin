from typing import List, Dict
import requests

def get_ip_coord(ip: str) -> List[float]:
    lookup_info: Dict = requests.get(f'https://api.incolumitas.com/?q={ip}').json()
    return [lookup_info["location"]["latitude"], lookup_info["location"]["longitude"]]

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
