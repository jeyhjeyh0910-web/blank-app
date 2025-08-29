#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

#######################
# Page configuration
st.set_page_config(
    page_title="Titanic Survival Dashboard",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)
alt.themes.enable("default")

#######################
# CSS styling
st.markdown("""
<style>
/* 전체 레이아웃 여백 */
[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}
[data-testid="stVerticalBlock"] {
    padding-left: 0rem;
    padding-right: 0rem;
}

/* ===== st.metric 카드 스타일 (배경 흰색 + 중앙정렬) ===== */
[data-testid="stMetric"]{
    background-color:#ffffff !important;
    border:1px solid #e9ecef;
    border-radius:10px;
    padding:20px;
    box-shadow:0 1px 3px rgba(0,0,0,.06);

    display:flex;
    flex-direction:column;
    justify-content:center;   /* 세로 중앙 정렬 */
    align-items:center;       /* 가로 중앙 정렬 */
    text-align:center;
}

/* 라벨/값/델타 텍스트 */
[data-testid="stMetricLabel"] * { color:#111 !important; }
[data-testid="stMetricValue"]   { color:#111 !important; font-weight:700 !important; text-align:center; }
[data-testid="stMetricDelta"]   { font-weight:600 !important; text-align:center; }

/* 델타 아이콘 중앙 정렬 */
[data-testid="stMetricDeltaIcon-Up"],
[data-testid="stMetricDeltaIcon-Down"]{
    position: relative;
    left: 50%;
    transform: translateX(-50%);
}

/* 구분선 여백 */
.divider { margin: 0.75rem 0 1rem 0; border-top: 1px solid #eee; }
</style>
""", unsafe_allow_html=True)

#######################
# Load data
df_reshaped = pd.read_csv('titanic.csv')  # 분석 데이터

#######################
# Sidebar
with st.sidebar:
    st.header("Titanic Survival Dashboard")
    st.caption("필터를 조정해 현재 조건에 맞는 생존 분석을 확인하세요.")

    # ---- 원본 데이터 사본 & 파생컬럼
    df = df_reshaped.copy()
    df["FamilySize"] = df["SibSp"] + df["Parch"]
    df["Embarked_filled"] = df["Embarked"].fillna("Unknown")

    # ---- 기본 범위 계산 (NaN 제외)
    age_min, age_max = int(df["Age"].dropna().min()), int(df["Age"].dropna().max())
    fare_min, fare_max = float(df["Fare"].min()), float(df["Fare"].max())
    fam_min, fam_max = int(df["FamilySize"].min()), int(df["FamilySize"].max())

    # ---- 필터 위젯
    st.subheader("필터")
    sel_pclass = st.multiselect(
        "객실 등급 (Pclass)",
        options=sorted(df["Pclass"].unique().tolist()),
        default=sorted(df["Pclass"].unique().tolist()),
    )
    sel_sex = st.multiselect(
        "성별 (Sex)",
        options=sorted(df["Sex"].unique().tolist()),
        default=sorted(df["Sex"].unique().tolist()),
    )
    sel_embarked = st.multiselect(
        "승선 항구 (Embarked)",
        options=sorted(df["Embarked_filled"].unique().tolist()),
        default=sorted(df["Embarked_filled"].unique().tolist()),
        help="결측치는 'Unknown'으로 처리됩니다.",
    )
    age_rng = st.slider(
        "나이 범위 (Age)",
        min_value=age_min, max_value=age_max,
        value=(age_min, age_max), step=1
    )
    fare_rng = st.slider(
        "운임 범위 (Fare)",
        min_value=float(round(fare_min, 2)), max_value=float(round(fare_max, 2)),
        value=(float(round(fare_min, 2)), float(round(fare_max, 2)))
    )
    fam_rng = st.slider(
        "동승 가족 수 (SibSp + Parch)",
        min_value=fam_min, max_value=fam_max,
        value=(fam_min, fam_max), step=1
    )

    # ---- 필터 적용
    mask = (
        df["Pclass"].isin(sel_pclass)
        & df["Sex"].isin(sel_sex)
        & df["Embarked_filled"].isin(sel_embarked)
        & df["FamilySize"].between(fam_rng[0], fam_rng[1])
        & df["Fare"].between(fare_rng[0], fare_rng[1])
    )
    # Age는 NaN이 많아 범위 필터는 값이 있는 행에만 적용
    age_ok = (df["Age"].between(age_rng[0], age_rng[1])) | (df["Age"].isna())
    df_filtered = df[mask & age_ok].copy()

    # ---- 테마/옵션
    st.subheader("시각화 옵션")
    plotly_theme = st.selectbox(
        "Plotly 테마",
        options=["plotly", "plotly_dark", "ggplot2", "seaborn", "simple_white"],
        index=0,
    )
    altair_scheme = st.selectbox(
        "Altair 색상 스킴",
        options=["tableau10", "category10", "set2", "pastel1"],
        index=0,
    )

    st.markdown("---")
    st.metric("필터링된 승객 수", len(df_filtered))
    st.caption("※ df_filtered, plotly_theme, altair_scheme 변수를 아래 섹션에서 사용하세요.")

#######################
# Dashboard Main Panel
col = st.columns((1.5, 4.5, 2), gap='medium')

# ======================
# 왼쪽: 요약 지표
# ======================
with col[0]:
    st.subheader("요약 지표")

    total_passengers = len(df_filtered)
    survived_count = int(df_filtered["Survived"].sum())
    dead_count = total_passengers - survived_count
    survived_rate = (survived_count / total_passengers * 100) if total_passengers > 0 else 0
    dead_rate = (dead_count / total_passengers * 100) if total_passengers > 0 else 0
    avg_age = round(df_filtered["Age"].mean(skipna=True), 1) if total_passengers > 0 else 0
    avg_fare = round(df_filtered["Fare"].mean(), 2) if total_passengers > 0 else 0
    avg_family = round(df_filtered["FamilySize"].mean(), 1) if total_passengers > 0 else 0

    st.metric("총 승객 수", total_passengers)
    st.metric("생존자 수", f"{survived_count}명", f"{survived_rate:.1f}%")
    st.metric("사망자 수", f"{dead_count}명", f"{dead_rate:.1f}%")
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.metric("평균 나이", f"{avg_age} 세")
    st.metric("평균 운임", f"${avg_fare}")
    st.metric("평균 가족 수", f"{avg_family}")

# ======================
# 가운데: 세 개 그래프를 동시에 표시
# ======================
with col[1]:
    st.subheader("메인 시각화")

    if "df_filtered" not in locals() or df_filtered.empty:
        st.warning("현재 필터 조건에 맞는 데이터가 없습니다. 사이드바에서 조건을 조정해 주세요.")
    else:
        # Plotly 전역 테마 적용
        px.defaults.template = plotly_theme

        # --------- 그래프 1: 성별·등급별 생존율 (막대) ----------
        st.markdown("### 1) 성별·등급별 생존율")
        g = (
            df_filtered.groupby(["Pclass", "Sex"])
            .agg(SurvivalRate=("Survived", lambda s: s.mean() * 100),
                 Count=("PassengerId", "count"))
            .reset_index()
        )
        fig_bar = px.bar(
            g,
            x="Pclass", y="SurvivalRate", color="Sex",
            barmode="group",
            text=g["SurvivalRate"].round(1).astype(str) + "%",
            hover_data=["Count"],
            labels={"Pclass": "등급", "SurvivalRate": "생존율(%)", "Sex": "성별", "Count": "표본수"},
            title="성별·등급별 생존율"
        )
        fig_bar.update_traces(textposition="outside")
        fig_bar.update_layout(yaxis_range=[0, 100])
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # --------- 그래프 2: 연령대 × 등급 히트맵 (Altair) ----------
        st.markdown("### 2) 연령대 × 등급 히트맵")
        bins = [0,10,20,30,40,50,60,70,80]
        labels = ["0대","10대","20대","30대","40대","50대","60대","70대"]
        df_age = df_filtered.dropna(subset=["Age"]).copy()
        df_age["AgeGroup"] = pd.cut(df_age["Age"], bins=bins, labels=labels, right=False)

        heat = (
            df_age.groupby(["AgeGroup","Pclass"])
            .agg(SurvivalRate=("Survived", lambda s: s.mean()*100),
                 Count=("PassengerId","count"))
            .reset_index()
        )

        base = alt.Chart(heat).encode(
            x=alt.X("Pclass:N", title="등급"),
            y=alt.Y("AgeGroup:N", title="연령대", sort=labels),
        )
        heatmap = base.mark_rect().encode(
            color=alt.Color("SurvivalRate:Q",
                            title="생존율(%)",
                            scale=alt.Scale(domain=[0,100], scheme=altair_scheme))
        ).properties(
            width="container", height=360, title="연령대 × 등급별 생존율 히트맵"
        )
        text = base.mark_text().encode(
            text=alt.Text("SurvivalRate:Q", format=".1f"),
            color=alt.value("black")
        )
        st.altair_chart(heatmap + text, use_container_width=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # --------- 그래프 3: 운임 vs 나이 (생존 여부) 산점도 ----------
        st.markdown("### 3) 운임 vs 나이 (생존 여부/등급)")
        df_scatter = df_filtered.dropna(subset=["Age", "Fare"]).copy()
        df_scatter["SurvivedLabel"] = df_scatter["Survived"].map({1:"Survived", 0:"Died"})
        fig_scatter = px.scatter(
            df_scatter,
            x="Age", y="Fare", color="SurvivedLabel", symbol="Pclass",
            hover_data=["Sex","Pclass","Embarked"],
            labels={"Age":"나이", "Fare":"운임", "SurvivedLabel":"생존 여부", "Pclass":"등급"},
            title="운임 vs 나이 (생존 여부/등급)"
        )
        fig_scatter.update_traces(marker=dict(size=8, opacity=0.7))
        st.plotly_chart(fig_scatter, use_container_width=True)

# ======================
# 오른쪽: 세부 분석
# ======================
with col[2]:
    st.subheader("세부 분석")

    if "df_filtered" not in locals() or df_filtered.empty:
        st.info("현재 조건에 맞는 데이터가 없어 상세 분석을 표시할 수 없습니다.")
    else:
        grp = (
            df_filtered.groupby(["Pclass","Sex"])
            .agg(SurvivalRate=("Survived", lambda s: s.mean()*100),
                 Count=("PassengerId","count"),
                 AvgAge=("Age","mean"),
                 AvgFare=("Fare","mean"))
            .reset_index()
            .sort_values("SurvivalRate", ascending=False)
        )

        st.markdown("**생존율 Top 3 그룹**")
        st.dataframe(grp.head(3).style.format({
            "SurvivalRate":"{:.1f}%",
            "AvgAge":"{:.1f}",
            "AvgFare":"${:.2f}"
        }))

        st.markdown("**생존율 Bottom 3 그룹**")
        st.dataframe(grp.tail(3).style.format({
            "SurvivalRate":"{:.1f}%",
            "AvgAge":"{:.1f}",
            "AvgFare":"${:.2f}"
        }))

        st.markdown("---")
        st.markdown("**추가 인사이트**")
        top_group = grp.iloc[0]
        bottom_group = grp.iloc[-1]
        st.write(
            f"📌 **가장 높은 생존율 그룹:** {top_group['Sex']} / {top_group['Pclass']}등석 "
            f"→ 생존율 {top_group['SurvivalRate']:.1f}%"
        )
        st.write(
            f"📌 **가장 낮은 생존율 그룹:** {bottom_group['Sex']} / {bottom_group['Pclass']}등석 "
            f"→ 생존율 {bottom_group['SurvivalRate']:.1f}%"
        )

        st.markdown("---")
        st.caption("데이터 출처: Kaggle Titanic Dataset")
        st.caption("Survived: 1 = 생존, 0 = 사망")
