from lib.dupin_python_lib.dupin_core import DupinPathSniffer, DupinInfoSniffer, DupinLevelGrader, DupinVchainConnecter, database_init
import sys

if __name__ == '__main__':
    database_init()
    main()

def main():
    try:
        if sys.argv[1] == 'path':
            target: str = sys.argv[2]
            temp: DupinPathSniffer = DupinPathSniffer(targit_url = target)
            print(temp.sniff_result)
            temp2: DupinInfoSniffer = DupinInfoSniffer(temp)
            print(temp2.info_result)
        
    except:
        print("command error")