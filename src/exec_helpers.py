from settings import *

import datetime
import psycopg2

def query(sql, row_delimiter = '\r\n', field_delimiter = ' '):
	pgsql_conn = psycopg2.connect(PGSQL_DSN)
	cur = pgsql_conn.cursor()
	cur.execute(sql)	

	return row_delimiter.join(field_delimiter.join(unicode(x.decode('utf-8') if type(x) == str else '' if x is None else x).encode('utf-8') for x in i) for i in cur.fetchall())

def day(day_offset = 0):
	return (datetime.date.today() + datetime.timedelta(day_offset)).isoformat()

