import os
import json
import sqlite3
from zipfile import ZipFile
from glob import glob

# DB 연결
db_path = "db/sensor_data.sqlite"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 정규화된 테이블 생성 (앞서 반영된 구조)
cur.executescript("""
DROP TABLE IF EXISTS device_info;
DROP TABLE IF EXISTS sensor_record;
DROP TABLE IF EXISTS ir_data;
DROP TABLE IF EXISTS external_data;

CREATE TABLE device_info (
    device_id TEXT PRIMARY KEY,
    device_name TEXT,
    device_manufacturer TEXT,
    dust_sensor_manufacturer TEXT,
    dust_sensor_name TEXT,
    temp_sensor_manufacturer TEXT,
    temp_sensor_name TEXT,
    overcurrent_sensor_manufacturer TEXT,
    overcurrent_sensor_name TEXT,
    thermal_camera_sensor_manufacturer TEXT,
    thermal_camera_sensor_name TEXT,
    img_description TEXT
);

CREATE TABLE sensor_record (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT,
    filename TEXT,
    collection_date TEXT,
    collection_time TEXT,
    duration_time TEXT,
    sensor_types TEXT,
    cumulative_operating_day TEXT,
    equipment_history TEXT,
    annotation_type TEXT,
    annotation_state TEXT,
    PM10_value REAL, PM10_unit TEXT, PM10_trend TEXT,
    PM2_5_value REAL, PM2_5_unit TEXT, PM2_5_trend TEXT,
    PM1_0_value REAL, PM1_0_unit TEXT, PM1_0_trend TEXT,
    NTC_value REAL, NTC_unit TEXT, NTC_trend TEXT,
    CT1_value REAL, CT1_unit TEXT, CT1_trend TEXT,
    CT2_value REAL, CT2_unit TEXT, CT2_trend TEXT,
    CT3_value REAL, CT3_unit TEXT, CT3_trend TEXT,
    CT4_value REAL, CT4_unit TEXT, CT4_trend TEXT,
    FOREIGN KEY (device_id) REFERENCES device_info(device_id)
);

CREATE TABLE ir_data (
    record_id INTEGER,
    img_id TEXT,
    location TEXT,
    filename TEXT,
    img_name TEXT,
    img_description TEXT,
    value_TGmx REAL,
    X_Tmax REAL,
    Y_Tmax REAL,
    FOREIGN KEY (record_id) REFERENCES sensor_record(record_id)
);

CREATE TABLE external_data (
    record_id INTEGER,
    sensor_type TEXT,
    value REAL,
    unit TEXT,
    trend TEXT,
    FOREIGN KEY (record_id) REFERENCES sensor_record(record_id)
);
""")

# ZIP 파일 내부 JSON 파싱 함수
def extract_json_from_zip(zip_path):
    with ZipFile(zip_path, 'r') as zipf:
        for file in zipf.namelist():
            if file.endswith(".json"):
                with zipf.open(file) as f:
                    try:
                        data = json.load(f)
                        insert_normalized_data(data)
                    except Exception as e:
                        print(f"JSON 파싱 실패: {file} in {zip_path} — {e}")

# INSERT 함수
def insert_normalized_data(data):
    m = data["meta_info"][0]
    s = data["sensor_data"][0]
    ir = data["ir_data"][0]["temp_max"][0]
    ann = data["annotations"][0]["tagging"][0]
    ext = data["external_data"][0]

    def g(sensor, key):
        return s.get(sensor, [{}])[0].get(key)

    # 1. device_info (중복 방지)
    cur.execute("SELECT 1 FROM device_info WHERE device_id = ?", (m["device_id"],))
    if cur.fetchone() is None:
        cur.execute("""
            INSERT INTO device_info VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            m.get("device_id"),
            m.get("device_name"),
            m.get("device_manufacturer"),
            m.get("dust_sensor_manufacturer"),
            m.get("dust_sensor_name"),
            m.get("temp_sensor_manufacturer"),
            m.get("temp_sensor_name"),
            m.get("overcurrent_sensor_manufacturer"),
            m.get("overcurrent_sensor_name"),
            m.get("thermal_camera_sensor_manufacturer"),
            m.get("thermal_camera_sensor_name"),
            m.get("img_description")
        ))

    # 2. sensor_record
    cur.execute("""
        INSERT INTO sensor_record (
            device_id, filename, collection_date, collection_time,
            duration_time, sensor_types, cumulative_operating_day, equipment_history,
            annotation_type, annotation_state,
            PM10_value, PM10_unit, PM10_trend,
            PM2_5_value, PM2_5_unit, PM2_5_trend,
            PM1_0_value, PM1_0_unit, PM1_0_trend,
            NTC_value, NTC_unit, NTC_trend,
            CT1_value, CT1_unit, CT1_trend,
            CT2_value, CT2_unit, CT2_trend,
            CT3_value, CT3_unit, CT3_trend,
            CT4_value, CT4_unit, CT4_trend
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        m.get("device_id"),
        m.get("filename"),
        m.get("collection_date"),
        m.get("collection_time"),
        m.get("duration_time"),
        m.get("sensor_types"),
        m.get("cumulative_operating_day"),
        m.get("equipment_history"),
        ann.get("annotation_type"),
        ann.get("state"),
        g("PM10", "value"), g("PM10", "data_unit"), g("PM10", "trend"),
        g("PM2.5", "value"), g("PM2.5", "data_unit"), g("PM2.5", "trend"),
        g("PM1.0", "value"), g("PM1.0", "data_unit"), g("PM1.0", "trend"),
        g("NTC", "value"), g("NTC", "data_unit"), g("NTC", "trend"),
        g("CT1", "value"), g("CT1", "data_unit"), g("CT1", "trend"),
        g("CT2", "value"), g("CT2", "data_unit"), g("CT2", "trend"),
        g("CT3", "value"), g("CT3", "data_unit"), g("CT3", "trend"),
        g("CT4", "value"), g("CT4", "data_unit"), g("CT4", "trend")
    ))
    record_id = cur.lastrowid

    # 3. ir_data
    cur.execute("""
        INSERT INTO ir_data (
            record_id, img_id, location, filename, img_name, img_description,
            value_TGmx, X_Tmax, Y_Tmax
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record_id,
        m.get("img-id"),
        m.get("location"),
        m.get("filename"),
        m.get("img_name"),
        m.get("img_description"),
        ir.get("value_TGmx"),
        ir.get("X_Tmax"),
        ir.get("Y_Tmax")
    ))

    # 4. external_data
    for sensor_type, values in ext.items():
        e = values[0]
        cur.execute("""
            INSERT INTO external_data (
                record_id, sensor_type, value, unit, trend
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            record_id,
            sensor_type,
            e.get("value"),
            e.get("data_unit"),
            e.get("trend")
        ))


# data/ 아래의 모든 zip 처리
for zip_file in glob("data/*.zip"):
    extract_json_from_zip(zip_file)

# 저장
conn.commit()
conn.close()

# 결과 파일 경로 반환
db_path
