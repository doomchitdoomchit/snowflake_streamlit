import streamlit as st

from src.data_loader import load_mart_data

st.set_page_config(page_title="글로벌 커머스 BI 대시보드", layout="wide")
st.title("글로벌 커머스 BI 대시보드 - Home")

with st.spinner("데이터 마트 뷰 로딩 중..."):
    try:
        raw_df = load_mart_data()
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        st.stop()

with st.expander("데이터 미리보기"):
    st.dataframe(raw_df.head(50), width="stretch")
    st.caption(f"행 수: {len(raw_df):,}")
################################################################################
# 지표 종합
################################################################################
st.markdown(
    """
    <style>
    /* Home KPI: 세로 간격 축소 */
    div[data-testid="stMain"] h3, div[data-testid="stMain"] h4 {
        margin: 0.35rem 0 0.1rem 0 !important;
        padding: 0 !important;
    }
    div[data-testid="stMain"] [data-testid="stMetric"] {
        padding: 0.1rem 0 !important;
    }
    div[data-testid="stMain"] [data-testid="stHorizontalBlock"] {
        gap: 0.5rem !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    div[data-testid="stMain"] [data-testid="stVerticalBlock"] {
        gap: 0.35rem !important;
    }
    div[data-testid="stMain"] hr {
        margin: 0.25rem 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

display_df = raw_df

# --- Page 1: 비즈니스 매출 트렌드 ---
monthly_df = (
    display_df.groupby("CONFIRMED_MONTH")
    .agg({"TOTAL_NET_REVENUE": "sum", "TOTAL_ORDERS": "sum", "TOTAL_ITEMS_SOLD": "sum"})
    .reset_index()
    .sort_values("CONFIRMED_MONTH")
)
monthly_df["AOV"] = monthly_df["TOTAL_NET_REVENUE"] / monthly_df["TOTAL_ORDERS"]
monthly_df["REVENUE_MOM_PCT"] = monthly_df["TOTAL_NET_REVENUE"].pct_change() * 100

st.markdown("#### 📈 비즈니스 매출 트렌드")
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
    st.metric(label="누적 총 주문 건수", value=f"{display_df['TOTAL_ORDERS'].sum():,} 건")
with kpi3:
    st.metric(label="종합 주문당 평균 결제액 (AOV)", value=f"${overall_aov:,.2f}")
with kpi4:
    st.metric(label="누적 총 판매 아이템 수", value=f"{display_df['TOTAL_ITEMS_SOLD'].sum():,} 개")

# --- Page 2: 고객 세그먼트 및 행동 분석 ---
segment_df = display_df.groupby("PART_MATERIAL").agg(
    {
        "TOTAL_NET_REVENUE": "sum",
        "TOTAL_ORDERS": "sum",
        "TOTAL_ITEMS_SOLD": "sum",
        "TOTAL_RETURNED_ITEMS": "sum",
    }
).reset_index()
segment_df["ITEMS_PER_ORDER"] = segment_df["TOTAL_ITEMS_SOLD"] / segment_df["TOTAL_ORDERS"]
segment_df["RETURN_RATE"] = (
    segment_df["TOTAL_RETURNED_ITEMS"] / segment_df["TOTAL_ITEMS_SOLD"]
) * 100

st.markdown("#### 👥 고객 세그먼트 및 행동 분석")
m_col1, m_col2, m_col3 = st.columns(3)
top_segment = segment_df.sort_values("TOTAL_NET_REVENUE", ascending=False).iloc[0]["PART_MATERIAL"]
bulk_segment = segment_df.sort_values("ITEMS_PER_ORDER", ascending=False).iloc[0]["PART_MATERIAL"]
risk_segment = segment_df.sort_values("RETURN_RATE", ascending=False).iloc[0]["PART_MATERIAL"]

with m_col1:
    st.metric(label="⭐ 최고 매출 기여 세그먼트 (VIP)", value=top_segment)
with m_col2:
    st.metric(
        label="📦 건당 대량 구매 세그먼트",
        value=bulk_segment,
        delta=f"{segment_df.sort_values('ITEMS_PER_ORDER', ascending=False).iloc[0]['ITEMS_PER_ORDER']:.1f}개 / 주문",
    )
with m_col3:
    st.metric(
        label="⚠️ 반품 주의 리스크 세그먼트",
        value=risk_segment,
        delta=f"{segment_df.sort_values('RETURN_RATE', ascending=False).iloc[0]['RETURN_RATE']:.2f}% (반품률)",
        delta_color="inverse",
    )

# --- Page 3: 상품 마진 및 프로모션 성과 ---
display_df_p3 = display_df.copy()
display_df_p3["PART_MANUFACTURER"] = display_df_p3["PART_BRAND"].apply(
    lambda x: f"Manufacturer #{x.split('#')[1][0]}" if "#" in str(x) else "Other Mfg"
)
mfg_df = display_df_p3.groupby("PART_MANUFACTURER").agg(
    {"TOTAL_NET_REVENUE": "sum", "TOTAL_ITEMS_SOLD": "sum", "AVG_DISCOUNT_PERCENT": "mean"}
).reset_index()
mfg_df["REVENUE_SHARE_PCT"] = (
    mfg_df["TOTAL_NET_REVENUE"] / mfg_df["TOTAL_NET_REVENUE"].sum()
) * 100

st.markdown("#### 🏷️ 상품 마진 및 프로모션 성과")
p_col1, p_col2, p_col3, p_col4 = st.columns(4)
avg_discount = display_df_p3["AVG_DISCOUNT_PERCENT"].mean()
top_mfg = mfg_df.sort_values("TOTAL_NET_REVENUE", ascending=False).iloc[0]["PART_MANUFACTURER"]
top_mfg_share = mfg_df.sort_values("TOTAL_NET_REVENUE", ascending=False).iloc[0]["REVENUE_SHARE_PCT"]
total_gross = display_df_p3["TOTAL_GROSS_REVENUE"].sum()
total_net = display_df_p3["TOTAL_NET_REVENUE"].sum()
retention_rate = (total_net / total_gross) * 100

with p_col1:
    st.metric(label="📉 전사 평균 프로모션 할인율", value=f"{avg_discount:.2f} %")
with p_col2:
    st.metric(label="👑 시장 지배 제조사", value=top_mfg, delta=f"{top_mfg_share:.1f}% 점유")
with p_col3:
    st.metric(label="💰 프로모션 매출 방어율(Net/Gross)", value=f"{retention_rate:.1f} %")
with p_col4:
    st.metric(label="🏷️ 활성 분석 브랜드 라인업 수", value=f"{display_df_p3['PART_BRAND'].nunique()} 개")

# --- Page 4: SCM 및 물류 파이프라인 최적화 ---
region_logistics = display_df.groupby("CUSTOMER_REGION").agg(
    {
        "TOTAL_ITEMS_SOLD": "sum",
        "AVG_DELIVERY_LEAD_TIME_DAYS": "mean",
        "TOTAL_RETURNED_ITEMS": "sum",
    }
).reset_index()
global_avg_lead_time = display_df["AVG_DELIVERY_LEAD_TIME_DAYS"].mean()

st.markdown("#### 🚚 SCM 및 물류 파이프라인 최적화")
l_col1, l_col2, l_col3, l_col4 = st.columns(4)
bottleneck_region = region_logistics.sort_values(
    "AVG_DELIVERY_LEAD_TIME_DAYS", ascending=False
).iloc[0]["CUSTOMER_REGION"]
bottleneck_days = region_logistics.sort_values(
    "AVG_DELIVERY_LEAD_TIME_DAYS", ascending=False
).iloc[0]["AVG_DELIVERY_LEAD_TIME_DAYS"]
efficient_region = region_logistics.sort_values(
    "AVG_DELIVERY_LEAD_TIME_DAYS", ascending=True
).iloc[0]["CUSTOMER_REGION"]
efficient_days = region_logistics.sort_values(
    "AVG_DELIVERY_LEAD_TIME_DAYS", ascending=True
).iloc[0]["AVG_DELIVERY_LEAD_TIME_DAYS"]

with l_col1:
    st.metric(
        label="🌐 전사 평균 배송 소요 기간 (Global Lead Time)",
        value=f"{global_avg_lead_time:.1f} 일",
    )
with l_col2:
    st.metric(
        label="⚠️ 최대 병목 대륙",
        value=bottleneck_region,
        delta=f"{bottleneck_days:.1f} 일 소요",
        delta_color="inverse",
    )
with l_col3:
    st.metric(label="🚢 총 물동량 (판매 아이템 수)", value=f"{display_df['TOTAL_ITEMS_SOLD'].sum():,} 개")
with l_col4:
    st.metric(
        label="⚡ 최적 물류 대륙",
        value=efficient_region,
        delta=f"{efficient_days:.1f} 일 소요",
    )

# --- Page 5: SCM 리스크 관리 및 종합 진단 ---
total_items = display_df["TOTAL_ITEMS_SOLD"].sum()
total_returns = display_df["TOTAL_RETURNED_ITEMS"].sum()
global_return_rate = (total_returns / total_items) * 100 if total_items > 0 else 0
risk_product = display_df.groupby(["PART_MATERIAL", "PART_BRAND"]).agg(
    {
        "TOTAL_ITEMS_SOLD": "sum",
        "TOTAL_RETURNED_ITEMS": "sum",
        "AVG_DELIVERY_LEAD_TIME_DAYS": "mean",
    }
).reset_index()
risk_product["RETURN_RATE"] = (
    risk_product["TOTAL_RETURNED_ITEMS"] / risk_product["TOTAL_ITEMS_SOLD"]
) * 100
worst_brand_row = risk_product.sort_values("RETURN_RATE", ascending=False).iloc[0]

st.markdown("#### ⚠️ SCM 리스크 관리 및 종합 진단")
r_col1, r_col2, r_col3, r_col4 = st.columns(4)
avg_lead = display_df["AVG_DELIVERY_LEAD_TIME_DAYS"].mean()

with r_col1:
    st.metric(label="🚨 종합 반품률 (Total Return Rate)", value=f"{global_return_rate:.2f} %")
with r_col2:
    st.metric(label="📉 누적 반품 처리 건수", value=f"{total_returns:,} 개")
with r_col3:
    st.metric(
        label="🔥 최고 위험 브랜드",
        value=worst_brand_row["PART_BRAND"],
        delta=f"{worst_brand_row['RETURN_RATE']:.2f}% (반품률)",
        delta_color="inverse",
    )
with r_col4:
    st.metric(label="⏳ 평균 물류 대기 시간", value=f"{avg_lead:.1f} 일")

################################################################################
# 지표 설명 및 데이터 출처
################################################################################
with st.expander("지표 설명 및 데이터 출처"):
    st.write("데이터 마트 뷰: `V_MONTHLY_GLOBAL_SALES_MART`")
    st.write("데이터 출처: Snowflake Sample Data (TPC-H) [https://docs.snowflake.com/en/user-guide/sample-data-tpch](https://docs.snowflake.com/en/user-guide/sample-data-tpch)")
