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

# ☕ 단정하고 깔끔한 모던 카페 아이콘 (원하시는 스타일로 URL 선택 가능)
# [옵션 A] 에코 그린 톤의 단정한 커피잔 아이콘
COFFEE_ICON_URL = "https://img.icons8.com/fluency-systems-filled/96/2E7D32/cafe.png"

# [옵션 B] 다크 모던 픽토그램 아이콘을 원하시면 아래 주소의 주석(#)을 해제하고 사용해 주세요.
# COFFEE_ICON_URL = "https://img.icons8.com/material-rounded/96/374151/cafe.png"

# 데이터 불러오기
def load_cafe_data():
    if os.path.exists(CAFE_FILE):
        df = pd.read_csv(CAFE_FILE)
        if "비밀번호" not in df.columns:
            df["비밀번호"] = "1234"
        return df
    return pd.DataFrame(columns=["카페명", "주소 (도로명 주소)", "위도", "경도", "할인 내용", "비밀번호"])

def load_review_data():
    if os.path.exists(REVIEW_FILE):
        df = pd.read_csv(REVIEW_FILE)
        if "비밀번호" not in df.columns:
            df["비밀번호"] = "1234"
        return df
    return pd.DataFrame(columns=["카페명", "작성자", "평점", "후기", "비밀번호"])

cafe_df = load_cafe_data()
review_df = load_review_data()

# 지도용 아이콘 데이터 추가
if not cafe_df.empty and "위도" in cafe_df.columns and "경도" in cafe_df.columns:
    cafe_df["icon_data"] = [{
        "url": COFFEE_ICON_URL,
        "width": 128,
        "height": 128,
        "anchorY": 128
    }] * len(cafe_df)

# 메인 타이틀
st.title("🌱 eㅔ브리띵 에코 맵")
st.caption("텀블러 할인 카페를 확인하고, 자유롭게 후기와 새 에코 스팟을 공유하세요!")

# 탭 구성
tab1, tab2, tab3 = st.tabs(["🗺️ 에코 맵 대시보드", "➕ 카페 직접 추가", "🛠️ 등록 카페 수정/삭제"])

# ==================== [TAB 1] 대시보드 및 후기 ====================
with tab1:
    col_map, col_detail = st.columns([1.8, 1])

    with col_map:
        st.subheader("📍 서울 텀블러 할인 카페 지도")
        st.caption("💡 지도 위 카페 아이콘에 마우스를 올리면 할인 정보와 주소가 표시됩니다.")

        valid_data = cafe_df.dropna(subset=["위도", "경도"]).copy()

        if not valid_data.empty:
            view_state = pdk.ViewState(
                latitude=valid_data["위도"].mean(),
                longitude=valid_data["경도"].mean(),
                zoom=12.5,
                pitch=0
            )

            # 아이콘 레이어 (크기와 스케일을 단정하게 조정)
            icon_layer = pdk.Layer(
                "IconLayer",
                data=valid_data,
                get_icon="icon_data",
                get_size=3.5,
                size_scale=8,
                get_position=["경도", "위도"],
                pickable=True,
                auto_highlight=True
            )

            r = pdk.Deck(
                map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
                layers=[icon_layer],
                initial_view_state=view_state,
                tooltip={
                    "html": "<b>☕ {카페명}</b><br/>"
                            "📍 주소: {주소 (도로명 주소)}<br/>"
                            "🎁 혜택: <span style='color:#2E7D32;'><b>{할인 내용}</b></span>",
                    "style": {
                        "backgroundColor": "#FFFFFF",
                        "color": "#1F2937",
                        "fontSize": "14px",
                        "padding": "12px",
                        "borderRadius": "10px",
                        "boxShadow": "0px 4px 12px rgba(0,0,0,0.15)",
                        "border": "1px solid #E5E7EB"
                    }
                }
            )

            st.pydeck_chart(r, use_container_width=True)
        else:
            st.info("지도에 표시할 데이터가 없습니다.")

    with col_detail:
        st.subheader("☕ 카페 상세 정보 및 후기")

        cafe_list = cafe_df["카페명"].dropna().tolist() if not cafe_df.empty else []

        if cafe_list:
            selected_cafe = st.selectbox("지점(카페) 선택", cafe_list)

            info = cafe_df[cafe_df["카페명"] == selected_cafe].iloc[0]

            st.markdown(f"### **{info['카페명']}**")
            st.markdown(f"📍 **주소:** {info['주소 (도로명 주소)']}")
            st.success(f"🎁 **할인 혜택:** {info['할인 내용']}")

            st.divider()

            # 후기 작성
            st.markdown("💬 **후기 작성하기**")
            with st.form("review_form", clear_on_submit=True):
                user_name = st.text_input("작성자 (닉네임)", value="에코러버")
                password = st.text_input("삭제용 비밀번호 (4자리)", type="password", max_chars=10)
                rating = st.slider("평점", 1, 5, 5)
                review_text = st.text_area("방문 후기 및 텀블러 사용 팁")

                submit_review = st.form_submit_button("후기 등록")

                if submit_review:
                    if review_text.strip() and password.strip():
                        new_rev = pd.DataFrame([{
                            "카페명": selected_cafe,
                            "작성자": user_name,
                            "평점": "⭐" * rating,
                            "후기": review_text,
                            "비밀번호": str(password)
                        }])
                        review_df = pd.concat([review_df, new_rev], ignore_index=True)
                        review_df.to_csv(REVIEW_FILE, index=False)
                        st.success("후기가 등록되었습니다!")
                        st.rerun()
                    else:
                        st.warning("후기 내용과 비밀번호를 모두 입력해 주세요.")

            # 후기 목록 & 삭제 기능
            st.markdown("📖 **등록된 후기**")
            cafe_reviews = review_df[review_df["카페명"] == selected_cafe]

            if not cafe_reviews.empty:
                for idx, r in cafe_reviews.iloc[::-1].iterrows():
                    col_r1, col_r2 = st.columns([4, 1])
                    with col_r1:
                        st.write(f"**{r['작성자']}** ({r['평점']})")
                        st.caption(r["후기"])
                    with col_r2:
                        with st.popover("🗑️ 삭제"):
                            del_pwd = st.text_input("비밀번호 입력", type="password", key=f"del_pwd_{idx}")
                            if st.button("확인 및 삭제", key=f"del_btn_{idx}"):
                                if str(del_pwd) == str(r.get("비밀번호")):
                                    review_df = review_df.drop(idx)
                                    review_df.to_csv(REVIEW_FILE, index=False)
                                    st.success("후기가 삭제되었습니다!")
                                    st.rerun()
                                else:
                                    st.error("비밀번호가 일치하지 않습니다.")
                    st.divider()
            else:
                st.info("아직 등록된 후기가 없습니다. 첫 후기를 올려보세요!")

# ==================== [TAB 2] 위치 직접 추가 ====================
with tab2:
    st.subheader("➕ 새로운 카페 위치 직접 추가하기")

    with st.form("add_cafe_form", clear_on_submit=True):
        new_name = st.text_input("카페명 (예: 스타벅스 OO점)")
        new_address = st.text_input("도로명 주소 (예: 서울 용산구 청파로47길 78)")
        new_discount = st.text_input("할인 내용 (예: 텀블러 사용 시 300원 할인)")
        new_pwd = st.text_input("수정/삭제용 비밀번호", type="password")

        st.markdown("📌 **지도 표시용 좌표**")
        col_lat, col_lng = st.columns(2)
        with col_lat:
            new_lat = st.number_input("위도 (Latitude)", value=37.550000, format="%.6f")
        with col_lng:
            new_lng = st.number_input("경도 (Longitude)", value=126.980000, format="%.6f")

        submit_cafe = st.form_submit_button("카페 위치 추가하기")

        if submit_cafe:
            if new_name and new_address and new_pwd:
                new_data = pd.DataFrame([{
                    "카페명": new_name,
                    "주소 (도로명 주소)": new_address,
                    "위도": new_lat,
                    "경도": new_lng,
                    "할인 내용": new_discount if new_discount else "텀블러 할인 제공",
                    "비밀번호": str(new_pwd)
                }])

                cafe_df = pd.concat([cafe_df, new_data], ignore_index=True)
                cafe_df.to_csv(CAFE_FILE, index=False)

                st.success(f"'{new_name}' 카페가 성공적으로 등록되었습니다!")
                st.rerun()
            else:
                st.error("카페명, 주소, 비밀번호는 필수 입력 사항입니다.")

# ==================== [TAB 3] 카페 정보 수정/삭제 ====================
with tab3:
    st.subheader("🛠️ 등록한 카페 정보 수정 및 삭제")

    if not cafe_df.empty:
        target_cafe = st.selectbox("수정/삭제할 카페 선택", cafe_df["카페명"].tolist())
        target_info = cafe_df[cafe_df["카페명"] == target_cafe].iloc[0]
        target_idx = cafe_df[cafe_df["카페명"] == target_cafe].index[0]

        input_pwd = st.text_input("해당 카페 등록 시 설정한 비밀번호 입력", type="password")

        col_edit, col_delete = st.columns(2)

        with col_edit:
            st.markdown("### ✏️ 카페 정보 수정")
            with st.form("edit_cafe_form"):
                edit_name = st.text_input("카페명", value=target_info["카페명"])
                edit_address = st.text_input("도로명 주소", value=target_info["주소 (도로명 주소)"])
                edit_discount = st.text_input("할인 내용", value=target_info["할인 내용"])
                edit_lat = st.number_input("위도", value=float(target_info["위도"]) if pd.notna(target_info["위도"]) else 37.550000, format="%.6f")
                edit_lng = st.number_input("경도", value=float(target_info["경도"]) if pd.notna(target_info["경도"]) else 126.980000, format="%.6f")

                btn_update = st.form_submit_button("정보 수정 완료")

                if btn_update:
                    if str(input_pwd) == str(target_info.get("비밀번호")):
                        cafe_df.at[target_idx, "카페명"] = edit_name
                        cafe_df.at[target_idx, "주소 (도로명 주소)"] = edit_address
                        cafe_df.at[target_idx, "할인 내용"] = edit_discount
                        cafe_df.at[target_idx, "위도"] = edit_lat
                        cafe_df.at[target_idx, "경도"] = edit_lng
                        cafe_df.to_csv(CAFE_FILE, index=False)
                        st.success("카페 정보가 수정되었습니다!")
                        st.rerun()
                    else:
                        st.error("비밀번호가 올바르지 않습니다.")

        with col_delete:
            st.markdown("### 🗑️ 카페 정보 삭제")
            st.warning("카페를 삭제하면 다시 복구할 수 없습니다.")
            if st.button("카페 완전 삭제하기", type="primary"):
                if str(input_pwd) == str(target_info.get("비밀번호")):
                    cafe_df = cafe_df.drop(target_idx)
                    cafe_df.to_csv(CAFE_FILE, index=False)
                    st.success(f"'{target_cafe}' 카페가 삭제되었습니다.")
                    st.rerun()
                else:
                    st.error("비밀번호가 올바르지 않습니다.")
