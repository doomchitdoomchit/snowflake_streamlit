# 글로벌 커머스 BI 대시보드 (Snowflake + Streamlit)

Snowflake 데이터 마트 뷰 `V_MONTHLY_GLOBAL_SALES_MART`를 Snowpark로 조회하고, Streamlit 멀티 페이지 대시보드로 KPI·매출·고객·마케팅·물류·리스크를 시각화하는 프로젝트입니다.

## 주요 기능

| 페이지 | 설명 |
|--------|------|
| **Home** | 5개 분석 화면의 핵심 KPI를 한 화면에 요약 |
| **01 비즈니스 매출 트렌드** | 월별 순매출, AOV, 국가별 매출, MoM 성장률 |
| **02 고객 세그먼트 및 행동 분석** | 재질(세그먼트)별 매출·대량구매·반품 리스크, 트리맵 |
| **03 상품 마진 및 프로모션 성과** | 할인율 vs 매출, 제조사 점유율, 브랜드별 프로모션 리스크 |
| **04 SCM 및 물류 파이프라인 최적화** | 대륙별 리드타임, 월별 물동량, 국가별 배송 지연 |
| **05 SCM 리스크 관리 및 종합 진단** | 반품 히트맵, 리드타임–반품 상관, 월별 반품률 추이 |

## 스크린샷

### Home — KPI 종합

[Home 화면](img/Home_screenshot.png)

### 01 비즈니스 매출 트렌드

[비즈니스 매출 트렌드](img/01page.png)

### 02 고객 세그먼트 및 행동 분석

[고객 세그먼트 및 행동 분석](img/2번_페이지.png)

### 03 상품 마진 및 프로모션 성과

[상품 마진 및 프로모션 성과](img/3번_페이지.png)

### 04 SCM 및 물류 파이프라인 최적화

[SCM 및 물류 파이프라인 최적화](img/4번_페이지.png)

### 05 SCM 리스크 관리 및 종합 진단
[SCM 리스크 관리 및 종합 진단](img/5번_페이지.png)


## 기술 스택

- **Python** 3.12+
- **Streamlit** — 웹 대시보드 UI
- **Snowflake Snowpark** — 데이터 웨어하우스 연동
- **Pandas / Plotly** — 집계 및 시각화
- **python-dotenv** — 환경 변수 관리
- **uv** — 패키지·가상환경 관리

## 프로젝트 구조

```
snowflake_streamlit/
├── HOME.py                 # Streamlit Home (KPI 요약)
├── pages/                  # 멀티 페이지 앱
├── src/
│   ├── snowflake_session.py  # Snowflake 세션 (.env)
│   └── data_loader.py        # 마트 뷰 로드 (캐싱)
├── img/                    # 스크린샷
├── .env                    # Snowflake 접속 정보 (Git 제외)
├── pyproject.toml
└── uv.lock
```

## 사전 요구 사항

- [uv](https://docs.astral.sh/uv/) 설치
- Snowflake 계정 및 `V_MONTHLY_GLOBAL_SALES_MART` 뷰 접근 권한
- 가상 웨어하우스 사용 가능 상태

## 설치 및 실행

### 1. 저장소 클론

```bash
git clone https://github.com/doomchitdoomchit/snowflake_streamlit.git
cd snowflake_streamlit
```

### 2. 가상환경 및 의존성 설치

```bash
uv venv
uv sync
```

### 3. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 만들고 아래 항목을 채웁니다.

```env
SNOWFLAKE_ACCOUNT=your_account_locator
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=WAREHOUSE
SNOWFLAKE_DATABASE=DATABASE
SNOWFLAKE_SCHEMA=SCHEMA
```

선택 사항:

```env
SNOWFLAKE_ROLE=ACCOUNTADMIN
```

### 4. 앱 실행

```bash
uv run streamlit run HOME.py
```

브라우저에서 `http://localhost:8501` 로 접속합니다.

## 데이터 소스

- **뷰:** `V_MONTHLY_GLOBAL_SALES_MART`
- **참고:** [Snowflake TPC-H 샘플 데이터](https://docs.snowflake.com/en/user-guide/sample-data-tpch)

## 캐싱

- `@st.cache_resource` — Snowflake 세션
- `@st.cache_data` — 마트 뷰 DataFrame

데이터·연결 설정을 바꾼 뒤에는 Streamlit 사이드바 **Clear cache** 후 다시 실행하세요.

## 주의 사항

- `.env`에는 계정 비밀번호가 포함되므로 **Git에 커밋하지 마세요.** (`.gitignore`에 등록됨)
- Windows PowerShell에서 이모지가 포함된 파일명을 터미널에 직접 입력하면 인코딩 오류가 날 수 있습니다. 실행 시 `HOME.py`처럼 ASCII 파일명을 사용하세요.

## 라이선스

개인 학습·포트폴리오 용도로 제작되었습니다.
