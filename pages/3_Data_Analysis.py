import streamlit as st
import pandas as pd
import plotly.express as px
from data_access import get_device_list, get_sensor_data_by_device
from utils import STATE_MAP, COLOR_MAP, apply_date_filter

st.set_page_config(
    page_title="데이터 분석",
    page_icon="📈",
    layout="wide",
)

st.title("📈 데이터 분석")
st.markdown("센서 데이터 간의 관계를 분석하여 이상 원인 탐색을 지원합니다.")

# 1. 장비 선택
device_list = get_device_list()
if device_list.empty:
    st.warning("장비 목록을 불러올 수 없습니다.")
else:
    # device_name과 device_id를 결합한 새로운 컬럼 생성
    device_list['display_name'] = device_list['device_name'] + " (" + device_list['device_id'] + ")"
    
    selected_display_name = st.selectbox(
        '분석할 장비를 선택하세요.',
        device_list['display_name']
    )
    
    # 선택된 display_name을 기반으로 device_id 문자열을 정확히 추출합니다.
    selected_device_id = device_list[device_list['display_name'] == selected_display_name]['device_id'].iloc[0]

    st.header(f"{selected_display_name} 데이터 분석")

    # 2. 데이터 로드
    with st.spinner("센서 데이터를 불러오는 중..."):
        df_sensor = get_sensor_data_by_device(selected_device_id)

    if df_sensor.empty:
        st.warning("선택된 장비의 센서 데이터를 찾을 수 없습니다.")
    else:
        # 날짜 필터링 적용
        df_sensor_filtered = apply_date_filter(df_sensor, key_prefix="data_analysis")

        if df_sensor_filtered.empty:
            st.warning("선택된 기간에 해당하는 센서 데이터가 없습니다.")
        else:
            sensor_columns = ['PM10_value', 'PM2_5_value', 'PM1_0_value', 'NTC_value', 'CT1_value', 'CT2_value', 'CT3_value', 'CT4_value']
            df_numeric = df_sensor_filtered[sensor_columns].copy()

            # 3. 상관관계 히트맵
            st.subheader("센서 데이터 상관관계 히트맵")
            st.markdown("센서 간의 선형 관계를 시각적으로 분석합니다. 붉은색은 강한 양의 상관관계, 푸른색은 강한 음의 상관관계를 의미합니다.")
            corr = df_numeric.corr()
            fig_heatmap = px.imshow(corr, text_auto=True, aspect="auto", 
                                    title="주요 센서 간 상관관계",
                                    color_continuous_scale='icefire',
                                    zmin=-1, zmax=1) # 색상 범위를 -1에서 1로 고정
            st.plotly_chart(fig_heatmap, use_container_width=True)

            st.divider()

            # 4. 센서별 산점도
            st.subheader("센서별 관계 분석 (산점도)")
            st.markdown("두 센서를 선택하여 데이터 분포와 이상치의 관계를 자세히 확인합니다. 점의 색상은 장비의 상태를 나타냅니다.")
            col1, col2 = st.columns(2)
            with col1:
                x_axis = st.selectbox("X축으로 사용할 센서를 선택하세요.", sensor_columns, index=0)
            with col2:
                y_axis = st.selectbox("Y축으로 사용할 센서를 선택하세요.", sensor_columns, index=1)
            
            if x_axis and y_axis:
                # 상관계수 계산 및 표시
                correlation_value = df_sensor_filtered[x_axis].corr(df_sensor_filtered[y_axis])
                st.info(f"**{x_axis}**와 **{y_axis}**의 상관계수: **{correlation_value:.2f}**")

                # 상태 정보 매핑
                df_sensor_filtered['state_label'] = df_sensor_filtered['annotation_state'].astype(int).map(STATE_MAP)

                fig_scatter = px.scatter(df_sensor_filtered, x=x_axis, y=y_axis, 
                                         color="state_label", 
                                         color_discrete_map=COLOR_MAP,
                                         title=f'{x_axis} vs. {y_axis}',
                                         hover_data=['timestamp'])
                st.plotly_chart(fig_scatter, use_container_width=True)