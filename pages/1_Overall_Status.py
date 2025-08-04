import streamlit as st
import pandas as pd
import plotly.express as px
from data_access import get_overall_equipment_status
from utils import STATE_MAP, COLOR_MAP

st.set_page_config(
    page_title="종합 현황",
    page_icon="📊",
    layout="wide",
)

st.title("📊 종합 현황")
st.markdown("전체 장비의 현재 상태를 요약하여 보여줍니다.")

# 데이터 로드
with st.spinner("전체 장비 현황을 불러오는 중..."):
    df_status = get_overall_equipment_status()

if df_status.empty:
    st.warning("데이터를 불러올 수 없습니다. 데이터베이스를 확인하세요.")
else:
    # 상태(state) 값에 대한 레이블 및 색상 정의
    df_status['annotation_state_label'] = df_status['annotation_state'].astype(int).map(STATE_MAP)

    st.subheader("실시간 장비 상태 요약")
    col1, col2 = st.columns([0.4, 0.6])

    with col1:
        state_counts = df_status['annotation_state_label'].value_counts().reindex(['정상', '주의', '경고', '위험'], fill_value=0)
        st.metric(label="🟢 정상", value=state_counts.get('정상', 0))
        st.metric(label="🟡 주의", value=state_counts.get('주의', 0))
        st.metric(label="🟠 경고", value=state_counts.get('경고', 0))
        st.metric(label="🔴 위험", value=state_counts.get('위험', 0))

    with col2:
        fig = px.pie(state_counts, values=state_counts.values, names=state_counts.index, 
                     title='장비 상태 비율', hole=.4,
                     color=state_counts.index, 
                     color_discrete_map=COLOR_MAP)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # 이상 징후 장비 목록
    st.subheader("🚨 이상 징후 장비 목록 (경고/위험)")
    critical_devices = df_status[df_status['annotation_state_label'].isin(['경고', '위험'])]
    if critical_devices.empty:
        st.success("현재 경고 또는 위험 상태의 장비가 없습니다.")
    else:
        st.dataframe(critical_devices[['device_id', 'device_name', 'annotation_state_label', 'collection_date', 'collection_time']].rename(
            columns={
                'device_id': '장비 ID',
                'device_name': '장비 종류',
                'annotation_state_label': '현재 상태',
                'collection_date': '마지막 업데이트 날짜',
                'collection_time': '마지막 업데이트 시간'
            }
        ), use_container_width=True)

    # 전체 장비 목록 (Expander 안에)
    with st.expander("전체 장비 목록 보기"):
        st.dataframe(df_status[['device_id', 'device_name', 'annotation_state_label', 'collection_date', 'collection_time']].rename(
            columns={
                'device_id': '장비 ID',
                'device_name': '장비 종류',
                'annotation_state_label': '현재 상태',
                'collection_date': '마지막 업데이트 날짜',
                'collection_time': '마지막 업데이트 시간'
            }
        ), use_container_width=True)