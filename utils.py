import streamlit as st
import pandas as pd
from datetime import date

# 장비 상태 매핑 및 색상 정의
STATE_MAP = {0: '정상', 1: '주의', 2: '경고', 3: '위험'}
COLOR_MAP = {'정상': 'green', '주의': 'yellow', '경고': 'orange', '위험': 'red'}

def apply_date_filter(df: pd.DataFrame, key_prefix: str = ""): # key_prefix 추가
    """
    데이터프레임에 날짜 필터를 적용하고 필터링된 데이터프레임을 반환합니다.
    Streamlit의 date_input 위젯을 사이드바에 표시합니다.
    """
    st.sidebar.header("기간 필터")
    
    if df.empty:
        st.sidebar.warning("필터링할 데이터가 없습니다.")
        return df

    min_date = df['timestamp'].min().date()
    max_date = df['timestamp'].max().date()

    start_date = st.sidebar.date_input('시작일', min_date, min_value=min_date, max_value=max_date, key=f"{key_prefix}_start_date")
    end_date = st.sidebar.date_input('종료일', max_date, min_value=min_date, max_value=max_date, key=f"{key_prefix}_end_date")

    if start_date > end_date:
        st.sidebar.error('오류: 종료일은 시작일보다 빠를 수 없습니다.')
        return pd.DataFrame() # 빈 데이터프레임 반환
    
    mask = (df['timestamp'].dt.date >= start_date) & (df['timestamp'].dt.date <= end_date)
    df_filtered = df.loc[mask]
    
    return df_filtered

def configure_xaxis(fig):
    """
    Plotly 차트의 X축을 카테고리 타입으로 설정하고 레이블을 기울입니다.
    """
    fig.update_xaxes(type='category', tickangle=-45)
    return fig
