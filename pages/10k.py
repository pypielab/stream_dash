import streamlit as st
from edgar import Company, set_identity
import time

# 1. SEC 신원 설정 (본인의 이메일로 수정하세요)
set_identity("your_name your_email@example.com")

# 2. 캐싱 적용: 동일한 티커 조회 시 네트워크 요청 스킵
# persist="disk" 설정을 더하면 앱을 껐다 켜도 로컬 파일에 저장되어 속도가 유지됩니다.
@st.cache_data(persist="disk")
def get_10k_sections(ticker: str):
    try:
        company = Company(ticker)
        filings = company.get_filings(form="10-K")
        if not filings:
            return None, None
            
        latest_filing = filings.latest()
        doc = latest_filing.obj()
        
        # 실제 데이터 추출
        item1 = doc["Item 1"]
        item1a = doc["Item 1A"]
        
        return item1, item1a
    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류 발생: {e}")
        return None, None

# --- Streamlit UI ---
st.title("🚀 US Stock 10-K Analyzer")

ticker = st.text_input("분석할 티커를 입력하세요 (예: AAPL, MSFT)", "MSFT").upper()

if st.button("데이터 가져오기"):
    with st.spinner(f"{ticker}의 보고서를 분석 중입니다..."):
        start_time = time.time()
        
        # 캐싱된 함수 호출
        item1, item1a = get_10k_sections(ticker)
        
        end_time = time.time()
        
        if item1 and item1a:
            st.success(f"완료! (소요 시간: {end_time - start_time:.2f}초)")
            
            tab1, tab2 = st.tabs(["Item 1: Business", "Item 1A: Risk Factors"])
            
            with tab1:
                st.markdown(item1)
            with tab2:
                st.markdown(item1a)
        else:
            st.warning("해당 티커의 10-K 보고서를 찾을 수 없습니다.")