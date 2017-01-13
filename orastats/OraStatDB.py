# !/usr/bin/env python
# coding: utf-8
import MySQLdb as msqldb

class orastatdb(object):
    def __init__(self,mysqldb):
        mysqlconn = {}

        mysqlconn['db_ip']      = mysqldb[0][0]
        mysqlconn['db_port']    = mysqldb[0][1]
        mysqlconn['db_name']    = mysqldb[0][2]
        mysqlconn['username']   = mysqldb[0][3]
        mysqlconn['passwd']     = mysqldb[0][4]
        mysqlconn['charset']    = mysqldb[0][5]
        # print mysqlconn['db_ip']
        self.mysqlconn = mysqlconn

    def connect(self):
        self.saveconn = msqldb.connect( host    = self.mysqlconn['db_ip'],
                                        port    = int(self.mysqlconn['db_port']) ,
                                        user    = self.mysqlconn['username'],
                                        passwd  = self.mysqlconn['passwd'],
                                        db      = self.mysqlconn['db_name'],
                                        charset = self.mysqlconn['charset'])


    def processrows(self):
        pass

    def close(self):
        pass

    # def db_connect(self):

    #     try:
    #         if self.mysqlconn['db_type'] == "mysql":
    #             import MySQLdb as msqldb
    #             self.saveconn = msqldb.connect(host=self.connsavedb['db_ip'], user=self.connsavedb['username'],
    #                                            passwd=self.connsavedb['password'], db=self.connsavedb['db_name'],
    #                                            charset="utf8")
    #             self.savecurs = self.saveconn.cursor()
    #         if self.connsavedb['db_type'] == "oracle":
    #             # printf('Connect db username %s host %s\n',self.connsavedb['username'],self.connsavedb['db_url'])
    #             self.saveconn = db.connect(self.connsavedb['username'], self.connsavedb['password'],
    #                                        self.connsavedb['db_url'])
    #             self.savecurs = self.saveconn.cursor()
    #     except Exception, e:
    #         print str(e)
    #         os._exit(0)
        # raise e


    # def savetodb(self):

    #     insert_time = int(time.time())
    #     if len(self.rows) > 0 and len(self.rows[0]) == 2:
    #         try:
    #             param = []
    #             for self.row in self.rows:
    #                 str1 = self.splitrow()
    #                 keyname = str1[1]
    #                 keyalter = str1[2]
    #                 keyalter1 = str1[3]
    #                 keyvalues = self.row[1]

    #                 param.append((str(datetime.datetime.fromtimestamp(insert_time)), str(self.conndb['db_unique_id']),
    #                               str(self.mointorinfo['key']), str(keyname), str(keyalter), str(keyalter1),
    #                               str(keyvalues)))

    #             if self.connsavedb['db_type'] == "oracle":
    #                 self.savecurs.prepare(
    #                     "insert into MONI_RESULT(INSERT_TIME, DB_UNIQUE_ID, MONI_KEY,MONI_ITEM,MONI_ALERT,MONI_ALERT1,MONI_VALUE) values(to_date(:1,'yyyy-mm-dd hh24:mi:ss'), :2, :3,:4, :5, :6, :7)")  # 一次插入全部数据
    #                 self.savecurs.executemany(None, param)
    #             if self.connsavedb['db_type'] == "mysql":
    #                 # print param
    #                 sql = "insert into MONI_RESULT(INSERT_TIME, DB_UNIQUE_ID, MONI_KEY,MONI_ITEM,MONI_ALERT,MONI_ALERT1,MONI_VALUE) values(%s,%s,%s,%s,%s,%s,%s)"
    #                 self.savecurs.executemany(sql, param)

    #             self.saveconn.commit()
    #         except Exception, err:
    #             print err
