from lib.dupin_python_lib.dupin_core import DupinPathSniffer, DupinInfoSniffer, DupinLevelGrader, DupinVchainConnecter, database_init

if __name__ == '__main__':
    a: DupinVchainConnecter = DupinVchainConnecter('rdg-of01-1.adrussia.ru')
    a.connect()

