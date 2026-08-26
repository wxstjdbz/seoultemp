import streamlit as st
import pandas as pd


# ==================================================
# 페이지 설정
# ==================================================

st.set_page_config(
    page_title="서울 기온 분석",
    page_icon="🌡️",
    layout="wide"
)


# ==================================================
# 제목
# ==================================================

st.title("🌡️ 서울, 언제 가장 더웠을까?")

st.write(
    "두 날짜를 선택하면 같은 기간의 평균기온을 연도별로 비교합니다."
)


# ==================================================
# 데이터 불러오기
# ==================================================

@st.cache_data
def load_data():

    # CSV 읽기
    data = pd.read_csv(
        "seoul.csv",
        encoding="utf-8-sig"
    )

    # 컬럼명 공백 제거
    data.columns = data.columns.str.strip()

    # 날짜 앞뒤 공백 및 탭 제거
    data["날짜"] = (
        data["날짜"]
        .astype(str)
        .str.strip()
    )

    # 날짜 변환
    data["날짜"] = pd.to_datetime(
        data["날짜"],
        errors="coerce"
    )

    # 기온 숫자 변환
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

    # 날짜와 평균기온이 없는 행 제거
    data = data.dropna(
        subset=["날짜", "평균기온"]
    ).copy()

    # 연도 / 월 / 일
    data["연도"] = data["날짜"].dt.year
    data["월"] = data["날짜"].dt.month
    data["일"] = data["날짜"].dt.day

    # 월일 숫자
    # 6월 1일 → 601
    # 8월 31일 → 831
    data["월일"] = (
        data["월"] * 100
        + data["일"]
    )

    return data


df = load_data()


# ==================================================
# 데이터의 실제 날짜 범위 확인
# ==================================================

min_date = df["날짜"].min().date()
max_date = df["날짜"].max().date()


# ==================================================
# 날짜 선택
# ==================================================

st.subheader("📅 비교할 기간을 선택하세요")

st.caption(
    f"데이터 기간: {min_date.strftime('%Y년 %m월 %d일')} ~ "
    f"{max_date.strftime('%Y년 %m월 %d일')}"
)


col1, col2 = st.columns(2)


# --------------------------------------------------
# 시작 날짜
# --------------------------------------------------

with col1:

    start_date = st.date_input(
        "시작 날짜",
        value=pd.Timestamp("06-01-2020").date(),
        min_value=min_date,
        max_value=max_date,
        format="YYYY-MM-DD"
    )


# --------------------------------------------------
# 종료 날짜
# --------------------------------------------------

with col2:

    end_date = st.date_input(
        "종료 날짜",
        value=pd.Timestamp("08-31-2020").date(),
        min_value=min_date,
        max_value=max_date,
        format="YYYY-MM-DD"
    )


# ==================================================
# 날짜 오류 확인
# ==================================================

if start_date > end_date:

    st.error(
        "⚠️ 종료 날짜는 시작 날짜보다 빠를 수 없습니다."
    )

    st.stop()


# ==================================================
# 선택한 날짜의 월/일 추출
# ==================================================

start_md = (
    start_date.month * 100
    + start_date.day
)

end_md = (
    end_date.month * 100
    + end_date.day
)


# ==================================================
# 선택 기간 데이터 추출
# ==================================================

# 일반적인 기간
# 예: 6월 1일 ~ 8월 31일

if start_md <= end_md:

    selected_df = df[
        (df["월일"] >= start_md)
        & (df["월일"] <= end_md)
    ].copy()


# 연도를 넘어가는 기간
# 예: 11월 1일 ~ 2월 28일

else:

    selected_df = df[
        (df["월일"] >= start_md)
        | (df["월일"] <= end_md)
    ].copy()


# ==================================================
# 데이터 확인
# ==================================================

if selected_df.empty:

    st.warning(
        "선택한 기간에 해당하는 데이터가 없습니다."
    )

    st.stop()


# ==================================================
# 연도별 평균기온 계산
# ==================================================

year_result = (
    selected_df
    .groupby("연도")["평균기온"]
    .mean()
    .reset_index()
)

year_result.columns = [
    "연도",
    "기간평균기온"
]


# 높은 순으로 정렬
year_result = (
    year_result
    .sort_values(
        "기간평균기온",
        ascending=False
    )
    .reset_index(drop=True)
)


# ==================================================
# 가장 더웠던 해
# ==================================================

hottest_year = int(
    year_result.iloc[0]["연도"]
)

hottest_temperature = float(
    year_result.iloc[0]["기간평균기온"]
)


# ==================================================
# 결과
# ==================================================

st.divider()

st.subheader("🔥 가장 더웠던 해")


col1, col2 = st.columns(2)


with col1:

    st.metric(
        label="가장 더웠던 해",
        value=f"{hottest_year}년"
    )


with col2:

    st.metric(
        label="기간 평균기온",
        value=f"{hottest_temperature:.1f} ℃"
    )


st.success(
    f"🌡️ {start_date.month}월 {start_date.day}일 ~ "
    f"{end_date.month}월 {end_date.day}일을 비교했을 때, "
    f"**{hottest_year}년**이 가장 더웠습니다."
)


# ==================================================
# 연도별 차트
# ==================================================

st.divider()

st.subheader("📊 연도별 기간 평균기온")


chart_df = (
    year_result
    .sort_values("연도")
    .set_index("연도")
)


st.bar_chart(
    chart_df["기간평균기온"],
    use_container_width=True
)


# ==================================================
# TOP 10
# ==================================================

st.subheader("🏆 가장 더웠던 연도 TOP 10")


top10 = year_result.head(10).copy()


top10["연도"] = top10["연도"].astype(int)

top10["기간평균기온"] = (
    top10["기간평균기온"]
    .round(1)
)


top10.index = range(1, len(top10) + 1)


st.dataframe(
    top10,
    use_container_width=True
)


# ==================================================
# 데이터 설명
# ==================================================

st.divider()

with st.expander("ℹ️ 어떻게 계산했나요?"):

    st.write(
        "선택한 두 날짜에서 연도는 제외하고 월·일만 기준으로 "
        "모든 연도의 같은 기간을 비교합니다."
    )

    st.write(
        "예를 들어 6월 1일 ~ 8월 31일을 선택하면 "
        "1907년부터 2026년까지 각각의 6월 1일 ~ 8월 31일 "
        "평균기온을 계산합니다."
    )

    st.write(
        "그중 기간 평균기온이 가장 높은 연도를 "
        "'가장 더웠던 해'로 표시합니다."
    )
