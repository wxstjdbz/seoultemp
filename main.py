import streamlit as st
import pandas as pd
from pathlib import Path


# -----------------------------
# 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="서울 기온 비교",
    page_icon="🌡️",
    layout="wide"
)


# -----------------------------
# CSS
# -----------------------------
st.markdown("""
<style>
    .main {
        background-color: #f8fafc;
    }

    .title {
        font-size: 42px;
        font-weight: 800;
        color: #172033;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 17px;
        color: #64748b;
        margin-bottom: 30px;
    }

    .result-card {
        padding: 28px;
        border-radius: 18px;
        background: linear-gradient(135deg, #fff7ed, #ffedd5);
        border: 1px solid #fed7aa;
        margin: 15px 0 25px 0;
    }

    .result-label {
        font-size: 16px;
        color: #9a3412;
        font-weight: 600;
    }

    .result-year {
        font-size: 48px;
        font-weight: 800;
        color: #c2410c;
        margin: 5px 0;
    }

    .result-temp {
        font-size: 24px;
        font-weight: 700;
        color: #431407;
    }

    .info-card {
        padding: 18px;
        border-radius: 14px;
        background-color: white;
        border: 1px solid #e2e8f0;
        text-align: center;
    }

    .info-number {
        font-size: 25px;
        font-weight: 700;
        color: #0f172a;
    }

    .info-label {
        font-size: 14px;
        color: #64748b;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------
# 제목
# -----------------------------
st.markdown(
    '<div class="title">🌡️ 서울, 언제 가장 더웠을까?</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    '원하는 두 날짜를 선택하면 같은 기간의 기온을 연도별로 비교합니다.'
    '</div>',
    unsafe_allow_html=True
)


# -----------------------------
# 데이터 불러오기
# -----------------------------
file_path = Path("seoul.csv")

if not file_path.exists():
    st.error(
        "seoul.csv 파일을 찾을 수 없습니다. "
        "GitHub 저장소에 app.py와 seoul.csv를 같은 폴더에 올려주세요."
    )
    st.stop()


# 인코딩 자동 대응
try:
    df = pd.read_csv(file_path, encoding="utf-8-sig")
except UnicodeDecodeError:
    try:
        df = pd.read_csv(file_path, encoding="cp949")
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding="euc-kr")


# -----------------------------
# 컬럼 이름 정리
# -----------------------------
df.columns = (
    df.columns
    .astype(str)
    .str.strip()
)


def find_column(columns, candidates):
    """후보 이름 중 실제 데이터에 존재하는 컬럼을 찾음."""
    for candidate in candidates:
        if candidate in columns:
            return candidate

    # 괄호 등의 차이를 고려한 부분 검색
    for col in columns:
        for candidate in candidates:
            if candidate in col:
                return col

    return None


date_col = find_column(
    df.columns,
    ["날짜", "일자", "date", "Date"]
)

avg_col = find_column(
    df.columns,
    ["평균기온", "평균기온(℃)", "평균기온(°C)", "avg_temp"]
)

max_col = find_column(
    df.columns,
    ["최고기온", "최고기온(℃)", "최고기온(°C)", "max_temp"]
)


if date_col is None or avg_col is None:
    st.error(
        "필요한 데이터를 찾을 수 없습니다.\n\n"
        "seoul.csv에 날짜와 평균기온 컬럼이 있는지 확인해주세요."
    )
    st.stop()


# -----------------------------
# 데이터 전처리
# -----------------------------
df[date_col] = (
    df[date_col]
    .astype(str)
    .str.strip()
)

df[date_col] = pd.to_datetime(
    df[date_col],
    errors="coerce"
)

df[avg_col] = pd.to_numeric(
    df[avg_col],
    errors="coerce"
)

if max_col is not None:
    df[max_col] = pd.to_numeric(
        df[max_col],
        errors="coerce"
    )

df = df.dropna(
    subset=[date_col, avg_col]
).copy()

df["연도"] = df[date_col].dt.year
df["월"] = df[date_col].dt.month
df["일"] = df[date_col].dt.day


# -----------------------------
# 날짜 선택
# -----------------------------
st.subheader("📅 비교할 기간")

col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input(
        "시작 날짜",
        value=pd.Timestamp("06-01").date()
    )

with col2:
    end_date = st.date_input(
        "종료 날짜",
        value=pd.Timestamp("08-31").date()
    )


# 날짜 순서 확인
if start_date > end_date:
    st.error("종료 날짜는 시작 날짜보다 빠를 수 없습니다.")
    st.stop()


# -----------------------------
# 월/일 기준으로 기간 필터링
# -----------------------------
start_month_day = start_date.month * 100 + start_date.day
end_month_day = end_date.month * 100 + end_date.day

df["월일숫자"] = df["월"] * 100 + df["일"]


if start_month_day <= end_month_day:

    selected = df[
        (df["월일숫자"] >= start_month_day)
        & (df["월일숫자"] <= end_month_day)
    ].copy()

else:
    # 예: 11월 1일 ~ 2월 28일처럼 연도를 넘어가는 경우
    selected = df[
        (df["월일숫자"] >= start_month_day)
        | (df["월일숫자"] <= end_month_day)
    ].copy()


if selected.empty:
    st.warning("선택한 기간에 해당하는 데이터가 없습니다.")
    st.stop()


# -----------------------------
# 연도별 평균기온 계산
# -----------------------------
yearly = (
    selected
    .groupby("연도")
    .agg(
        기간평균기온=(avg_col, "mean"),
        관측일수=(avg_col, "count")
    )
    .reset_index()
)

yearly = yearly.sort_values(
    "기간평균기온",
    ascending=False
)


if yearly.empty:
    st.warning("비교할 수 있는 연도별 데이터가 없습니다.")
    st.stop()


# 가장 더웠던 해
hottest = yearly.iloc[0]

hottest_year = int(hottest["연도"])
hottest_temp = float(hottest["기간평균기온"])


# -----------------------------
# 결과 카드
# -----------------------------
st.markdown(
    f"""
    <div class="result-card">
        <div class="result-label">
            선택한 기간의 평균기온이 가장 높았던 해
        </div>
        <div class="result-year">
            {hottest_year}년
        </div>
        <div class="result-temp">
            기간 평균기온 {hottest_temp:.1f}℃
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# -----------------------------
# 요약 정보
# -----------------------------
info1, info2, info3 = st.columns(3)

with info1:
    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-number">
                {start_date.strftime("%m월 %d일")}
            </div>
            <div class="info-label">시작 날짜</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with info2:
    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-number">
                {end_date.strftime("%m월 %d일")}
            </div>
            <div class="info-label">종료 날짜</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with info3:
    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-number">
                {len(yearly):,}개 연도
            </div>
            <div class="info-label">비교한 연도 수</div>
        </div>
        """,
        unsafe_allow_html=True
    )


st.write("")


# -----------------------------
# 연도별 차트
# -----------------------------
st.subheader("📊 연도별 기간 평균기온")

chart_data = (
    yearly
    .sort_values("연도")
    .set_index("연도")[["기간평균기온"]]
)

st.bar_chart(
    chart_data,
    y="기간평균기온",
    use_container_width=True
)


# -----------------------------
# 상위 10개 연도
# -----------------------------
st.subheader("🔥 가장 더웠던 연도 TOP 10")

top10 = yearly.head(10).copy()

top10["연도"] = top10["연도"].astype(int)

top10["기간 평균기온"] = (
    top10["기간평균기온"]
    .round(1)
    .map(lambda x: f"{x:.1f}℃")
)

top10["관측일수"] = (
    top10["관측일수"]
    .astype(int)
)

display_df = top10[
    ["연도", "기간 평균기온", "관측일수"]
].reset_index(drop=True)

display_df.index = display_df.index + 1

st.dataframe(
    display_df,
    use_container_width=True
)


# -----------------------------
# 데이터 설명
# -----------------------------
with st.expander("ℹ️ 분석 방법"):
    st.write(
        "선택한 날짜 구간을 각 연도에 동일하게 적용한 뒤, "
        "해당 기간의 일평균기온을 연도별로 평균냈습니다. "
        "그 값이 가장 높은 연도를 '가장 더웠던 해'로 표시합니다."
    )

    st.write(
        "예를 들어 6월 1일~8월 31일을 선택하면 "
        "각 연도의 6월 1일~8월 31일 평균기온을 비교합니다."
    )
