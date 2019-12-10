import MySQLdb

HOST     = 'localhost'
USER     = 'root'
PASSWD   = 'password'
DATABASE = 'society_mysqldb'
def connection():
	conn = MySQLdb.connect(host = HOST, user = USER, passwd = PASSWD, db = DATABASE)
	cursor = conn.cursor()
	return conn, cursor
