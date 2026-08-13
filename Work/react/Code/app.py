import streamlit as st
import pandas as pd
import requests
import re
import io

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
            df.drop(['조회수','좋아요수','RT수'], axis=1, inplace=True)
            df = df[df['URL'].str.contains('youtube.com', na=False)]
        st.success("파일 업로드 완료! 아래 데이터 미리보기를 확인하세요.")
        st.dataframe(df.head())
        
        # URL이 들어있는 열(Column) 선택
        url_column = st.selectbox("어떤 열(Column)에 유튜브 URL이 있나요?", df.columns)
        
        # 실행 버튼
        if st.button("댓글 수 업데이트 시작", type="primary"):
            # 진행 상태 표시 준비
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_rows = len(df)
            comment_counts = []
            
            # 각 행을 순회하며 API 호출
            for index, row in df.iterrows():
                url = row[url_column]
                count = get_comment_count_api(url)
                comment_counts.append(count)
                
                # 진행률 업데이트
                current_progress = (index + 1) / total_rows
                progress_bar.progress(current_progress)
                status_text.text(f"처리 중... ({index + 1}/{total_rows})")
            
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
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")