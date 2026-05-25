import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data_loader import load_mart_data

st.set_page_config(page_title="Product & Marketing", layout="wide")

st.title("🏷️ 상품별 마진 및 프로모션 할인 효과 분석")
st.markdown("제조사별 시장 점유율을 파악하고, 할인율 변동이 순매출에 미치는 영향을 추적합니다.")

with st.spinner("데이터 로드 중..."):
    try:
        raw_df = load_mart_data().copy()
        # Brand#11 -> Manufacturer #1 형태로 제조사 칼럼 파생
        raw_df["PART_MANUFACTURER"] = raw_df["PART_BRAND"].apply(
            lambda x: f"Manufacturer #{x.split('#')[1][0]}" if "#" in str(x) else "Other Mfg"
        )
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        st.stop()

# -------------------------------------------------------------------
# 🎨 2. 기간/대륙 필터
# -------------------------------------------------------------------

# 사이드바 필터
st.sidebar.header("🔍 마케팅 분석 필터")
regions = sorted(raw_df['CUSTOMER_REGION'].unique())
selected_region = st.sidebar.selectbox("대상 대륙 선택", ["전체 대륙"] + regions)

if selected_region != "전체 대륙":
    display_df = raw_df[raw_df['CUSTOMER_REGION'] == selected_region]
else:
    display_df = raw_df

# -------------------------------------------------------------------
# 🧮 3. 데이터 통계 및 비즈니스 메트릭 연산
# -------------------------------------------------------------------
# 제조사별 집계 (점유율용)
mfg_df = display_df.groupby('PART_MANUFACTURER').agg({
    'TOTAL_NET_REVENUE': 'sum',
    'TOTAL_ITEMS_SOLD': 'sum',
    'AVG_DISCOUNT_PERCENT': 'mean'
}).reset_index()

# 💡 마진 구조 분석을 위한 데이터 가공
# 원본 마트의 TOTAL_GROSS_REVENUE(할인 전 원가) 대비 TOTAL_NET_REVENUE(할인 후 판매가) 비율 계산
# 이를 통해 할인으로 인해 양보한 마진율(Discount Impact)을 역산
mfg_df['REVENUE_SHARE_PCT'] = (mfg_df['TOTAL_NET_REVENUE'] / mfg_df['TOTAL_NET_REVENUE'].sum()) * 100

# -------------------------------------------------------------------
# 📊 4. 상단 마케팅 KPI 요약 카드 (Metrics)
# -------------------------------------------------------------------
st.subheader("📌 프로모션 및 브랜드 성과 지표")
p_col1, p_col2, p_col3, p_col4 = st.columns(4)

avg_discount = display_df['AVG_DISCOUNT_PERCENT'].mean()
top_mfg = mfg_df.sort_values('TOTAL_NET_REVENUE', ascending=False).iloc[0]['PART_MANUFACTURER']
top_mfg_share = mfg_df.sort_values('TOTAL_NET_REVENUE', ascending=False).iloc[0]['REVENUE_SHARE_PCT']

with p_col1:
    st.metric(label="📉 전사 평균 프로모션 할인율", value=f"{avg_discount:.2f} %")
with p_col2:
    st.metric(label="👑 시장 지배 제조사", value=top_mfg, delta=f"{top_mfg_share:.1f}% 점유")
with p_col3:
    # 총 매출액(할인 전) 대비 순매출액(할인 후) 비율로 방어한 매출 비율 계산
    total_gross = display_df['TOTAL_GROSS_REVENUE'].sum()
    total_net = display_df['TOTAL_NET_REVENUE'].sum()
    retention_rate = (total_net / total_gross) * 100
    st.metric(label="💰 프로모션 매출 방어율(Net/Gross)", value=f"{retention_rate:.1f} %")
with p_col4:
    st.metric(label="🏷️ 활성 분석 브랜드 라인업 수", value=f"{display_df['PART_BRAND'].nunique()} 개")

st.markdown("---")

# -------------------------------------------------------------------
# 📉 5. 메인 시각화 차트 (시장 점유율 파이 & 할인율 상관관계)
# -------------------------------------------------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🍕 제조사별 시장 점유율 (순매출 기준)")
    # 돈넛 차트로 시장 지배력 시각화
    fig_pie = px.pie(
        mfg_df, 
        names='PART_MANUFACTURER', 
        values='TOTAL_NET_REVENUE',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel,
        template="plotly_white"
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, width="stretch")

with col_right:
    st.subheader("📉 월별 할인율 추이와 매출 민감도 분석")
    # 월별로 할인율과 매출 흐름을 엮어 프로모션의 밸류를 측정
    monthly_promo = display_df.groupby('CONFIRMED_MONTH').agg({
        'TOTAL_NET_REVENUE': 'sum',
        'AVG_DISCOUNT_PERCENT': 'mean'
    }).reset_index().sort_values('CONFIRMED_MONTH')
    
    # 이중 축 그래프로 할인율(Line)과 순매출(Bar)의 동향 비교
    fig_promo = go.Figure()
    fig_promo.add_trace(go.Bar(
        x=monthly_promo['CONFIRMED_MONTH'], y=monthly_promo['TOTAL_NET_REVENUE'],
        name="순매출액 ($)", yaxis="y1", marker_color="#34495e", opacity=0.6
    ))
    fig_promo.add_trace(go.Scatter(
        x=monthly_promo['CONFIRMED_MONTH'], y=monthly_promo['AVG_DISCOUNT_PERCENT'],
        name="평균 할인율 (%)", yaxis="y2", mode="lines+markers", line=dict(color="#e74c3c", width=3)
    ))
    
    fig_promo.update_layout(
        xaxis=dict(title="분석 기준 월"),
        yaxis=dict(
            title=dict(text="총 순매출액 ($)", font=dict(color="#34495e")),
            tickfont=dict(color="#34495e"),
        ),
        yaxis2=dict(
            title=dict(text="평균 할인율 (%)", font=dict(color="#e74c3c")),
            tickfont=dict(color="#e74c3c"),
            anchor="x",
            overlaying="y",
            side="right",
        ),
        template="plotly_white",
        legend=dict(x=0.01, y=0.99, orientation="h"),
    )
    st.plotly_chart(fig_promo, width="stretch")

# -------------------------------------------------------------------
# 📊 6. 하단 세부 브랜드별 마진 리스크 매트릭스 (가로 바 차트)
# -------------------------------------------------------------------
st.markdown("---")
st.subheader("⚡ 브랜드 라인업별 프로모션 잠식 효과 (Top 15 브랜드)")
st.markdown("할인율이 지나치게 높아 매출 단가가 과도하게 깎이고 있는 브랜드를 선별합니다.")

# 브랜드별 정밀 집계
brand_mkt = display_df.groupby(['PART_BRAND', 'PART_MANUFACTURER']).agg({
    'TOTAL_NET_REVENUE': 'sum',
    'AVG_DISCOUNT_PERCENT': 'mean'
}).reset_index()

# 상위 15개 브랜드 필터링
top_brands = brand_mkt.sort_values('TOTAL_NET_REVENUE', ascending=False).head(15)

# X축: 브랜드, Y축: 매출액, 색상: 할인율 강도
fig_brand_bar = px.bar(
    top_brands,
    x='PART_BRAND',
    y='TOTAL_NET_REVENUE',
    color='AVG_DISCOUNT_PERCENT',
    labels={'TOTAL_NET_REVENUE': '총 순매출 ($)', 'PART_BRAND': '브랜드명', 'AVG_DISCOUNT_PERCENT': '평균 할인율(%)'},
    color_continuous_scale=px.colors.sequential.Reds,  # 할인이 심할수록 붉게 표시하여 리스크 시각화
    template="plotly_white"
)
st.plotly_chart(fig_brand_bar, width="stretch")