#encoding=utf8
import MySQLdb
import os

class MysqlDriverException(Exception):
    def __init__(self, code, msg):
        Exception.__init__(self)
        self.code = code
        self.message = msg

class mysql_driver():
    def __init__(self):
        try:
            self.conn = MySQLdb.connect(host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'), passwd=os.getenv('DB_PASSWD'), db=os.getenv('DB_NAME'), charset='utf8')
            self.cur = self.conn.cursor()
        except Exception as e:
            raise MysqlDriverException(500, ("数据库链接失败:%s" % e))

    def __del__(self):
        try:
            self.cur.close()
            self.conn.close()
        except Exception as e:
            pass

    def read(self, sql, argv = ''):
        try:
            self.cur.execute(sql, argv)
            return [dict((self.cur.description[i][0], value) for i, value in enumerate(row)) for row in self.cur.fetchall()]
        except Exception as e:
            raise MysqlDriverException(500, ("数据库读取失败:%s" % e))

    def write(self ,sql, argv = ''):
        try:
            self.cur.execute(sql, argv)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise MysqlDriverException(500, ("数据库写入失败:%s" % e))

    def write_ret_val(self):
        try:
            self.cur.execute('SELECT LAST_INSERT_ID()')
            return self.cur.fetchone()[0]
        except Exception as e:
            raise MysqlDriverException(500, ("数据库写入返回值失败:%s" % e))
