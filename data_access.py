import sqlite3
import pandas as pd

DB_PATH = "db/sensor_data.sqlite"

def get_db_connection():
    """데이터베이스 연결을 생성하고 반환합니다."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_overall_equipment_status():
    """
    모든 장비의 가장 최신 상태 정보를 가져옵니다.
    각 device_id 별로 가장 마지막 record_id의 데이터를 조회합니다.
    """
    conn = get_db_connection()
    query = """
    SELECT
        sr.device_id,
        di.device_name,
        sr.annotation_state,
        sr.collection_date,
        sr.collection_time
    FROM sensor_record sr
    JOIN (
        SELECT device_id, MAX(record_id) as max_record_id
        FROM sensor_record
        GROUP BY device_id
    ) latest ON sr.device_id = latest.device_id AND sr.record_id = latest.max_record_id
    JOIN device_info di ON sr.device_id = di.device_id;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_device_list():
    """전체 장비 목록을 가져옵니다."""
    conn = get_db_connection()
    query = "SELECT device_id, device_name FROM device_info ORDER BY device_name;"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_sensor_data_by_device(device_id: str):
    """특정 장비의 시계열 센서 데이터를 가져옵니다. (보안 및 안정성 강화 버전)"""
    conn = get_db_connection()
    query = """
    SELECT
        record_id,
        collection_date || ' ' || collection_time as timestamp,
        PM10_value, PM2_5_value, PM1_0_value,
        NTC_value,
        CT1_value, CT2_value, CT3_value, CT4_value,
        annotation_state
    FROM sensor_record
    WHERE device_id = ?
    ORDER BY collection_date ASC, collection_time ASC;
    """
    # SQL Injection을 방지하기 위해 매개변수화된 쿼리 사용
    df = pd.read_sql_query(query, conn, params=(device_id,))
    
    if df.empty:
        conn.close()
        return pd.DataFrame()

    # 날짜 형식 변환 및 오류 처리
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%m-%d %H:%M:%S', errors='coerce')
    df.dropna(subset=['timestamp'], inplace=True)
    
    # 연도를 2024년으로 강제 설정 (NaT 값 오류 방지)
    df['timestamp'] = df['timestamp'].apply(lambda dt: dt.replace(year=2024) if pd.notnull(dt) else dt)
    
    # datetime 객체 기준으로 최종 정렬하여 순서 보장
    df.sort_values(by='timestamp', inplace=True)

    conn.close()
    return df

def get_external_data_by_device(device_id: str):
    """특정 장비의 외부 환경 데이터를 가져옵니다."""
    conn = get_db_connection()
    # 이 쿼리는 sensor_record와 external_data를 조인하여 특정 장비의 외부 데이터를 가져옵니다.
    # external_data는 record_id를 기준으로 sensor_record와 연결됩니다.
    query = f"""
    SELECT
        sr.record_id,
        sr.collection_date || ' ' || sr.collection_time as timestamp,
        ed.sensor_type,
        ed.value
    FROM external_data ed
    JOIN sensor_record sr ON ed.record_id = sr.record_id
    WHERE sr.device_id = '{device_id}'
    ORDER BY timestamp ASC;
    """
    df = pd.read_sql_query(query, conn)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%m-%d %H:%M:%S', errors='coerce')
    df.dropna(subset=['timestamp'], inplace=True)
    # 연도를 2024년으로 강제 설정
    df['timestamp'] = df['timestamp'].apply(lambda dt: dt.replace(year=2024))
    # Pivot the table to have sensor types as columns
    df_pivot = df.pivot_table(index='timestamp', columns='sensor_type', values='value').reset_index()
    conn.close()
    return df_pivot

def get_sensor_data_for_devices(device_ids: list[str]):
    """선택된 여러 장비의 시계열 센서 데이터를 가져옵니다."""
    if not device_ids:
        return pd.DataFrame()

    conn = get_db_connection()
    # SQL의 IN 연산자에 맞게 device_ids 리스트를 튜플 형태로 변환
    device_ids_tuple = tuple(device_ids)
    placeholders = ', '.join('?' * len(device_ids_tuple))

    query = f"""
    SELECT
        sr.device_id,
        di.device_name,
        sr.collection_date || ' ' || sr.collection_time as timestamp,
        sr.PM10_value, sr.PM2_5_value, sr.PM1_0_value,
        sr.NTC_value,
        sr.CT1_value, sr.CT2_value, sr.CT3_value, sr.CT4_value
    FROM sensor_record sr
    JOIN device_info di ON sr.device_id = di.device_id
    WHERE sr.device_id IN ({placeholders})
    ORDER BY sr.device_id, timestamp ASC;
    """
    df = pd.read_sql_query(query, conn, params=device_ids_tuple)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%m-%d %H:%M:%S', errors='coerce')
    df.dropna(subset=['timestamp'], inplace=True)
    df['timestamp'] = df['timestamp'].apply(lambda dt: dt.replace(year=2024))
    conn.close()
    return df

