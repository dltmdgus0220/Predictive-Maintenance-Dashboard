import sqlite3
import pandas as pd

# DB 연결
conn = sqlite3.connect("db/sensor_data.sqlite")

# SQL 쿼리 실행
query = "SELECT * FROM external_data" # 테이블명 언젠가 바꿀 수도...

df = pd.read_sql_query(query, conn)
print(df.info())

print(df.head(30))

# 연결 종료
conn.close()