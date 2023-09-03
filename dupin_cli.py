from lib.dupin_python_lib.dupin_core import DupinPathSniffer, DupinInfoSniffer, DupinLevelGrader, database_init

if __name__ == '__main__':
    database_init()
    test = DupinPathSniffer('dublin-traceroute.net')
    print(test.sniff_result)
    test_path_info: DupinInfoSniffer = DupinInfoSniffer(test)
    print(test_path_info.info_result)
    test_grade: DupinLevelGrader = DupinLevelGrader(test_path_info)
    print(test_grade.path_clean_result)