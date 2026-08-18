import streamlit as st
import pandas as pd
import requests
import re
import io
import os

# -------------------------------------------------------------
# 1. 유튜브 API 처리 함수
# -------------------------------------------------------------
def get_video_id(url):
    """유튜브 URL에서 11자리 영상 ID를 추출합니다."""
    if not isinstance(url, str):
        return None
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

def get_comment_count_api(url, api_key='AIzaSyD0K4bmt7kPRpslQ7WkquGJ-bBRDlf39cM'):
    """API를 호출하여 특정 영상의 댓글 수를 반환합니다."""
    video_id = get_video_id(url)
    if not video_id:
        return None
    
    api_url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={video_id}&key={api_key}"
    
    try:
        response = requests.get(api_url)
        data = response.json()
        
        if data.get("items"):
            statistics = data["items"][0]["statistics"]
            comment_count = statistics.get("commentCount")
            return int(comment_count) if comment_count else 0
        else:
            return None
    except Exception:
        return None

# -------------------------------------------------------------
# 2. Streamlit 웹 UI 구성
# -------------------------------------------------------------
st.set_page_config(page_title="유튜브 댓글 수집기", layout="wide")

st.title("📊 유튜브 댓글 수 일괄 업데이트 도구")
st.markdown("엑셀 또는 CSV 파일을 업로드하면 유튜브 URL을 분석하여 최신 댓글 수를 채워줍니다.")

# 메인 화면: 파일 업로드
uploaded_file = st.file_uploader("URL 목록이 포함된 파일 업로드", type=["xlsx", "csv"])

if uploaded_file is not None:
    # 파일 확장자에 따라 데이터프레임 읽기
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file,header=7,sheet_name='result')
            # 열이 없어도 에러가 나지 않도록 errors='ignore' 추가
            df.drop(['조회수','좋아요수','RT수'], axis=1, inplace=True, errors='ignore')
            df = df[df['URL'].str.contains('youtube.com', na=False)]
            
        st.success("파일 업로드 완료! 아래 데이터 미리보기를 확인하세요.")
        st.dataframe(df.head())
        
        # URL이 들어있는 열(Column) 선택
        url_column = st.selectbox("어떤 열(Column)에 유튜브 URL이 있나요?", df.columns)
        
        # 실행 버튼
        if st.button("댓글 수 업데이트 시작", type="primary"):
            
            # [핵심 1] 뷰(View) 충돌을 막기 위해 inplace 대신 변수에 직접 덮어씌워 인덱스를 완벽히 초기화합니다.
            df = df.reset_index(drop=True)
            
            total_rows = len(df)
            
            # [방어 로직] 필터링 후 남은 데이터가 없는 경우 처리
            if total_rows == 0:
                st.warning("분석할 유효한 URL 데이터가 없습니다.")
            else:
                progress_bar = st.progress(0.0)
                status_text = st.empty()
                
                comment_counts = []
                
                # [핵심 2] iterrows 대신 range를 사용하여 인덱스가 꼬일 가능성을 0%로 만듭니다.
                for i in range(total_rows):
                    # loc를 사용하여 0부터 시작하는 i번째 행의 데이터를 안전하게 가져옵니다.
                    url = df.loc[i, url_column]
                    count = get_comment_count_api(url)
                    comment_counts.append(count)
                    
                    # 진행률 계산 (i + 1 은 절대 total_rows를 넘을 수 없습니다)
                    progress_value = (i + 1) / total_rows
                    
                    # [핵심 3] 부동소수점 연산 오차로 인해 1.0을 아주 미세하게 초과하는 것을 차단합니다.
                    progress_bar.progress(min(progress_value, 1.0))
                    status_text.text(f"처리 중... ({i + 1}/{total_rows})")
                
                # 수집된 데이터를 새로운 열로 추가
                df['최신_댓글수'] = comment_counts
                
                st.success("모든 데이터 업데이트가 완료되었습니다!")
                st.dataframe(df)                
                # 결과를 엑셀 파일로 메모리에 저장 (서버에 파일 남기지 않음)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Sheet1')
                excel_data = output.getvalue()
                
                # 다운로드 버튼 제공
                st.download_button(
                    label="📥 업데이트된 엑셀 파일 다운로드",
                    data=excel_data,
                    file_name="youtube_comments_updated.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                st.write(f'총 업데이트 된 총 댓글 수: {df['최신_댓글수'].sum()}')
                
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")

st.divider()
st.subheader("🛠️ 인앱 코드 에디터 (빠른 수정용)")

# 현재 실행 중인 파이썬 파일의 절대 경로 가져오기
current_file_path = os.path.abspath(__file__)

# 현재 코드 읽어오기
with open(current_file_path, "r", encoding="utf-8") as f:
    current_code = f.read()

# 텍스트 에디터 위젯에 현재 코드를 띄우고, 수정된 내용을 변수에 담기
edited_code = st.text_area("이곳에서 코드를 직접 수정하세요:", value=current_code, height=400)

# 적용 버튼
if st.button("코드 저장 및 앱 재실행"):
    # 수정된 코드를 실제 파이썬 파일에 덮어쓰기
    with open(current_file_path, "w", encoding="utf-8") as f:
        f.write(edited_code)
    
    st.success("코드가 성공적으로 업데이트되었습니다. 앱을 다시 로드합니다.")
    # Streamlit 앱 즉시 새로고침
    st.rerun()