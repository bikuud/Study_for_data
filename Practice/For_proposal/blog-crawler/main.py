import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin

import time
import numpy as np
from supabase import create_client
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.getenv("ENV_FILE", ".env"))

supabase_client=create_client(
     os.environ["SUPABASE_URL"],
     os.environ["SUPABASE_KEY"])

CLIENT_ID=os.environ['CLIENT_ID']
CLIENT_SECRET_KEY=os.environ['CLIENT_SECRET_KEY']


API_URL = "https://naverapihub.apigw.ntruss.com/search/v1/blog" 

headers={'X-NCP-APIGW-API-KEY-ID':CLIENT_ID,
         'X-NCP-APIGW-API-KEY':CLIENT_SECRET_KEY}
keywords=['신혼부부 필수템','신혼부부 필수품','신혼부부 강추템','신혼부부 추천템']
body_data=[]

HEADERS_FOR_CRAWLER = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36")}

def blog_extractor(start_num=1, target_number=1000, batch_size=100):
    data_dict={}
    
    for keyword in keywords:
        total_data=[]
        
        for start in range(start_num, target_number+1, batch_size):
            params={'query':keyword,
            'display':batch_size,
            'start':start,
            'sort':'date',
            'format':'json'}

            try:
                response=requests.get(
                    API_URL,
                    headers=headers,
                    params=params,
                    timeout=15
                )
                response.raise_for_status()
                items=response.json().get('items',[])
                
                if not items:
                    break
                
                total_data.extend(items)                
            except Exception as e:
                print(e)
                break
        
        data_dict[keyword]=total_data
        
    rows=[]
    for keyword, items in data_dict.items():
        for item in items:
            row=item.copy()
            row['keyword']= keyword
            rows.append(row)
    df=pd.json_normalize(rows)
    if df.empty:
        return df
    
    df=df.drop_duplicates(
        subset=['link'],
        keep='first',
        ignore_index=True
    )
    
    df=df.drop(columns=['description','bloggername','bloggerlink'])
    return df


def body_text_extractor(url):
    print('블로그 본문을 수집합니다.')
    
    rng = np.random.default_rng()

    
    
    try:
        # 1. 외부 네이버 블로그 페이지 요청
        response = requests.get(
            url,
            headers=HEADERS_FOR_CRAWLER,
            timeout=10
        )
        
        response.raise_for_status()

        outer_soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # 2. 실제 본문을 담은 iframe 주소 찾기
        iframe = outer_soup.select_one("iframe#mainFrame")

        if iframe is not None and iframe.get("src"):
            inner_url = urljoin(url, iframe["src"])

            # 3. iframe 내부 페이지 재요청
            inner_response = requests.get(
                inner_url,
                headers=HEADERS_FOR_CRAWLER,
                timeout=10
            )
            inner_response.raise_for_status()

            soup = BeautifulSoup(
                inner_response.text,
                "html.parser"
            )

        else:
            # iframe 없는 주소(PostView 등)는 현재 HTML 그대로 사용
            soup = outer_soup

        # 4. 최신 스마트에디터 본문 선택
        body_tag = soup.select_one("div.se-main-container")

        # 5. 구형 에디터 구조도 대비
        if body_tag is None:
            body_tag = soup.select_one("#postViewArea")

        if body_tag is None:
            print(f"본문 영역을 찾지 못함: {url}")
            return None

        print('네이버 블로그 본문 크롤링을 완료했습니다. ')
        
        num=rng.uniform(1,3)
        time.sleep(num)
        return body_tag.get_text(
            separator="\n",
            strip=True)
    
    except requests.RequestException as e:
        print(f"요청 오류: {url} / {e}")
        return None
    
def save_to_supabase(df:pd.DataFrame,
                     table_name :str='blog_DB',
                     batch_size:int=100) -> int:
    if batch_size<=0:
        raise ValueError('batch size는 1 이상이어야 합니다.')
    
    if df is None or df.empty:
        print('저장할 데이터가 없습니다.')
        return 0
    
    save_df=df.copy().rename(columns={"Content":'content'})
    
    save_df=save_df.dropna(subset=['link', 'content'])
    save_df=save_df[
        save_df['link'].str.strip().ne("")
        & save_df['content'].str.strip().ne("")
    ].copy()
    
    save_df=save_df.drop_duplicates(subset='link')
    
    if save_df.empty:
        print('본문 수집에 성공한 데이터가 없습니다.')
        return 0
    
    save_df['postdate']=(
        pd.to_datetime(
            save_df['postdate'],
            format='%Y%m%d',
            errors='raise'
        )
    ).dt.strftime('%Y-%m-%d')
    
    save_df['crawled_at']=datetime.now(timezone.utc).isoformat()
    
    save_df=save_df.astype(object).where(
        pd.notna(save_df), None
    )
    
    rows=save_df.to_dict(orient='records')
    
    print(
        f'전체{len(df)}건/저장 대상{len(rows)}건/'
        f'제외{len(df)-len(rows)}건'
    )
    
    saved_count=0
    
    for start in range(0, len(rows), batch_size):
        batch=rows[start:start+batch_size]
        
        try:
            (
                supabase_client
                .table(table_name)
                .upsert(batch, on_conflict='link')
                .execute()
            )
            
        except Exception as e:
            print(
                f'저장 실패: {start+1}~{start+len(batch)}번쨰 데이터/'
                f'앞서 저장 완료한 건수 :{saved_count}'
            )
            
            raise RuntimeError(
                f'Supabase 적재 실패 :{table_name}'
            ) from e
        saved_count+=len(batch)
        print(f'저장 완료:{saved_count}/{len(rows)}건')
        
    return saved_count
    
    
def main():
    try:
        df=blog_extractor()
        
        if df.empty:
            return df
        df_sample=df.iloc[:5,:].copy()      
        df_sample['Content']=df_sample['link'].apply(lambda x: body_text_extractor(x))
        
        saved_count=save_to_supabase(df_sample)
        print(f'전체 작업 완료 :{saved_count}건 저장 처리')
        
    
    except Exception as e:
        print(f"작업 실패: {e}")
        raise

    
if __name__=='__main__':
    main()