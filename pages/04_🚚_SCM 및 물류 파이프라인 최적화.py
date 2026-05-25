import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data_loader import load_mart_data

st.set_page_config(page_title="Logistics & SCM", layout="wide")

st.title("🚚 SCM 및 물류 파이프라인 리드타임 최적화")
st.markdown("`V_MONTHLY_GLOBAL_SALES_MART` 뷰의 물류 메트릭을 바탕으로 대륙별 배송 소요 기간과 물류 병목 현상을 진단합니다.")

with st.spinner("데이터 로드 중..."):
    try:
        raw_df = load_mart_data()
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        st.stop()

# -------------------------------------------------------------------
# 🎨 2. 공급망 필터
# -------------------------------------------------------------------

# 사이드바 필터: 특정 상품 카테고리(재질)별로 물류 속도가 다른지 비교 가능
st.sidebar.header("📦 물류 분석 필터")
materials = sorted(raw_df['PART_MATERIAL'].unique())
selected_material = st.sidebar.selectbox("분석 상품 재질 선택", ["전체 상품"] + materials)

if selected_material != "전체 상품":
    display_df = raw_df[raw_df['PART_MATERIAL'] == selected_material]
else:
    display_df = raw_df

# -------------------------------------------------------------------
# 🧮 3. SCM 핵심 통계 연산
# -------------------------------------------------------------------
# 글로벌 물류 현황 요약을 위한 대륙별(Region) 그룹화
region_logistics = display_df.groupby('CUSTOMER_REGION').agg({
    'TOTAL_ITEMS_SOLD': 'sum',
    'AVG_DELIVERY_LEAD_TIME_DAYS': 'mean',
    'TOTAL_RETURNED_ITEMS': 'sum'
}).reset_index()

# 글로벌 기준 평균 배송일 계산 (비교용 가이드라인)
global_avg_lead_time = display_df['AVG_DELIVERY_LEAD_TIME_DAYS'].mean()

# -------------------------------------------------------------------
# 📊 4. 상단 물류 파이프라인 KPI 카드 (Metrics)
# -------------------------------------------------------------------
st.subheader("📌 글로벌 물류 파이프라인 핵심 지표")
l_col1, l_col2, l_col3, l_col4 = st.columns(4)

# 가장 배송이 오래 걸리는 병목 대륙 추출
bottleneck_region = region_logistics.sort_values('AVG_DELIVERY_LEAD_TIME_DAYS', ascending=False).iloc[0]['CUSTOMER_REGION']
bottleneck_days = region_logistics.sort_values('AVG_DELIVERY_LEAD_TIME_DAYS', ascending=False).iloc[0]['AVG_DELIVERY_LEAD_TIME_DAYS']

with l_col1:
    st.metric(label="🌐 전사 평균 배송 소요 기간 (Global Lead Time)", value=f"{global_avg_lead_time:.1f} 일")
with l_col2:
    st.metric(label="⚠️ 최대 병목 대륙", value=bottleneck_region, delta=f"{bottleneck_days:.1f} 일 소요", delta_color="inverse")
with l_col3:
    st.metric(label="🚢 총 물동량 (판매 아이템 수)", value=f"{display_df['TOTAL_ITEMS_SOLD'].sum():,} 개")
with l_col4:
    # 가장 배송 속도가 빠른 효율 대륙 추출
    efficient_region = region_logistics.sort_values('AVG_DELIVERY_LEAD_TIME_DAYS', ascending=True).iloc[0]['CUSTOMER_REGION']
    efficient_days = region_logistics.sort_values('AVG_DELIVERY_LEAD_TIME_DAYS', ascending=True).iloc[0]['AVG_DELIVERY_LEAD_TIME_DAYS']
    st.metric(label="⚡ 최적 물류 대륙", value=efficient_region, delta=f"{efficient_days:.1f} 일 소요")

st.markdown("---")

# -------------------------------------------------------------------
# 📉 5. 메인 시각화 차트 (대륙별 리드타임 비교 및 월별 물류 추이)
# -------------------------------------------------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🗺️ 대륙별 평균 배송 리드타임 비교")
    
    # 글로벌 평균선과 비교해 어떤 대륙이 물류 지연을 유발하는지 막대그래프로 시각화
    fig_region_lead = px.bar(
        region_logistics.sort_values('AVG_DELIVERY_LEAD_TIME_DAYS', ascending=False),
        x='CUSTOMER_REGION',
        y='AVG_DELIVERY_LEAD_TIME_DAYS',
        labels={'CUSTOMER_REGION': '대륙', 'AVG_DELIVERY_LEAD_TIME_DAYS': '평균 배송일 (일)'},
        color='AVG_DELIVERY_LEAD_TIME_DAYS',
        color_continuous_scale=px.colors.sequential.YlOrRd, # 지연될수록 붉어지게 세팅
        template="plotly_white"
    )
    # 가독성을 높이기 위해 글로벌 평균 점선 추가
    fig_region_lead.add_hline(y=global_avg_lead_time, line_dash="dash", line_color="blue", annotation_text="전사 평균 배송일")
    fig_region_lead.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig_region_lead, width="stretch")

with col_right:
    st.subheader("📅 월별 물동량 변화 및 배송 리드타임 추이")
    
    # 월별 물류 지표 트렌드 분석
    monthly_logistics = display_df.groupby('CONFIRMED_MONTH').agg({
        'TOTAL_ITEMS_SOLD': 'sum',
        'AVG_DELIVERY_LEAD_TIME_DAYS': 'mean'
    }).reset_index().sort_values('CONFIRMED_MONTH')
    
    # 이중 축 차트: 물동량(Bar) + 배송일수(Line)
    fig_track = go.Figure()
    fig_track.add_trace(go.Bar(
        x=monthly_logistics['CONFIRMED_MONTH'], y=monthly_logistics['TOTAL_ITEMS_SOLD'],
        name="물동량 (판매수)", yaxis="y1", marker_color="#2ecc71", opacity=0.6
    ))
    fig_track.add_trace(go.Scatter(
        x=monthly_logistics['CONFIRMED_MONTH'], y=monthly_logistics['AVG_DELIVERY_LEAD_TIME_DAYS'],
        name="배송 리드타임 (일)", yaxis="y2", mode="lines+markers", line=dict(color="#e67e22", width=3)
    ))
    
    fig_track.update_layout(
        xaxis=dict(title="주문 월"),
        yaxis=dict(
            title=dict(text="총 물동량 (개)", font=dict(color="#2ecc71")),
            tickfont=dict(color="#2ecc71"),
        ),
        yaxis2=dict(
            title=dict(text="평균 배송 소요 일수 (일)", font=dict(color="#e67e22")),
            tickfont=dict(color="#e67e22"),
            anchor="x",
            overlaying="y",
            side="right",
        ),
        template="plotly_white",
        legend=dict(x=0.01, y=0.99, orientation="h"),
    )
    st.plotly_chart(fig_track, width="stretch")

# -------------------------------------------------------------------
# 📊 6. 하단 국가별 정밀 병목 스크리닝 (심층 가로 바 차트)
# -------------------------------------------------------------------
st.markdown("---")
st.subheader("🚨 국가별 배송 지연 리스크 랭킹 (Top 15 국가)")
st.markdown("글로벌 물류 기지 중 배송 효율화 개선이 시급한 국가 리스트를 추려냅니다.")

# 국가별 정밀 분석
nation_logistics = display_df.groupby(['CUSTOMER_NATION', 'CUSTOMER_REGION']).agg({
    'AVG_DELIVERY_LEAD_TIME_DAYS': 'mean',
    'TOTAL_ITEMS_SOLD': 'sum'
}).reset_index()

# 배송 기간이 긴 상위 15개 국가 추출
top_delayed_nations = nation_logistics.sort_values('AVG_DELIVERY_LEAD_TIME_DAYS', ascending=True).tail(15)

fig_nation_delay = px.bar(
    top_delayed_nations,
    x='AVG_DELIVERY_LEAD_TIME_DAYS',
    y='CUSTOMER_NATION',
    orientation='h',
    color='CUSTOMER_REGION', # 대륙별 분류 코드 적용
    labels={'AVG_DELIVERY_LEAD_TIME_DAYS': '평균 배송 소요 기간 (일)', 'CUSTOMER_NATION': '국가명'},
    title="가장 배송 리드타임이 긴 국가 Top 15",
    template="plotly_white"
)
st.plotly_chart(fig_nation_delay, width="stretch")