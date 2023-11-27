# Dupin
#### _Clean Network-Based Transmission Path Risk Detection and Improvement Architecture Program_

[![N|Solid](https://www.python.org/static/community_logos/python-powered-w-100x40.png)](https://www.python.org)

[![Build Status](https://travis-ci.org/joemccann/dillinger.svg?branch=master)](https://travis-ci.org/joemccann/dillinger)

#### REQUIREMENTS ####

- Linux (tested on Ubuntu 22.04, but should work on most distributions)
- Python 3.10/up
- Duplin-traceroute
- Nmap
- Config files from your OpenVPN network servers
- OpenVPN client
- net-tools


### Set Up ###

for dupin-server:
    apt update
    apt install pip dublin-traceroute nmap
    git clone https://github.com/Kotno557/Dobie
    cd Dobie
    root$ python3 -m pip install -r requirement.txt
    python3 dupin_server.py
    
for dupin-frontend:
    apt update
    curl -s https://deb.nodesource.com/setup_18.x | sudo bash
    sudo apt install nodejs -y
    cd Dobie/dupin-frontend
    npm install
    npm run dev (The application will listen on http://localhost:5173)
    
for dupin_vpn_server:
    apt update
    apt install pip dublin-traceroute nmap
    git clone https://github.com/Kotno557/Dobie
    cd Dobie
    root$ python3 -m pip install -r requirement.txt
    python3 dupin_server.py
    (You can use nohup to keep FastAPI server working)

for OpenVpn-server:
    wget https://git.io/vpn -O openvpn-install.sh
    chmod +x openvpn-install.sh
    ./openvpn-install.sh
    (Get the oven file to localhost)

to be completed.

