from supabase import create_client, Client

TARGET_DB="content_DB"
MIGRATION_DB="practice_DB"


print('기존 DB에서 POST_NUM을 가져옵니다.')
SUPABASE_KEY='sb_publishable_DVlQhSuIouv53mYz9NAFSQ_WBuLqavM'
SUPABASE_URL='https://jjnlqyxgxtzxeirksgqq.supabase.co'


supabase:Client=create_client(SUPABASE_URL, SUPABASE_KEY)

def seed_content_queue():
    response=(
        supabase
        .table("practice_DB")
        .select("post_num")
        .order("post_num")
        .execute()
    )