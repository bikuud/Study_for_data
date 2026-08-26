import os
import re
import asyncio
from datetime import datetime, timezone, timedelta
from playwright.async_api import async_playwright
from supabase import create_client, Client
KST=timezone(timedelta(hours=9))
GALLERY_ID = "hanwhaeagles_new"
TARGET_DB = "content_DB"
FK_DB="practice_DB"


HEADLESS=True

print('Content_crawler.py 실행')
# 깃허브 업로드 시 삭제
SUPABASE_KEY='sb_publishable_DVlQhSuIouv53mYz9NAFSQ_WBuLqavM'
SUPABASE_URL='https://jjnlqyxgxtzxeirksgqq.supabase.co'

##SUPABASE_URL=os.getenv("SUPABASE_URL")
##SUPABASE_KEY=os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "\n SUPABASE_URL 또는 SUPABASE_KEY가 설정되지 않았습니다."
    )
    
supabase:Client= create_client(SUPABASE_URL, SUPABASE_KEY)

def get_postnum() -> list:
    """크롤링 해야하는 대상 게시글 번호 찾기"""
    try:
        response=supabase.table(FK_DB).select("post_num").order("post_num", desc=False).limit(100).execute()
        target_gall_num=[row["post_num"] for row in response.data]
        
        print(f'조회 건수:{len(response.data)}')
        print(target_gall_num)
        return target_gall_num
                
    except Exception as e:
        print('게시글 번호 조회 실패')

def Content_cralwer(post_num) ->str:
    """게시물 번호를 기반으로 콘텐츠를 크롤링합니다."""
    
    content_locator=page.locator("div.write_div")
    try:
        await content_locator.first.wait_for()
        print(f"게시글 번호 {post_num} 크롤링을 시작합니다.")
        print('='*40)
        print('게시글 미리 보기')
        print(content_locator.inner_text())
        
    except:
        print('게시글이 제대로 수집되지 않았습니다.')

if __name__=="__main__":
    Content_crawler(17655144)
    
        
            
    
    
    
    
    
    
    
    
    
    
    
    
def main()->None:
    url=f'https://gall.dcinside.com/board/view/?id={GALLERY_ID}_new&no={post_num}'
    