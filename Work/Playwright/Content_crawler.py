import os
import re
import asyncio
from datetime import datetime, timezone, timedelta
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from supabase import create_client, Client

KST=timezone(timedelta(hours=9))
GALLERY_ID = "hanwhaeagles_new"

SOURCE_DB = "practice_DB"
TARGET_DB = "content_DB"

CRAWL_LIMIT = 10
SYNC_LIMIT = 1000
HEADLESS = False



SUPABASE_KEY='sb_publishable_DVlQhSuIouv53mYz9NAFSQ_WBuLqavM'
SUPABASE_URL='https://jjnlqyxgxtzxeirksgqq.supabase.co'

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL 또는 SUPABASE_KEY가 설정되지 않았습니다.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def sync_post_numbers(limit: int = SYNC_LIMIT) -> int:
    """practice_DB의 게시글 번호와 작성일을 content_DB에 동기화한다."""
    try:
        response = (
            supabase.table(SOURCE_DB)
            .select("post_num, date")
            .not_.is_("post_num", "null")
            .order("post_num", desc=True)
            .limit(limit)
            .execute()
        )

        rows = [
            {
                "post_num": row["post_num"],
                "created_at": row.get("date"),
            }
            for row in (response.data or [])
        ]

        if not rows:
            print("동기화할 게시글 번호가 없습니다.")
            return 0

        (
            supabase.table(TARGET_DB)
            .upsert(
                rows,
                on_conflict="post_num",
                ignore_duplicates=True,
            )
            .execute()
        )

        print(f"게시글 번호 동기화 완료: {len(rows)}건")
        return len(rows)

    except Exception as e:
        print(f"게시글 번호 동기화 실패: {e}")
        return 0


def get_target_post_numbers(limit: int = CRAWL_LIMIT) -> list[int]:
    """아직 크롤링되지 않은 게시글 번호를 조회한다."""
    try:
        response = (
            supabase.table(TARGET_DB)
            .select("post_num")
            .is_("crawled_at", "null")
            .order("post_num", desc=False)
            .limit(limit)
            .execute()
        )

        post_numbers = [
            row["post_num"]
            for row in (response.data or [])
            if row.get("post_num") is not None
        ]

        print(f"크롤링 대상: {len(post_numbers)}건")
        return post_numbers

    except Exception as e:
        print(f"크롤링 대상 조회 실패: {e}")
        return []


async def crawl_contents(page, post_numbers: list[int]) -> list[dict]:
    """게시글 번호 목록의 본문을 수집한다."""
    results = []

    for post_num in post_numbers:
        url = f"https://gall.dcinside.com/board/view/?id={GALLERY_ID}&no={post_num}"

        try:
            print(f"게시글 {post_num} 수집 시작")

            await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60_000,
            )

            content_locator = page.locator("div.write_div").first
            await content_locator.wait_for(state="visible", timeout=10_000)

            content = (await content_locator.inner_text()).strip()

            if not content:
                print(f"게시글 {post_num}: 본문이 비어 있습니다.")
                continue

            results.append(
                {
                    "post_num": post_num,
                    "content": content,
                    "crawled_at":  datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")
                }
            )

            print(f"게시글 {post_num} 수집 성공: {len(content)}자")

        except PlaywrightTimeoutError:
            print(f"게시글 {post_num}: 페이지 또는 본문 로딩 시간 초과")

        except Exception as e:
            print(f"게시글 {post_num}: 수집 실패 - {e}")

    return results


def save_contents(rows: list[dict]) -> int:
    """수집한 본문과 수집 시각을 content_DB에 저장한다."""
    if not rows:
        print("저장할 정상 수집 결과가 없습니다.")
        return 0

    try:
        response = (
            supabase.table(TARGET_DB)
            .upsert(rows, on_conflict="post_num")
            .execute()
        )

        saved_count = len(response.data) if response.data else len(rows)
        print(f"Supabase 저장 완료: {saved_count}건")
        return saved_count

    except Exception as e:
        print(f"Supabase 저장 실패: {e}")
        raise


async def main() -> None:
    print("Content_crawler.py 실행")

    sync_post_numbers()

    target_post_numbers = get_target_post_numbers()

    if not target_post_numbers:
        print("수집할 신규 게시글이 없습니다.")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)

        try:
            page = await browser.new_page()
            results = await crawl_contents(page, target_post_numbers)
        finally:
            await browser.close()

    save_contents(results)


if __name__ == "__main__":
    asyncio.run(main())