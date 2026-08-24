import os
import re
import asyncio
from datetime import datetime, timezone, timedelta

from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)
from supabase import create_client, Client


# ============================================================
# 기본 설정
# ============================================================

KST = timezone(timedelta(hours=9))

GALLERY_ID = "hanwhaeagles_new"
TABLE_NAME = "practice_DB"

# 로컬 PC에서 화면을 보며 테스트할 때 False
# GitHub Actions로 돌릴 때 True
HEADLESS = False

# 한 페이지를 최대 몇 페이지까지 확인할지
MAX_PAGES = 9

# 스크립트가 수정된 파일인지 확인하기 위한 출력
print("Crawler.py 실행: debug-attached-v1")


# ============================================================
# Supabase 설정
# ============================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client=create_client(SUPABASE_URL, SUPABASE_KEY)


if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "\nSUPABASE_URL 또는 SUPABASE_KEY가 설정되지 않았습니다.\n\n"
        "PowerShell에서 아래를 실행한 뒤, 같은 창에서 다시 실행하세요.\n\n"
        '$env:SUPABASE_URL="https://jjnlqyxgxtzxeirksgqq.supabase.co"\n'
        '$env:SUPABASE_KEY="Supabase에서_발급받은_키"\n'
        "python .\\Crawler.py\n"
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ============================================================
# 일반 함수
# ============================================================

def get_last_postnum() -> int:
    """DB에 저장된 가장 큰 게시글 번호를 가져온다."""
    try:
        response = (
            supabase.table(TABLE_NAME)
            .select("post_num")
            .order("post_num", desc=True)
            .limit(1)
            .execute()
        )

        if response.data:
            last_postnum = int(response.data[0]["post_num"])
        else:
            last_postnum = 0

        print(f"DB의 마지막 게시글 번호: {last_postnum}")
        return last_postnum

    except Exception as e:
        print(f"DB 마지막 게시글 번호 조회 실패: {e}")
        print("마지막 게시글 번호를 0으로 처리합니다.")
        return 0


def normalize_date(date_text: str) -> str:
    """목록의 날짜 표현을 YYYY-MM-DD 형식으로 변환한다."""
    date_text = date_text.strip()

    # 당일 작성 글: 예) 14:35
    if re.fullmatch(r"\d{2}:\d{2}", date_text):
        return datetime.now(KST).strftime("%Y-%m-%d")

    # 과거 글: 예) 24.08.24 / 24/08/24
    clean_date = date_text.replace(".", "-").replace("/", "-")

    # 혹시 YYYY-MM-DD로 이미 들어올 때는 그대로 반환
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", clean_date):
        return clean_date

    return f"20{clean_date}"


async def save_debug_files(page) -> None:
    """문제 발생 시 화면과 HTML을 현재 폴더에 남긴다."""
    try:
        await page.screenshot(
            path="debug_timeout.png",
            full_page=True,
        )

        html = await page.content()

        with open("debug_timeout.html", "w", encoding="utf-8") as f:
            f.write(html)

        print("\n디버그 파일을 저장했습니다.")
        print("- debug_timeout.png")
        print("- debug_timeout.html")

    except Exception as e:
        print(f"디버그 파일 저장 중 오류: {e}")


# ============================================================
# 비동기 수집 함수
# ============================================================

async def scrape_page(
    page,
    url: str,
    last_postnum: int,
) -> tuple[list[dict], bool]:
    """
    갤러리 목록의 한 페이지에서 신규 게시글을 수집한다.

    반환값:
    - list[dict]: 신규 게시글 목록
    - bool: 기존 수집 글 번호에 도달하면 True
    """
    print("\n" + "=" * 70)
    print(f"접속 URL: {url}")

    try:
        response = await page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

    except PlaywrightTimeoutError:
        print("\n[오류] page.goto()가 60초 안에 완료되지 않았습니다.")
        print("현재 URL:", page.url)
        print("페이지 제목:", await page.title())
        await save_debug_files(page)
        raise

    print("HTTP 상태:", response.status if response else "응답 없음")
    print("현재 URL:", page.url)
    print("페이지 제목:", await page.title())

    postnum_locator = page.locator("td.gall_num")
    title_locator = page.locator("td.gall_tit.ub-word > a:first-child")
    date_locator = page.locator("td.gall_date")

    # 이 메시지가 출력되는지 확인:
    # 출력된다면 지금 이 파일이 실행되고 있는 것입니다.
    print("DEBUG: td.gall_num state='attached' 대기 시작")

    try:
        # 핵심: 기본값 visible이 아니라 attached로 명시
        await postnum_locator.first.wait_for(
            state="attached",
            timeout=30_000,
        )

    except PlaywrightTimeoutError:
        print("\n[오류] 30초 안에 td.gall_num을 찾지 못했습니다.")
        print("현재 URL:", page.url)
        print("페이지 제목:", await page.title())
        print("td.gall_num:", await postnum_locator.count())
        print("td.gall_tit:", await title_locator.count())
        print("td.gall_date:", await date_locator.count())

        await save_debug_files(page)

        raise RuntimeError(
            "게시글 목록을 찾을 수 없습니다. "
            "debug_timeout.png 및 debug_timeout.html을 확인하세요."
        )

    postnum_count = await postnum_locator.count()
    title_count = await title_locator.count()
    date_count = await date_locator.count()

    print(f"td.gall_num 개수: {postnum_count}")
    print(f"제목 요소 개수: {title_count}")
    print(f"날짜 요소 개수: {date_count}")

    postnums = await postnum_locator.all()
    titles = await title_locator.all()
    dates = await date_locator.all()

    scraped_data: list[dict] = []
    reached_collected_post = False

    for postnum, title, date in zip(postnums, titles, dates):
        postnum_text = (await postnum.inner_text()).strip()

        # 공지, 설문 등 숫자가 아닌 행 제외
        if not postnum_text.isdigit():
            continue

        current_post_num = int(postnum_text)

        # 목록은 최신순이다.
        # 기존 최대 게시글 번호 이하를 만나면 다음 페이지 탐색도 불필요하다.
        if current_post_num <= last_postnum:
            print(f"기수집 게시글 번호에 도달: {current_post_num}")
            reached_collected_post = True
            break

        title_text = (await title.inner_text()).strip()
        date_text = (await date.inner_text()).strip()

        scraped_data.append(
            {
                "post_num": current_post_num,
                "title": title_text,
                "date": normalize_date(date_text),
            }
        )

    print(f"이번 페이지 신규 수집 건수: {len(scraped_data)}")

    return scraped_data, reached_collected_post


# ============================================================
# 메인 실행
# ============================================================

async def main() -> None:
    last_postnum = get_last_postnum()
    all_data: list[dict] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=HEADLESS,
            slow_mo=200 if not HEADLESS else 0,
        )

        try:
            page = await browser.new_page(
                viewport={
                    "width": 1440,
                    "height": 1000,
                }
            )

            for page_num in range(1, MAX_PAGES + 1):
                url = (
                    "https://gall.dcinside.com/board/lists/"
                    f"?id={GALLERY_ID}&page={page_num}"
                )

                page_data, reached_collected_post = await scrape_page(
                    page=page,
                    url=url,
                    last_postnum=last_postnum,
                )

                all_data.extend(page_data)

                if reached_collected_post:
                    print("기수집 게시글을 만났으므로 페이지 순회를 종료합니다.")
                    break

                if not page_data:
                    print("신규 데이터가 없으므로 페이지 순회를 종료합니다.")
                    break

        finally:
            await browser.close()

    if not all_data:
        print("\n새로 저장할 게시글이 없습니다.")
        return

    # DB에는 오래된 글부터 저장
    all_data.sort(key=lambda row: row["post_num"])

    print(f"\n총 {len(all_data)}건 수집 완료. Supabase 저장을 시작합니다.")

    try:
        response = supabase.table(TABLE_NAME).insert(all_data).execute()
        saved_count = len(response.data) if response.data else len(all_data)
        print(f"Supabase 저장 완료: {saved_count}건")

    except Exception as e:
        print(f"Supabase 저장 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())