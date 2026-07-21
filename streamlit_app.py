import os
import urllib.parse
import urllib.request
import json
import pandas as pd
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="eㅔ브리띵 에코 맵",
    page_icon="🌱",
    layout="wide"
)

CAFE_FILE = "cafes.csv"
REVIEW_FILE = "reviews.csv"

# OpenStreetMap Nominatim을 이용한 도로명 주소 -> 위도/경도 변환 함수 (무료/API Key 불필요)
def geocode_address(address):
    try:
        # 한국 지역 검색 정확도를 위해 주소 정리
        clean_addr = address.split("(")[0].strip()
        url = "https://nominatim.openstreetmap.org/search?format=json&q=" + urllib.parse.quote(clean_addr)
        req = urllib.request.Request(url, headers={'User-Agent': 'EverythingEcoMap/1.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
    except Exception:
        pass
    return None, None

# 데이터 로드 함수
def load_cafe_data():
    if os.path.exists(CAFE_FILE):
        try:
            df = pd.read_csv(CAFE_FILE)
            for col in ["카페명", "주소 (도로명 주소)", "할인 내용"]:
                if col not in df.columns:
                    df[col] = ""
            return df
        except Exception:
            pass
    return pd.DataFrame(columns=["카페명", "주소 (도로명 주소)", "할인 내용"])

def load_review_data():
    if os.path.exists(REVIEW_FILE):
        try:
            return pd.read_csv(REVIEW_FILE)
        except Exception:
            pass
    return pd.DataFrame(columns=["카페명", "작성자", "평점", "후기"])

# 데이터 로딩
cafe_df = load_cafe_data()
review_df = load_review_data()

# 메인 타이틀
st.title("🌱 eㅔ브리띵 에코 맵")
st.caption("텀블러 할인 카페를 찾고, 에코 장소를 공유해 보세요!")

tab1, tab2 = st.tabs(["🗺️ 에코 맵 & 지점 상세/후기", "➕ 새 카페 위치 추가"])

# ==================== [TAB 1] 에코 맵 & 상세 후기 ====================
with tab1:
    col_select, col_detail = st.columns([1, 1])

    with col_select:
        st.subheader("☕ 카페 검색 및 지도 보기")
        
        cafe_list = cafe_df["카페명"].dropna().tolist() if not cafe_df.empty else []
        
        if cafe_list:
            selected_cafe = st.selectbox("지점(카페)을 선택하세요", cafe_list)
            selected_info = cafe_df[cafe_df["카페명"] == selected_cafe].iloc[0]
            
            st.markdown(f"### **{selected_info['카페명']}**")
            address = selected_info.get("주소 (도로명 주소)", "주소 정보 없음")
            st.markdown(f"📍 **도로명 주소:** {address}")
            
            discount = selected_info.get('할인 내용')
            discount_text = discount if pd.notna(discount) and str(discount).strip() != "" else "텀블러 할인 제공"
            st.success(f"🎁 **할인 혜택:** {discount_text}")
            
            # 카카오맵 / 네이버지도 직접 보기 링크 제공
            encoded_addr = urllib.parse.quote(f"{selected_cafe} {address}")
            kakao_url = f"https://map.kakao.com/?q={encoded_addr}"
            naver_url = f"https://map.naver.com/v5/search/{encoded_addr}"
            
            st.markdown(f"🔗 **외부 지도에서 위치 확인하기:** [카카오맵에서 보기]({kakao_url}) | [네이버지도에서 보기]({naver_url})")
            
            # 주소 변환 후 Streamlit 인앱 지도 표시 시도
            lat, lng = geocode_address(address)
            if lat and lng:
                map_df = pd.DataFrame([{"위도": lat, "경도": lng}])
                st.map(map_df, latitude="위도", longitude="경도", size=25, color="#2E7D32")
            else:
                st.caption("💡 상단 외부 지도 링크를 누르시면 카카오/네이버 지도로 바로 위치가 연결됩니다.")

    with col_detail:
        st.subheader("💬 지점 후기 및 평점")
        
        if cafe_list and 'selected_cafe' in locals():
            st.markdown(f"**[{selected_cafe}] 후기 작성**")
            
            with st.form("review_form", clear_on_submit=True):
                user_name = st.text_input("작성자 (닉네임)", value="에코러버")
                rating = st.slider("평점", 1, 5, 5)
                review_text = st.text_area("후기 및 텀블러 사용 팁을 남겨주세요")
                
                submit_review = st.form_submit_button("후기 등록")
                
                if submit_review:
                    if review_text.strip():
                        new_review = pd.DataFrame([{
                            "카페명": selected_cafe,
                            "작성자": user_name,
                            "평점": "⭐" * rating,
                            "후기": review_text
                        }])
                        review_df = pd.concat([review_df, new_review], ignore_index=True)
                        review_df.to_csv(REVIEW_FILE, index=False)
                        st.success("후기가 등록되었습니다!")
                        st.rerun()
                    else:
                        st.warning("후기 내용을 입력해주세요.")
            
            st.divider()
            st.markdown("📖 **등록된 후기 목록**")
            cafe_reviews = review_df[review_df["카페명"] == selected_cafe]
            
            if not cafe_reviews.empty:
                for _, r in cafe_reviews.iloc[::-1].iterrows():
                    st.write(f"**{r['작성자']}** ({r['평점']})")
                    st.caption(r["후기"])
                    st.divider()
            else:
                st.info("아직 등록된 후기가 없습니다. 첫 후기를 작성해 보세요!")

# ==================== [TAB 2] 도로명 주소로 카페 추가 ====================
with tab2:
    st.subheader("➕ 새로운 텀블러 할인 카페 추가")
    st.caption("도로명 주소만 입력하셔도 카페를 등록하실 수 있습니다.")
    
    with st.form("add_cafe_form", clear_on_submit=True):
        new_name = st.text_input("카페명 (예: 스타벅스 OO점)")
        new_address = st.text_input("도로명 주소 (예: 서울 용산구 청파로47길 78)")
        new_discount = st.text_input("할인 내용 (예: 텀블러 사용시 300원 할인)")
        
        submit_cafe = st.form_submit_button("카페 등록하기")
        
        if submit_cafe:
            if new_name and new_address:
                new_data = pd.DataFrame([{
                    "카페명": new_name,
                    "주소 (도로명 주소)": new_address,
                    "할인 내용": new_discount
                }])
                
                cafe_df = pd.concat([cafe_df, new_data], ignore_index=True)
                cafe_df.to_csv(CAFE_FILE, index=False)
                
                st.success(f"'{new_name}' 카페가 성공적으로 추가되었습니다!")
                st.rerun()
            else:
                st.error("카페명과 도로명 주소는 필수 입력 사항입니다.")
