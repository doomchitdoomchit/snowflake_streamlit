import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data_loader import load_mart_data

st.set_page_config(page_title="Executive Overview", layout="wide")

st.title("📈 비즈니스 매출 트렌드")
st.markdown("`V_MONTHLY_GLOBAL_SALES_MART` 뷰를 활용한 거시적 KPI 모니터링 화면입니다.")

with st.spinner("데이터 로드 중..."):
    try:
        raw_df = load_mart_data()
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        st.stop()

################################################################################
# 데이터 필터링
################################################################################
st.sidebar.header("🗺️ 글로벌 필터")
regions = sorted(raw_df["CUSTOMER_REGION"].unique())
selected_region = st.sidebar.selectbox("분석 대상 대륙 선택", ["전체 대륙"] + regions)

if selected_region != "전체 대륙":
    display_df = raw_df[raw_df["CUSTOMER_REGION"] == selected_region]
else:
    display_df = raw_df

monthly_df = (
    display_df.groupby("CONFIRMED_MONTH")
    .agg(
        {
            "TOTAL_NET_REVENUE": "sum",
            "TOTAL_ORDERS": "sum",
            "TOTAL_ITEMS_SOLD": "sum",
        }
    )
    .reset_index()
    .sort_values("CONFIRMED_MONTH")
)

monthly_df["AOV"] = monthly_df["TOTAL_NET_REVENUE"] / monthly_df["TOTAL_ORDERS"]
monthly_df["REVENUE_MOM_PCT"] = monthly_df["TOTAL_NET_REVENUE"].pct_change() * 100

st.subheader("📌 Key Performance Indicators")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

current_month_sales = monthly_df["TOTAL_NET_REVENUE"].iloc[-1]
last_month_mom = monthly_df["REVENUE_MOM_PCT"].iloc[-1]
overall_aov = display_df["TOTAL_NET_REVENUE"].sum() / display_df["TOTAL_ORDERS"].sum()

with kpi1:
    st.metric(
        label="최근 월 순매출액 (Net Revenue)",
        value=f"${current_month_sales:,.0f}",
        delta=f"{last_month_mom:.2f}% (전월 대비)",
    )
with kpi2:
    st.metric(
        label="누적 총 주문 건수",
        value=f"{display_df['TOTAL_ORDERS'].sum():,} 건",
    )
with kpi3:
    st.metric(
        label="종합 주문당 평균 결제액 (AOV)",
        value=f"${overall_aov:,.2f}",
    )
with kpi4:
    st.metric(
        label="누적 총 판매 아이템 수",
        value=f"{display_df['TOTAL_ITEMS_SOLD'].sum():,} 개",
    )

st.markdown("---")

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📅 월별 순매출 및 AOV(주문당 평균 결제액) 추이")

    fig_dual = go.Figure()
    fig_dual.add_trace(
        go.Bar(
            x=monthly_df["CONFIRMED_MONTH"],
            y=monthly_df["TOTAL_NET_REVENUE"],
            name="순매출액 ($)",
            yaxis="y1",
            marker_color="#1f77b4",
            opacity=0.7,
        )
    )
    fig_dual.add_trace(
        go.Scatter(
            x=monthly_df["CONFIRMED_MONTH"],
            y=monthly_df["AOV"],
            name="AOV ($)",
            yaxis="y2",
            mode="lines+markers",
            line=dict(color="#ff7f0e", width=3),
        )
    )
    fig_dual.update_layout(
        xaxis=dict(title="주문 월"),
        yaxis=dict(
            title=dict(text="총 순매출액 ($)", font=dict(color="#1f77b4")),
            tickfont=dict(color="#1f77b4"),
        ),
        yaxis2=dict(
            title=dict(text="주문당 평균 결제액 ($)", font=dict(color="#ff7f0e")),
            tickfont=dict(color="#ff7f0e"),
            anchor="x",
            overlaying="y",
            side="right",
        ),
        template="plotly_white",
        legend=dict(x=0.01, y=0.99, orientation="h"),
    )
    st.plotly_chart(fig_dual, width="stretch")

with col_right:
    st.subheader("🌍 국가별 누적 순매출 비교")

    nation_df = display_df.groupby("CUSTOMER_NATION")["TOTAL_NET_REVENUE"].sum().reset_index()
    nation_df = nation_df.sort_values("TOTAL_NET_REVENUE", ascending=True)

    fig_nation = px.bar(
        nation_df,
        x="TOTAL_NET_REVENUE",
        y="CUSTOMER_NATION",
        orientation="h",
        labels={"TOTAL_NET_REVENUE": "총 순매출 ($)", "CUSTOMER_NATION": "국가"},
        template="plotly_white",
        color="TOTAL_NET_REVENUE",
        color_continuous_scale=px.colors.sequential.Viridis,
    )
    fig_nation.update_layout(showlegend=False)
    st.plotly_chart(fig_nation, width="stretch")

with st.expander("👀 Page 1 요약 데이터프레임 보기"):
    st.dataframe(
        monthly_df.sort_values("CONFIRMED_MONTH", ascending=False),
        width="stretch",
    )
