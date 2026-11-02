import pymysql

conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root',
                       database='zhhengguan_research', charset='utf8mb4')
cur = conn.cursor()
for t in ['api_pspa_teacher', 'api_pspa_achievement', 'api_pspa_notice', 'api_pspa_stat']:
    cur.execute("SELECT COUNT(*) FROM %s" % t)
    print(t, cur.fetchone()[0])
cur.execute("SELECT stat_key, label, value, unit FROM api_pspa_stat ORDER BY id")
for row in cur.fetchall():
    print('  ', row)
cur.execute("SELECT publish_date FROM api_pspa_achievement LIMIT 3")
print('sample dates', cur.fetchall())
conn.close()
