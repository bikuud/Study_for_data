import asyncio
from playwright.async_api import async_playwright
from supabase import create_client, Client
import re
from datetime import datetime, timezone, timedelta
KST=timezone(timedelta(hours=9))
today_str=datetime.now(KST).strftime('%Y-%m-%d')

#title_list=[]
#date_list=[]

SUPABASE_KEYS='sb_publishable_DVlQhSuIouv53mYz9NAFSQ_WBuLqavM'
SUPABASE_URL='https://jjnlqyxgxtzxeirksgqq.supabase.co'
supabase: Client=create_client(SUPABASE_URL, SUPABASE_KEYS)


async def community_scraper(url):
    scraped_data=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=False) # 서버에 올릴 땐 True
        page=await browser.new_page()
        
        await page.goto(url)
        
        title_locator=page.locator('td.gall_tit.ub-word >a:first-child')
        await title_locator.first.wait_for()
        titles=await title_locator.all()    
            
        date_locator=page.locator('td.gall_date')
        await date_locator.first.wait_for()
        dates= await date_locator.all()
        
        for title, date in zip(titles,dates):
            date_text=await date.inner_text()
            title_text=await title.inner_text()
            pattern=r'\d{2}:\d{2}'
            
            if re.search(pattern, date_text):
                date_text=today_str

            else:
                clean_date=date_text.replace(".","-").replace("/","-")
                date_text=f"20{clean_date}"
                
            scraped_data.append({
                'title':title_text.strip(),
                'date':date_text.strip()
            })
                        
        await browser.close()
        
        return scraped_data

if __name__=='__main__':
    url='https://gall.dcinside.com/board/lists/?id=hanwhaeagles_new'
    final_data=asyncio.run(community_scraper(url))
    
    print(f'총 {len(final_data)}개의 데이터를 수집했습니다. DB 전송을 시작합니다.')
    
    try:
        response=supabase.table('practice_DB').insert(final_data).execute()
        
        print('성공적으로 DB에 저장됐습니다.')
        
    
    except Exception as e:
        print(e)
    