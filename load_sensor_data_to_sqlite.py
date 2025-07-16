import os
import json
import sqlite3
from zipfile import ZipFile
from glob import glob

# SQLite DB 연결
db_path = "db/sensor_data.sqlite"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 테이블 생성
cur.executescript("""
CREATE TABLE IF NOT EXISTS full_flat_sensor_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT,
    device_manufacturer TEXT,
    device_name TEXT,
    dust_sensor_manufacturer TEXT,
    dust_sensor_name TEXT,
    temp_sensor_manufacturer TEXT,
    temp_sensor_name TEXT,
    overcurrent_sensor_manufacturer TEXT,
    overcurrent_sensor_name TEXT,
    thermal_camera_sensor_manufacturer TEXT,
    thermal_camera_sensor_name TEXT,
    installation_environment TEXT,
    collection_date TEXT,
    collection_time TEXT,
    duration_time TEXT,
    sensor_types TEXT,
    cumulative_operating_day TEXT,
    equipment_history TEXT,
    img_id TEXT,
    location TEXT,
    filename TEXT,
    img_name TEXT,
    img_description TEXT,
    PM10_value REAL,
    PM10_unit TEXT,
    PM10_trend TEXT,
    PM2_5_value REAL,
    PM2_5_unit TEXT,
    PM2_5_trend TEXT,
    PM1_0_value REAL,
    PM1_0_unit TEXT,
    PM1_0_trend TEXT,
    NTC_value REAL,
    NTC_unit TEXT,
    NTC_trend TEXT,
    CT1_value REAL,
    CT1_unit TEXT,
    CT1_trend TEXT,
    CT2_value REAL,
    CT2_unit TEXT,
    CT2_trend TEXT,
    CT3_value REAL,
    CT3_unit TEXT,
    CT3_trend TEXT,
    CT4_value REAL,
    CT4_unit TEXT,
    CT4_trend TEXT,
    value_TGmx REAL,
    X_Tmax REAL,
    Y_Tmax REAL,
    annotation_type TEXT,
    annotation_state TEXT,
    ex_temperature_value REAL,
    ex_temperature_unit TEXT,
    ex_temperature_trend TEXT,
    ex_humidity_value REAL,
    ex_humidity_unit TEXT,
    ex_humidity_trend TEXT,
    ex_illuminance_value REAL,
    ex_illuminance_unit TEXT,
    ex_illuminance_trend TEXT
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
                        insert_flat_data(data)
                    except Exception as e:
                        print(f"JSON 파싱 실패: {file} in {zip_path} — {e}")

# JSON → INSERT 함수
def insert_flat_data(data):
    m = data["meta_info"][0]
    s = data["sensor_data"][0]
    ir = data["ir_data"][0]["temp_max"][0]
    ann = data["annotations"][0]["tagging"][0]
    ext = data["external_data"][0]

    def g(sensor, key):
        return s.get(sensor, [{}])[0].get(key)

    cur.execute("""
        INSERT INTO full_flat_sensor_data VALUES (
            NULL, ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,
            ?,?,?,
            ?,?,?,
            ?,?,?,
            ?,?,?,
            ?,?,?,
            ?,?,?,
            ?,?,?,
            ?,?,?,
            ?,?,?,
            ?,?,?,
            ?,?,?,
            ?,?,?,
            ?,?,?
        )
    """, (
        m.get("device_id"),
        m.get("device_manufacturer"),
        m.get("device_name"),
        m.get("dust_sensor_manufacturer"),
        m.get("dust_sensor_name"),
        m.get("temp_sensor_manufacturer"),
        m.get("temp_sensor_name"),
        m.get("overcurrent_sensor_manufacturer"),
        m.get("overcurrent_sensor_name"),
        m.get("thermal_camera_sensor_manufacturer"),
        m.get("thermal_camera_sensor_name"),
        m.get("installation_environment"),
        m.get("collection_date"),
        m.get("collection_time"),
        m.get("duration_time"),
        m.get("sensor_types"),
        m.get("cumulative_operating_day"),
        m.get("equipment_history"),
        m.get("img-id"),
        m.get("location"),
        m.get("filename"),
        m.get("img_name"),
        m.get("img_description"),
        g("PM10", "value"), g("PM10", "data_unit"), g("PM10", "trend"),
        g("PM2.5", "value"), g("PM2.5", "data_unit"), g("PM2.5", "trend"),
        g("PM1.0", "value"), g("PM1.0", "data_unit"), g("PM1.0", "trend"),
        g("NTC", "value"), g("NTC", "data_unit"), g("NTC", "trend"),
        g("CT1", "value"), g("CT1", "data_unit"), g("CT1", "trend"),
        g("CT2", "value"), g("CT2", "data_unit"), g("CT2", "trend"),
        g("CT3", "value"), g("CT3", "data_unit"), g("CT3", "trend"),
        g("CT4", "value"), g("CT4", "data_unit"), g("CT4", "trend"),
        ir.get("value_TGmx"), ir.get("X_Tmax"), ir.get("Y_Tmax"),
        ann.get("annotation_type"), ann.get("state"),
        ext["ex_temperature"][0]["value"], ext["ex_temperature"][0]["data_unit"], ext["ex_temperature"][0]["trend"],
        ext["ex_humidity"][0]["value"], ext["ex_humidity"][0]["data_unit"], ext["ex_humidity"][0]["trend"],
        ext["ex_illuminance"][0]["value"], ext["ex_illuminance"][0]["data_unit"], ext["ex_illuminance"][0]["trend"]
    ))

# data/ 아래의 모든 zip 처리
for zip_file in glob("data/*.zip"):
    extract_json_from_zip(zip_file)

# 저장
conn.commit()
conn.close()

# DB 경로 반환
db_path