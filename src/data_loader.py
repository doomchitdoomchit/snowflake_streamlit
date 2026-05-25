import pandas as pd
import streamlit as st
from snowflake.snowpark import Session

from src.snowflake_session import init_snowflake_session


@st.cache_resource
def get_snowflake_session() -> Session:
    return init_snowflake_session()


@st.cache_data(show_spinner="데이터 로드 중...")
def load_mart_data() -> pd.DataFrame:
    session = get_snowflake_session()
    df = session.table("V_MONTHLY_GLOBAL_SALES_MART").to_pandas()
    df["CONFIRMED_MONTH"] = pd.to_datetime(df["CONFIRMED_MONTH"])
    return df
