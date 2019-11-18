import MySQLdb

HOST     = 'localhost'
USER     = 'root'
PASSWD   = 'Asmath.123'
DATABASE = 'society_mysqldb'
def connection():
	conn = MySQLdb.connect(host = HOST, user = USER, passwd = PASSWD, db = DATABASE)
	cursor = conn.cursor()
	return conn, cursor
