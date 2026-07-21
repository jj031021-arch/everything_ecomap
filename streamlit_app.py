import os
import pandas as pd
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="eㅔ브리띵 에코 맵",
    page_icon="🌱",
    layout="wide"
)

CAFE_FILE = "cafes.csv"
REVIEW_FILE = "reviews.csv"

# 데이터 로드 함수
@st.cache_data
def load_cafe_data():
    if os.path.exists(CAFE_FILE):
        return pd.read_csv(CAFE_FILE)
    else:
        return pd.DataFrame(columns=["카페명", "주소 (도로명 주소)", "위도", "경도", "할인 내용"])

def load_review_data():
    if os.path.exists(REVIEW_FILE):
        return pd.read_csv(REVIEW_FILE)
    return pd.DataFrame(columns=["카페명", "작성자", "평점", "후기"])

# 데이터 불러오기
cafe_df = load_cafe_data()
review_df = load_review_data()

# 메인 타이틀
st.title("🌱 eㅔ브리띵 에코 맵")
st.caption("텀블러 할인 카페를 찾고, 에코 장소를 공유해 보세요!")

# 탭 구성
tab1, tab2 = st.tabs(["🗺️ 에코 맵 & 지점 상세/후기", "➕ 새 카페 위치 추가"])

# ==================== [TAB 1] 지도 및 후기 ====================
with tab1:
    col_map, col_detail = st.columns([1.3, 1])

    with col_map:
        st.subheader("📍 텀블러 할인 카페 지도")
        
        # 위도/경도가 있는 데이터만 추출
        map_data = cafe_df.dropna(subset=["위도", "경도"]).copy()
        
        if not map_data.empty:
            st.map(
                map_data,
                latitude="위도",
                longitude="경도",
                size=20,
                color="#2E7D32"
            )
        else:
            st.info("지도에 표시할 좌표 데이터가 있는 카페가 없습니다.")

    with col_detail:
        st.subheader("☕ 카페 상세 정보 및 후기")
        
        cafe_list = cafe_df["카페명"].tolist() if not cafe_df.empty else []
        
        if cafe_list:
            selected_cafe = st.selectbox("지점(카페)을 선택하세요", cafe_list)
            
            # 선택한 카페 정보 찾기
            info = cafe_df[cafe_df["카페명"] == selected_cafe].iloc[0]
            
            st.markdown(f"### **{info['카페명']}**")
            st.markdown(f"📍 **주소:** {info['주소 (도로명 주소)']}")
            
            discount = info['할인 내용'] if pd.notna(info['할인 내용']) else "텀블러 할인 제공"
            st.success(f"🎁 **할인 혜택:** {discount}")
            
            st.divider()
            
            # 후기 작성
            st.markdown("💬 **이 카페 후기 작성하기**")
            with st.form("review_form", clear_on_submit=True):
                user_name = st.text_input("작성자 (닉네임)", value="에코러버")
                rating = st.slider("평점", 1, 5, 5)
                review_text = st.text_area("후기 및 텀블러 사용 팁을 작성해주세요")
                
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
            
            # 등록된 후기 목록
            st.markdown("📖 **지점 후기 목록**")
            cafe_reviews = review_df[review_df["카페명"] == selected_cafe]
            
            if not cafe_reviews.empty:
                for _, r in cafe_reviews.iloc[::-1].iterrows():
                    st.write(f"**{r['작성자']}** ({r['평점']})")
                    st.caption(r["후기"])
                    st.divider()
            else:
                st.info("아직 등록된 후기가 없습니다. 첫 후기를 작성해 보세요!")
        else:
            st.write("등록된 카페가 없습니다.")

# ==================== [TAB 2] 위치 직접 추가 ====================
with tab2:
    st.subheader("➕ 새로운 텀블러 할인 카페 추가")
    st.caption("알고 계신 텀블러 할인 카페를 직접 추가해 보세요.")
    
    with st.form("add_cafe_form", clear_on_submit=True):
        new_name = st.text_input("카페명 (예: 스타벅스 OO점)")
        new_address = st.text_input("주소 (도로명 주소)")
        new_discount = st.text_input("할인 내용 (예: 텀블러 사용시 300원 할인)")
        
        st.write("📌 **지도 표시용 좌표 (선택 사항)**")
        col_lat, col_lng = st.columns(2)
        with col_lat:
            new_lat = st.number_input("위도 (Latitude, 예: 37.596056)", value=0.0, format="%.6f")
        with col_lng:
            new_lng = st.number_input("경도 (Longitude, 예: 127.060750)", value=0.0, format="%.6f")
            
        submit_cafe = st.form_submit_button("카페 추가하기")
        
        if submit_cafe:
            if new_name and new_address:
                lat_val = new_lat if new_lat != 0.0 else None
                lng_val = new_lng if new_lng != 0.0 else None
                
                new_data = pd.DataFrame([{
                    "카페명": new_name,
                    "주소 (도로명 주소)": new_address,
                    "위도": lat_val,
                    "경도": lng_val,
                    "할인 내용": new_discount
                }])
                
                # 기존 데이터에 추가 후 저장
                cafe_df = pd.concat([cafe_df, new_data], ignore_index=True)
                cafe_df.to_csv(CAFE_FILE, index=False)
                
                st.success(f"'{new_name}' 카페가 성공적으로 추가되었습니다!")
                st.rerun()
            else:
                st.error("카페명과 주소는 필수 입력 사항입니다.")
