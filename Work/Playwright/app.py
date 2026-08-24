import asyncio
import time
from playwright.async_api import async_playwright

async def fetch_news_comments(url):
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        page=await browser.new_page()
        
        await page.goto(url)
        
        title_locator=page.locator('#title_area')
        
        await title_locator.wait_for()
        title=await title_locator.inner_text()
        
        
        print(title)
        
        await browser.close()
        
if __name__ == "__main__":
    url='https://n.news.naver.com/mnews/article/001/0016263501?rc=N&ntype=RANKING'
    asyncio.run(fetch_news_comments(url))