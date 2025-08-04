import streamlit as st
import pandas as pd
import plotly.express as px
from data_access import get_device_list, get_sensor_data_by_device, get_external_data_by_device
from utils import STATE_MAP, COLOR_MAP, apply_date_filter, configure_xaxis

st.set_page_config(
    page_title="개별 장비 분석",
    page_icon="⚙️",
    layout="wide",
)

st.title("⚙️ 개별 장비 분석")
st.markdown("특정 장비를 선택하여 상세 센서 데이터와 이력을 조회합니다.")

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
    
    # 선택된 display_name을 기반으로 device_id와 device_name 찾기
    selected_device_info = device_list[device_list['display_name'] == selected_display_name].iloc[0]
    selected_device_id = selected_device_info['device_id']
    selected_device_name = selected_device_info['device_name']

    st.header(f"{selected_device_name} (ID: {selected_device_id}) 분석")

    # 2. 데이터 로드
    with st.spinner("센서 데이터를 불러오는 중..."):
        df_sensor = get_sensor_data_by_device(selected_device_id)
        df_external = get_external_data_by_device(selected_device_id)

    if df_sensor.empty:
        st.warning("선택된 장비의 센서 데이터를 찾을 수 없습니다.")
    else:
        # 날짜 필터링 적용
        df_sensor_filtered = apply_date_filter(df_sensor, key_prefix="device_details_sensor")
        df_external_filtered = apply_date_filter(df_external, key_prefix="device_details_external")

        if df_sensor_filtered.empty:
            st.warning("선택된 기간에 해당하는 센서 데이터가 없습니다.")
        else:
            # x축 레이블을 위한 포맷팅 (필터링된 데이터에 적용)
            df_sensor_filtered['timestamp_label'] = df_sensor_filtered['timestamp'].dt.strftime('%m-%d %H:%M')
            if not df_external_filtered.empty:
                df_external_filtered['timestamp_label'] = df_external_filtered['timestamp'].dt.strftime('%m-%d %H:%M')

            # 3. 탭 기반 데이터 시각화 (필터링된 데이터 사용)
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["상태 변화", "미세먼지 (PM)", "온도 (NTC)", "전류 (CT)", "외부 환경"])

            with tab1:
                st.subheader("시간에 따른 장비 상태 변화")
                df_sensor_filtered['state_label'] = df_sensor_filtered['annotation_state'].astype(int).map(STATE_MAP)
                fig_state = px.scatter(df_sensor_filtered, x='timestamp_label', y='state_label', color='state_label', 
                                     title='시간에 따른 장비 상태 변화', labels={'state_label': '장비 상태', 'timestamp_label': '측정 시점'}, 
                                     category_orders={"state_label": ['정상', '주의', '경고', '위험']})
                configure_xaxis(fig_state)
                st.plotly_chart(fig_state, use_container_width=True)

            with tab2:
                st.subheader("미세먼지 센서 데이터 (µg/m³)")
                fig_pm = px.line(df_sensor_filtered, x='timestamp_label', y=['PM10_value', 'PM2_5_value', 'PM1_0_value'], 
                               title='시간에 따른 미세먼지 농도 변화', labels={'value': '농도 (µg/m³)', 'variable': '센서 종류', 'timestamp_label': '측정 시점'})
                configure_xaxis(fig_pm)
                st.plotly_chart(fig_pm, use_container_width=True)

            with tab3:
                st.subheader("온도 센서 데이터 (℃)")
                fig_temp = px.line(df_sensor_filtered, x='timestamp_label', y=['NTC_value'], 
                                 title='시간에 따른 장비 온도 변화', labels={'value': '온도 (℃)', 'variable': '센서 종류', 'timestamp_label': '측정 시점'})
                configure_xaxis(fig_temp)
                st.plotly_chart(fig_temp, use_container_width=True)

            with tab4:
                st.subheader("전류 센서 데이터 (A)")
                fig_ct = px.line(df_sensor_filtered, x='timestamp_label', y=['CT1_value', 'CT2_value', 'CT3_value', 'CT4_value'], 
                               title='시간에 따른 전류량 변화', labels={'value': '전류 (A)', 'variable': '센서 종류', 'timestamp_label': '측정 시점'})
                configure_xaxis(fig_ct)
                st.plotly_chart(fig_ct, use_container_width=True)

            with tab5:
                if not df_external_filtered.empty:
                    st.subheader("외부 환경 데이터")
                    fig_ext_temp = px.line(df_external_filtered, x='timestamp_label', y=['ex_temperature'], title='외부 온도 변화', labels={'value': '온도 (℃)', 'timestamp_label': '측정 시점'})
                    configure_xaxis(fig_ext_temp)
                    st.plotly_chart(fig_ext_temp, use_container_width=True)

                    fig_ext_hum = px.line(df_external_filtered, x='timestamp_label', y=['ex_humidity'], title='외부 습도 변화', labels={'value': '습도 (%)', 'timestamp_label': '측정 시점'})
                    configure_xaxis(fig_ext_hum)
                    st.plotly_chart(fig_ext_hum, use_container_width=True)

                    fig_ext_ill = px.line(df_external_filtered, x='timestamp_label', y=['ex_illuminance'], title='외부 조도 변화', labels={'value': '조도 (lux)', 'timestamp_label': '측정 시점'})
                    configure_xaxis(fig_ext_ill)
                    st.plotly_chart(fig_ext_ill, use_container_width=True)
                else:
                    st.info("해당 장비의 외부 환경 데이터가 없습니다.")

            with st.expander("상세 데이터 보기"):
                st.dataframe(df_sensor, use_container_width=True)
                if not df_external.empty:
                    st.dataframe(df_external, use_container_width=True)