import streamlit as st
import pandas as pd


# ==========================================
# 기본 설정
# ==========================================

st.set_page_config(
    page_title="서울 기온 분석",
    page_icon="🌡️",
    layout="wide"
)


# ==========================================
# 제목
# ==========================================

st.title("🌡️ 서울, 언제 가장 더웠을까?")

st.write(
    "두 날짜를 선택하면, 그 기간 동안 평균기온이 가장 높았던 연도를 찾아줍니다."
)


# ==========================================
# 데이터 불러오기
# ==========================================

@st.cache_data
def load_data():

    # seoul.csv가 app.py와 같은 폴더에 있다고 가정
    data = pd.read_csv(
        "seoul.csv",
        encoding="utf-8-sig"
    )

    # 컬럼 이름 앞뒤 공백 제거
    data.columns = data.columns.str.strip()

    # 날짜 앞에 있는 탭(\t)과 공백 제거
    data["날짜"] = (
        data["날짜"]
        .astype(str)
        .str.strip()
    )

    # 날짜를 datetime으로 변환
    data["날짜"] = pd.to_datetime(
        data["날짜"],
        errors="coerce"
    )

    # 기온 데이터를 숫자로 변환
    data["평균기온"] = pd.to_numeric(
        data["평균기온"],
        errors="coerce"
    )

    data["최저기온"] = pd.to_numeric(
        data["최저기온"],
        errors="coerce"
    )

    data["최고기온"] = pd.to_numeric(
        data["최고기온"],
        errors="coerce"
    )

    # 날짜가 제대로 변환되지 않은 행 제거
    data = data.dropna(
        subset=["날짜", "평균기온"]
    )

    # 연도 / 월 / 일 추가
    data["연도"] = data["날짜"].dt.year
    data["월"] = data["날짜"].dt.month
    data["일"] = data["날짜"].dt.day

    return data


df = load_data()


# ==========================================
# 날짜 선택
# ==========================================

st.subheader("📅 비교할 기간을 선택하세요")

col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input(
        "시작 날짜",
        value=pd.Timestamp("2000-06-01").date()
    )

with col2:
    end_date = st.date_input(
        "종료 날짜",
        value=pd.Timestamp("2000-08-31").date()
    )


# 날짜 순서 확인
if start_date > end_date:

    st.error("⚠️ 종료 날짜는 시작 날짜보다 빠를 수 없습니다.")

    st.stop()


# ==========================================
# 선택한 날짜의 월/일 추출
# ==========================================

start_month = start_date.month
start_day = start_date.day

end_month = end_date.month
end_day = end_date.day


# 월일을 숫자로 변환
# 예:
# 6월 1일  → 601
# 8월 31일 → 831
df["월일"] = df["월"] * 100 + df["일"]

start_md = start_month * 100 + start_day
end_md = end_month * 100 + end_day


# ==========================================
# 기간 필터링
# ==========================================

# 일반적인 경우
# 예: 6월 1일 ~ 8월 31일

if start_md <= end_md:

    selected_df = df[
        (df["월일"] >= start_md)
        & (df["월일"] <= end_md)
    ].copy()


# 연도를 넘어가는 경우
# 예: 11월 1일 ~ 2월 28일

else:

    selected_df = df[
        (df["월일"] >= start_md)
        | (df["월일"] <= end_md)
    ].copy()


# ==========================================
# 데이터 확인
# ==========================================

if selected_df.empty:

    st.warning(
        "선택한 기간에 해당하는 데이터가 없습니다."
    )

    st.stop()


# ==========================================
# 연도별 평균기온 계산
# ==========================================

year_result = (
    selected_df
    .groupby("연도")["평균기온"]
    .mean()
    .reset_index()
)


# 컬럼 이름 변경
year_result.columns = [
    "연도",
    "기간평균기온"
]


# 높은 기온 순으로 정렬
year_result = year_result.sort_values(
    "기간평균기온",
    ascending=False
).reset_index(drop=True)


# ==========================================
# 가장 더웠던 해
# ==========================================

hottest_year = int(
    year_result.iloc[0]["연도"]
)

hottest_temperature = float(
    year_result.iloc[0]["기간평균기온"]
)


# ==========================================
# 결과 표시
# ==========================================

st.divider()

st.subheader("🔥 가장 더웠던 해")


result_col1, result_col2 = st.columns(2)

with result_col1:

    st.metric(
        label="가장 더웠던 해",
        value=f"{hottest_year}년"
    )

with result_col2:

    st.metric(
        label="해당 기간 평균기온",
        value=f"{hottest_temperature:.1f} ℃"
    )


st.info(
    f"📌 {start_month}월 {start_day}일부터 "
    f"{end_month}월 {end_day}일까지 비교했을 때 "
    f"**{hottest_year}년**의 평균기온이 가장 높았습니다."
)


# ==========================================
# 연도별 차트
# ==========================================

st.divider()

st.subheader("📊 연도별 기간 평균기온")


# 차트용 데이터
chart_df = (
    year_result
    .sort_values("연도")
    .set_index("연도")
)


st.bar_chart(
    chart_df["기간평균기온"]
)


# ==========================================
# TOP 10
# ==========================================

st.subheader("🏆 가장 더웠던 연도 TOP 10")


top10 = year_result.head(10).copy()

top10["기간평균기온"] = (
    top10["기간평균기온"]
    .round(1)
)


top10.index = range(1, len(top10) + 1)


st.dataframe(
    top10,
    use_container_width=True
)


# ==========================================
# 데이터 정보
# ==========================================

st.divider()

with st.expander("ℹ️ 분석 방법"):

    st.write(
        "선택한 날짜의 월·일을 기준으로 모든 연도의 같은 기간을 비교합니다."
    )

    st.write(
        "예를 들어 6월 1일 ~ 8월 31일을 선택하면 "
        "1908년, 1909년, 1910년 등의 6월 1일 ~ 8월 31일 "
        "평균기온을 각각 계산한 뒤 비교합니다."
    )

    st.write(
        "가장 높은 기간 평균기온을 기록한 연도를 "
        "'가장 더웠던 해'로 선정합니다."
    )
