# Hello world
import sqlite3

conn = sqlite3.connect(r'E:\CodeProject\PycharmProjects\project1\scientificProject\data\database.db')
c = conn.cursor()
sql_text_1 = """CREATE TABLE IF NOT EXISTS scores (
id integer PRIMARY key,
name text,
class text,
gender text);"""

c.execute(sql_text_1)
for i in range(3, 10):
    sql_text_2 = f"INSERT INTO scores VALUES ({i},'jxy','1','boy');"
    c.execute(sql_text_2)

conn.commit()

c.close()
conn.close()
