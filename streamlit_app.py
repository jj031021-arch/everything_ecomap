import os
import pandas as pd
import pydeck as pdk
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="eㅔ브리띵 에코 맵",
    page_icon="🌱",
    layout="wide"
)

CAFE_FILE = "cafes.csv"
REVIEW_FILE = "reviews.csv"

# 데이터 로드
def load_cafe_data():
    if os.path.exists(CAFE_FILE):
        return pd.read_csv(CAFE_FILE)
    return pd.DataFrame(columns=["카페명", "주소 (도로명 주소)", "위도", "경도", "할인 내용"])

def load_review_data():
    if os.path.exists(REVIEW_FILE):
        return pd.read_csv(REVIEW_FILE)
    return pd.DataFrame(columns=["카페명", "작성자", "평점", "후기"])

cafe_df = load_cafe_data()
review_df = load_review_data()

# 타이틀
st.title("🌱 eㅔ브리띵 에코 맵")
st.caption("텀블러 할인 카페를 확인하고, 자유롭게 후기와 새 에코 스팟을 공유하세요!")

# 탭 구성
tab1, tab2 = st.tabs(["🗺️ 에코 맵 대시보드", "➕ 새로운 카페 위치 추가"])

# ==================== [TAB 1] 대시보드 ====================
with tab1:
    col_map, col_detail = st.columns([1.8, 1])

    with col_map:
        st.subheader("📍 서울 텀블러 할인 카페 지도")
        st.caption("💡 지도 위 마커(아이콘)에 마우스를 올리면 할인 정보와 주소가 표시됩니다.")

        # 위도/경도가 있는 데이터 필터링
        valid_data = cafe_df.dropna(subset=["위도", "경도"]).copy()

        if not valid_data.empty:
            # 기본 지도 위치 (서울 중심)
            view_state = pdk.ViewState(
                latitude=valid_data["위도"].mean(),
                longitude=valid_data["경도"].mean(),
                zoom=12,
                pitch=0
            )

            # 지도 아이콘 마커 레이어
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=valid_data,
                get_position=["경도", "위도"],
                get_color="[46, 125, 50, 200]",  # 에코 초록색 (RGB)
                get_radius=120,
                pickable=True,
                auto_highlight=True
            )

            # Pydeck 지도 렌더링 (마우스 오버 툴팁 설정)
            r = pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                tooltip={
                    "html": "<b>☕ {카페명}</b><br/>"
                            "📍 주소: {주소 (도로명 주소)}<br/>"
                            "🎁 혜택: <span style='color:#2E7D32;'><b>{할인 내용}</b></span>",
                    "style": {
                        "backgroundColor": "#ffffff",
                        "color": "#333333",
                        "fontSize": "14px",
                        "padding": "10px",
                        "borderRadius": "8px",
                        "boxShadow": "0px 2px 6px rgba(0,0,0,0.3)"
                    }
                }
            )

            st.pydeck_chart(r, use_container_width=True)
        else:
            st.info("지도에 표시할 데이터가 없습니다.")

    with col_detail:
        st.subheader("☕ 카페 상세 정보 및 후기 작성")

        cafe_list = cafe_df["카페명"].dropna().tolist() if not cafe_df.empty else []

        if cafe_list:
            selected_cafe = st.selectbox("지점(카페)을 선택해 상세 정보 확인/후기 등록", cafe_list)

            # 선택한 카페 정보
            info = cafe_df[cafe_df["카페명"] == selected_cafe].iloc[0]

            st.markdown(f"### **{info['카페명']}**")
            st.markdown(f"📍 **주소:** {info['주소 (도로명 주소)']}")
            st.success(f"🎁 **할인 혜택:** {info['할인 내용']}")

            st.divider()

            # 후기 작성
            st.markdown("💬 **후기 작성하기**")
            with st.form("review_form", clear_on_submit=True):
                user_name = st.text_input("작성자 (닉네임)", value="에코러버")
                rating = st.slider("평점", 1, 5, 5)
                review_text = st.text_area("방문 후기 및 텀블러 사용 팁")

                submit_review = st.form_submit_button("후기 등록")

                if submit_review:
                    if review_text.strip():
                        new_rev = pd.DataFrame([{
                            "카페명": selected_cafe,
                            "작성자": user_name,
                            "평점": "⭐" * rating,
                            "후기": review_text
                        }])
                        review_df = pd.concat([review_df, new_rev], ignore_index=True)
                        review_df.to_csv(REVIEW_FILE, index=False)
                        st.success("후기가 등록되었습니다!")
                        st.rerun()
                    else:
                        st.warning("후기 내용을 작성해주세요.")

            # 후기 목록
            st.markdown("📖 **등록된 후기**")
            cafe_reviews = review_df[review_df["카페명"] == selected_cafe]

            if not cafe_reviews.empty:
                for _, r in cafe_reviews.iloc[::-1].iterrows():
                    st.write(f"**{r['작성자']}** ({r['평점']})")
                    st.caption(r["후기"])
                    st.divider()
            else:
                st.info("아직 등록된 후기가 없습니다. 첫 후기를 올려보세요!")

# ==================== [TAB 2] 위치 직접 추가 ====================
with tab2:
    st.subheader("➕ 새로운 카페 위치 직접 추가하기")
    st.caption("새로운 텀블러 할인 카페를 지도에 직접 등록해보세요.")

    with st.form("add_cafe_form", clear_on_submit=True):
        new_name = st.text_input("카페명 (예: 스타벅스 OO점)")
        new_address = st.text_input("도로명 주소 (예: 서울 용산구 청파로47길 78)")
        new_discount = st.text_input("할인 내용 (예: 텀블러 사용 시 300원 할인)")

        st.markdown("📌 **지도 표시용 좌표** (좌표를 입력하면 지도 상에 마커가 표시됩니다)")
        col_lat, col_lng = st.columns(2)
        with col_lat:
            new_lat = st.number_input("위도 (Latitude, 예: 37.540100)", value=37.550000, format="%.6f")
        with col_lng:
            new_lng = st.number_input("경도 (Longitude, 예: 126.967771)", value=126.980000, format="%.6f")

        submit_cafe = st.form_submit_button("카페 위치 추가하기")

        if submit_cafe:
            if new_name and new_address:
                new_data = pd.DataFrame([{
                    "카페명": new_name,
                    "주소 (도로명 주소)": new_address,
                    "위도": new_lat,
                    "경도": new_lng,
                    "할인 내용": new_discount if new_discount else "텀블러 할인 제공"
                }])

                cafe_df = pd.concat([cafe_df, new_data], ignore_index=True)
                cafe_df.to_csv(CAFE_FILE, index=False)

                st.success(f"'{new_name}' 카페가 지도에 성공적으로 등록되었습니다!")
                st.rerun()
            else:
                st.error("카페명과 주소는 필수 입력 사항입니다.")
