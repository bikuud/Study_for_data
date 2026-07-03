import sqlite3

def load_to_sqlite(data_list, db_name='pokemon_data.db'):
    conn=sqlite3.connect(db_name)
    cursor=conn.cursor()
    
    cursor.execute('''
                   create table if not exists posts(
                       id text primary key,
                       title text)'''
                   )
    for post in data_list:
        cursor.execute('''
                       insert or ignore into posts(id,title) values(?,?)
                       ''', (post['id'], post['title']))
        
    conn.commit()
    conn.close()
    print(f'총 {len(data_list)}개의 데이터가 DB에 반영되었습니다.')