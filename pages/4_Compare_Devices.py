import streamlit as st
import pandas as pd
import plotly.express as px
from data_access import get_device_list, get_sensor_data_for_devices
from utils import apply_date_filter, configure_xaxis

st.set_page_config(
    page_title="장비 비교 분석",
    page_icon="🆚",
    layout="wide",
)

st.title("🆚 장비 비교 분석")
st.markdown("여러 장비를 선택하여 주요 센서 데이터를 비교 분석합니다.")

# 1. 장비 목록 가져오기
device_list = get_device_list()
if device_list.empty:
    st.warning("장비 목록을 불러올 수 없습니다.")
else:
    device_list['display_name'] = device_list['device_name'] + " (" + device_list['device_id'] + ")"
    all_display_names = device_list['display_name'].tolist()

    # 2. 사용자 입력 (다중 장비 선택 및 센서 선택)
    st.sidebar.header("비교 옵션")
    selected_display_names = st.sidebar.multiselect(
        "비교할 장비를 두 개 이상 선택하세요.",
        all_display_names,
        default=all_display_names[:2] # 기본값으로 첫 두 장비 선택
    )

    sensor_columns = {
        'PM10_value': '미세먼지 (PM10)',
        'PM2_5_value': '초미세먼지 (PM2.5)',
        'PM1_0_value': '극초미세먼지 (PM1.0)',
        'NTC_value': '장비 온도 (NTC)',
        'CT1_value': '전류 (CT1)',
        'CT2_value': '전류 (CT2)',
        'CT3_value': '전류 (CT3)',
        'CT4_value': '전류 (CT4)'
    }
    selected_sensor = st.sidebar.selectbox(
        "비교할 센서를 선택하세요.",
        options=list(sensor_columns.keys()),
        format_func=lambda x: sensor_columns[x] # 사용자에게는 보기 좋은 이름 표시
    )

    if len(selected_display_names) < 2:
        st.info("비교하려면 두 개 이상의 장비를 선택해야 합니다.")
    else:
        # 선택된 display_name으로부터 device_id 리스트 추출
        selected_device_ids = device_list[device_list['display_name'].isin(selected_display_names)]['device_id'].tolist()

        # 3. 데이터 로드
        with st.spinner("비교 데이터를 불러오는 중..."):
            df_compare = get_sensor_data_for_devices(selected_device_ids)

        if df_compare.empty:
            st.warning("선택된 장비의 데이터를 불러올 수 없습니다.")
        else:
            # 날짜 필터링 적용
            df_compare_filtered = apply_date_filter(df_compare, key_prefix="compare_devices")

            if df_compare_filtered.empty:
                st.warning("선택된 기간에 해당하는 데이터가 없습니다.")
            else:
                st.header(f'`{sensor_columns[selected_sensor]}` 데이터 비교')

                # x축 레이블 포맷팅
                df_compare_filtered['timestamp_label'] = df_compare_filtered['timestamp'].dt.strftime('%m-%d %H:%M')

                # 5. 비교 차트 시각화 (색상 기준: device_id)
                fig = px.line(df_compare_filtered, x='timestamp_label', y=selected_sensor, color='device_id',
                              title=f'장비별 {sensor_columns[selected_sensor]} 비교 분석',
                              labels={
                                  'timestamp_label': '측정 시점',
                                  selected_sensor: f'{sensor_columns[selected_sensor]} 값',
                                  'device_id': '장비 ID'
                              },
                              markers=True)
                configure_xaxis(fig)
                st.plotly_chart(fig, use_container_width=True)

                # 6. 상세 데이터 보기
                with st.expander("비교 데이터 상세 보기"):
                    st.dataframe(df_compare_filtered, use_container_width=True)}
