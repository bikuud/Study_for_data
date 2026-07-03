from extract import get_raw_data
from loader import load_to_sqlite

def main():
    data=get_raw_data()
    if data:
        load_to_sqlite(data)
    else:
        print('수집된 데이터가 없습니다.')
if __name__=="__main__":
    main()
