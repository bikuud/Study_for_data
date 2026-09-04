# 모듈 임포트
from supabase import create_client, Client

# 환경변수 등록
TARGET_DB='practice_DB'
MIGRATION_DB='contet_DB'
UPDATE_SIZE=1000
SUPABASE_KEY='sb_publishable_DVlQhSuIouv53mYz9NAFSQ_WBuLqavM'
SUPABASE_URL='https://jjnlqyxgxtzxeirksgqq.supabase.co'


supabase :Client=create_client(SUPABASE_URL, SUPABASE_KEY)


# 함수 1 : 마이그레이션 목표 Post_num 번호 한정

def get_target_numbers() -> tuple[int,int]:
    """크롤링 DB에서 Migration DB로 전송할 게시글 번호를 반환힙니다."""
    
    try:
        start_response=(
            supabase
            .table(MIGRATION_DB)
            .select('post_num')
            .order('post_num', desc=True)
            .limit(1)
            .maybe_single()
            .execute()
        )
        
        start_postnum=(
            start_response.data['postnum']
            if start_response.data
            else 0
        )
        
    except Exception as e:
        print(f'MIGRATION DB의 최신 게시글 번호 조회 실패 : {e}')
        start_postnum=0
        
        
        
    try:
        target_response=(
            supabase
            .table(TARGET_DB)
            .select('post_num')
            .order('post_num', desc=True)
            .limit(1)
            .maybe_single()
            .execute()
        )
        
        target_postnum=(
            target_response.data['post_num']
            if target_respnse.data
            else 0
        )
    except Exception as e:
        print(f'TARGET_DB의 최신 게시글 번호 조회 실패 : {e}')
        target_postnum=0
        
        
    return start_postnum, target_postnum


# 함수 2 : 실제 정보 마이그레이션

def data_migration(start_postnum, target_postnum) -> None:
    
    while True:
        response=(supabase.table(TARGET_DB).select('post_num, date')
                .gt('post_num', start_postnum)
                .lte('post_num', target_postnum)
                .order('post_num')
                .limit(UPDATE_SIZE).execute())
        
        posts=response.data or []
        
        if not posts:
            print('모든 게시글 적재 완료')
            return 0
        
        
        rows=[
            {'post_num':post['post_num'],
                'crawled_at':post['date']}
            for post in posts]
        
        (supabase
            .table(MIGRATION_DB)
            .upsert(
                rows,
                on_conflict='post_num',
                ignore_duplicates=True
            ).execute())
            
        
        start_postnum=response.data[-1]['post_num']
        
        print(
            f'이번 배치 {len(posts)건'
            f'다음 조회 기준 post_num :{start_postnum}'
            
        )
        
        
        
# 함수 3 : 누락 post_num 확인 및 누락 시 upsert

def upsert_missing_postnum()-> None:
    while True:
        response=
    
        
        
        
        
        
        
        
        
        
        
        
