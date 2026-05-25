import plotly.express as px
import streamlit as st

from src.data_loader import load_mart_data

st.set_page_config(page_title="Risk & Operations", layout="wide")

st.title("⚠️ SCM 리스크 관리 및 운영 종합 진단")
st.markdown("`V_MONTHLY_GLOBAL_SALES_MART` 뷰를 기반으로 반품 패턴과 물류 배송 지연 간의 복합 위험 요소를 스크리닝합니다.")

with st.spinner("데이터 로드 중..."):
    try:
        raw_df = load_mart_data()
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        st.stop()

# -------------------------------------------------------------------
# 2. 필터 바
# -------------------------------------------------------------------

# 사이드바 필터: 특정 대륙별 리스크만 추려볼 수 있도록 세팅
st.sidebar.header("🚨 리스크 필터링")
regions = sorted(raw_df['CUSTOMER_REGION'].unique())
selected_region = st.sidebar.selectbox("대륙 선택", ["전체 대륙"] + regions)

if selected_region != "전체 대륙":
    display_df = raw_df[raw_df['CUSTOMER_REGION'] == selected_region]
else:
    display_df = raw_df

# -------------------------------------------------------------------
# 3. 리스크 분석 매트릭 연산
# -------------------------------------------------------------------
# 전체 누적 값 연산
total_items = display_df['TOTAL_ITEMS_SOLD'].sum()
total_returns = display_df['TOTAL_RETURNED_ITEMS'].sum()
global_return_rate = (total_returns / total_items) * 100 if total_items > 0 else 0

# 상품 재질(Material) 및 브랜드별 리스크 그루핑
risk_product = display_df.groupby(['PART_MATERIAL', 'PART_BRAND']).agg({
    'TOTAL_ITEMS_SOLD': 'sum',
    'TOTAL_RETURNED_ITEMS': 'sum',
    'AVG_DELIVERY_LEAD_TIME_DAYS': 'mean'
}).reset_index()

# 브랜드별 반품률 계산
risk_product['RETURN_RATE'] = (risk_product['TOTAL_RETURNED_ITEMS'] / risk_product['TOTAL_ITEMS_SOLD']) * 100

# -------------------------------------------------------------------
# 4. 상단 SCM 리스크 KPI 대시보드 (Metrics)
# -------------------------------------------------------------------
st.subheader("📌 핵심 운영 리스크 지표")
r_col1, r_col2, r_col3, r_col4 = st.columns(4)

# 가장 반품율이 높은 문제 브랜드 추출
worst_brand_row = risk_product.sort_values('RETURN_RATE', ascending=False).iloc[0]

with r_col1:
    st.metric(label="🚨 종합 반품률 (Total Return Rate)", value=f"{global_return_rate:.2f} %")
with r_col2:
    st.metric(label="📉 누적 반품 처리 건수", value=f"{total_returns:,} 개")
with r_col3:
    st.metric(label="🔥 최고 위험 브랜드", value=worst_brand_row['PART_BRAND'], delta=f"{worst_brand_row['RETURN_RATE']:.2f}% (반품률)", delta_color="inverse")
with r_col4:
    # 반품 건당 평균 물류 지연일
    avg_lead = display_df['AVG_DELIVERY_LEAD_TIME_DAYS'].mean()
    st.metric(label="⏳ 평균 물류 대기 시간", value=f"{avg_lead:.1f} 일")

st.markdown("---")

# -------------------------------------------------------------------
# 5. 메인 시각화 차트 (반품 리스크 Heatmap & 리드타임 상관분석)
# -------------------------------------------------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🧱 상품 재질 x 브랜드별 반품 위험도 매트릭스 (Heatmap)")
    st.markdown("어떤 상품 조합에서 반품 불량률이 집중적으로 발생하는지 매트릭스로 추적합니다.")
    
    # 피벗 테이블을 생성하여 히트맵용 격자 데이터 빌드
    pivot_df = risk_product.pivot(index='PART_MATERIAL', columns='PART_BRAND', values='RETURN_RATE').fillna(0)
    
    fig_heat = px.imshow(
        pivot_df,
        labels=dict(x="상품 브랜드", y="상품 재질", color="반품률 (%)"),
        x=pivot_df.columns,
        y=pivot_df.index,
        color_continuous_scale="Reds", # 리스크 직관성을 위해 레드 스케일 적용
        template="plotly_white"
    )
    st.plotly_chart(fig_heat, width="stretch")

with col_right:
    st.subheader("🔍 배송 소요 기간(Lead Time)과 반품률의 상관관계")
    st.markdown("배송이 지연될수록 고객의 불만이 커져 반품률이 상승하는지 인과관계를 진단합니다.")
    
    # X축: 배송 리드타임, Y축: 반품률, 크기: 총 판매량으로 산점도 구축
    fig_scatter = px.scatter(
        risk_product,
        x='AVG_DELIVERY_LEAD_TIME_DAYS',
        y='RETURN_RATE',
        size='TOTAL_ITEMS_SOLD',
        color='PART_MATERIAL',
        trendline="ols", # 💡 [통계 심층 포인트] 선형 회귀 추세선 자동 추가
        labels={'AVG_DELIVERY_LEAD_TIME_DAYS': '평균 배송 소요 기간 (일)', 'RETURN_RATE': '반품률 (%)'},
        template="plotly_white"
    )
    st.plotly_chart(fig_scatter, width="stretch")

# -------------------------------------------------------------------
# 6. 하단 월별 리스크 타임라인 추이 (Area Chart)
# -------------------------------------------------------------------
st.markdown("---")
st.subheader("📅 월별 반품 아이템 추이 및 리스크 타임라인")

monthly_risk = display_df.groupby('CONFIRMED_MONTH').agg({
    'TOTAL_RETURNED_ITEMS': 'sum',
    'TOTAL_ITEMS_SOLD': 'sum'
}).reset_index().sort_values('CONFIRMED_MONTH')

monthly_risk['MONTHLY_RETURN_RATE'] = (monthly_risk['TOTAL_RETURNED_ITEMS'] / monthly_risk['TOTAL_ITEMS_SOLD']) * 100

fig_area = px.area(
    monthly_risk,
    x='CONFIRMED_MONTH',
    y='MONTHLY_RETURN_RATE',
    labels={'CONFIRMED_MONTH': '기준 월', 'MONTHLY_RETURN_RATE': '월간 반품률 (%)'},
    title="시간 흐름에 따른 반품률 변동 추이",
    template="plotly_white",
    color_discrete_sequence=["#e74c3c"]
)
st.plotly_chart(fig_area, width="stretch")