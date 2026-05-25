import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from snowflake.snowpark import Session
from src.data_loader import load_mart_data

with st.spinner("데이터 로드 중..."):
    try:
        raw_df = load_mart_data()
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        st.stop()

st.set_page_config(page_title="Customer Insights", layout="wide")
st.title("👥 고객 세그멘테이션 및 구매 행동 분석")
st.markdown("`V_MONTHLY_GLOBAL_SALES_MART` 뷰를 다차원 축으로 쪼개어 고객 그룹별 성향을 비교합니다.")

# 사이드바 필터: 국가(Nation) 선택을 통해 특정 타깃 국가 고객만 심층 분석 가능
st.sidebar.header("🔍 고객 타깃팅 필터")
nations = sorted(raw_df['CUSTOMER_NATION'].unique())
selected_nation = st.sidebar.selectbox("대상 국가 선택", ["전체 국가"] + nations)

if selected_nation != "전체_국가" and selected_nation != "전체 국가":
    display_df = raw_df[raw_df['CUSTOMER_NATION'] == selected_nation]
else:
    display_df = raw_df

# -------------------------------------------------------------------
# 🧮 3. 데이터 통계 및 파생 메트릭 연산
# -------------------------------------------------------------------
# 상품 재질(Material)을 고객이 선호하는 주요 상품 세그먼트로 정의하여 분석 진행
segment_df = display_df.groupby('PART_MATERIAL').agg({
    'TOTAL_NET_REVENUE': 'sum',
    'TOTAL_ORDERS': 'sum',
    'TOTAL_ITEMS_SOLD': 'sum',
    'TOTAL_RETURNED_ITEMS': 'sum'
}).reset_index()

# 주문당 평균 구매 수량 (주문당 얼마나 대량으로 구매하는가?)
segment_df['ITEMS_PER_ORDER'] = segment_df['TOTAL_ITEMS_SOLD'] / segment_df['TOTAL_ORDERS']
# 반품율 (주문 아이템 대비 반품된 아이템 비중)
segment_df['RETURN_RATE'] = (segment_df['TOTAL_RETURNED_ITEMS'] / segment_df['TOTAL_ITEMS_SOLD']) * 100

# -------------------------------------------------------------------
# 📊 4. 상단 세그먼트별 요약 비교 (Metrics 카드 그룹)
# -------------------------------------------------------------------
st.subheader("💡 세그먼트별 구매 행동 요약")
m_col1, m_col2, m_col3 = st.columns(3)

# 가장 매출이 높은 최고 가치 세그먼트(VIP Segment) 추출
top_segment = segment_df.sort_values('TOTAL_NET_REVENUE', ascending=False).iloc[0]['PART_MATERIAL']
# 가장 한 번에 많이 사는 대량 구매 세그먼트 추출
bulk_segment = segment_df.sort_values('ITEMS_PER_ORDER', ascending=False).iloc[0]['PART_MATERIAL']
# 반품 리스크가 가장 높은 세그먼트 추출
risk_segment = segment_df.sort_values('RETURN_RATE', ascending=False).iloc[0]['PART_MATERIAL']

with m_col1:
    st.metric(label="⭐ 최고 매출 기여 세그먼트 (VIP)", value=top_segment)
with m_col2:
    st.metric(label="📦 건당 대량 구매 세그먼트", value=bulk_segment, delta=f"{segment_df.sort_values('ITEMS_PER_ORDER', ascending=False).iloc[0]['ITEMS_PER_ORDER']:.1f}개 / 주문")
with m_col3:
    st.metric(label="⚠️ 반품 주의 리스크 세그먼트", value=risk_segment, delta=f"{segment_df.sort_values('RETURN_RATE', ascending=False).iloc[0]['RETURN_RATE']:.2f}% (반품률)", delta_color="inverse")

st.markdown("---")

# -------------------------------------------------------------------
# 📉 5. 메인 시각화 차트 (Plotly 세그먼트 다차원 분석)
# -------------------------------------------------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("💰 세그먼트별 총 순매출 및 주문 건수 비교")
    
    # 세그먼트별 매출(Bar)과 주문수(Line)를 한눈에 비교하여 '박리다매'형인지 '고단가'형인지 파악
    fig_seg = go.Figure()
    fig_seg.add_trace(go.Bar(
        x=segment_df['PART_MATERIAL'], y=segment_df['TOTAL_NET_REVENUE'],
        name="총 순매출 ($)", yaxis="y1", marker_color="#4B0082", opacity=0.8
    ))
    fig_seg.add_trace(go.Scatter(
        x=segment_df['PART_MATERIAL'], y=segment_df['TOTAL_ORDERS'],
        name="총 주문 건수", yaxis="y2", mode="lines+markers", line=dict(color="#00FA9A", width=3)
    ))
    
    fig_seg.update_layout(
        xaxis=dict(title="고객 선호 상품 재질(세그먼트)"),
        yaxis=dict(
            title=dict(text="총 순매출액 ($)", font=dict(color="#4B0082")),
            tickfont=dict(color="#4B0082"),
        ),
        yaxis2=dict(
            title=dict(text="총 주문 건수", font=dict(color="#00FA9A")),
            tickfont=dict(color="#00FA9A"),
            anchor="x",
            overlaying="y",
            side="right",
        ),
        template="plotly_white",
        legend=dict(x=0.01, y=0.99, orientation="h"),
    )
    st.plotly_chart(fig_seg, width="stretch")

with col_right:
    st.subheader("🎯 세그먼트별 구매 집중도 및 반품 리스크 산점도")
    
    # 4분면 버블 차트를 통해 세그먼트별 행동 패턴을 입체적으로 분석
    # X축: 건당 구매 수량(대량 구매 성향), Y축: 반품률, 크기: 총 순매출액
    fig_bubble = px.scatter(
        segment_df,
        x='ITEMS_PER_ORDER',
        y='RETURN_RATE',
        size='TOTAL_NET_REVENUE',
        color='PART_MATERIAL',
        hover_name='PART_MATERIAL',
        labels={'ITEMS_PER_ORDER': '주문당 평균 구매 수량 (개)', 'RETURN_RATE': '반품률 (%)'},
        text='PART_MATERIAL',
        template="plotly_white"
    )
    fig_bubble.update_traces(textposition='top center')
    # 기준선 추가 (평균치 파악용)
    fig_bubble.add_hline(y=segment_df['RETURN_RATE'].mean(), line_dash="dash", line_color="red", annotation_text="평균 반품률")
    fig_bubble.add_vline(x=segment_df['ITEMS_PER_ORDER'].mean(), line_dash="dash", line_color="blue", annotation_text="평균 주문 수량")
    
    st.plotly_chart(fig_bubble, width="stretch")

# -------------------------------------------------------------------
# 📊 6. 하단 교차 분석 (브랜드별 테마 분석 트레맵)
# -------------------------------------------------------------------
st.markdown("---")
st.subheader("🏷️ 세그먼트 내 브랜드별 매출 비중 (다차원 계층 분석)")

# 선호 재질 내에서 어떤 브랜드가 매출을 견인하는지 트리맵으로 시각화
brand_df = display_df.groupby(['PART_MATERIAL', 'PART_BRAND'])['TOTAL_NET_REVENUE'].sum().reset_index()

fig_tree = px.treemap(
    brand_df,
    path=['PART_MATERIAL', 'PART_BRAND'],
    values='TOTAL_NET_REVENUE',
    color='TOTAL_NET_REVENUE',
    color_continuous_scale=px.colors.sequential.Plasma,
    labels={'TOTAL_NET_REVENUE': '순매출액 ($)'}
)
st.plotly_chart(fig_tree, width="stretch")