from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import requests

#1 타겟 URL 설정
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
url= 'https://gall.dcinside.com/mgallery/board/lists?id=pokemontcgpocket'
response=requests.get(url, headers=headers)
post_data_list=[]
if response.status_code==200:
    print('서버는 잘 작동함, 이제 크롤링 해보겠음')
    soup=BeautifulSoup(response.text, 'html.parser')
    rows=soup.select('tr.ub-content.us-post')
    print(f'찾은 게시글 갯수 {len(rows)}')
    for row in rows:
        # 1. 제목이 있는 a 태그를 찾습니다.
        post_no=row.get('data-no')
        title_element = row.select_one('td.gall_tit.ub-word > a')
        if title_element:
            # 2. a 태그 안의 'em' 태그(아이콘)를 제거합니다.
            for em in title_element.select('em'):
                em.decompose() # .decompose()는 태그 자체를 완전히 삭제합니다.
            # 3. 이제 깨끗해진 텍스트만 추출합니다.
            title_text = title_element.text.strip()
            post_data={
                'id':post_no,
                'title':title_text
            }
            post_data_list.append(post_data)
else:
    print('일단 서버부터 응답 안함 ^^')
print(post_data_list)