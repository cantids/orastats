#!/usr/bin/env python
# coding: utf-8
import argparse
import cx_Oracle
import sqlite3
import re
import configparser
import os

from QueryDB import OraStats
from OraStatDB import orastatdb


# from termcolor import colored
from .__init__ import __version__
from .__init__ import __author__


class Main(OraStats):

  def methods_of(obj):
    """
      Get all callable methods of an object that don't start with underscore
      returns a list of tuples of the form (method_name, method)
    """
    result = []
    for i in dir(obj):
      if callable(getattr(obj, i)) and not i.startswith('_') and not i.startswith("db_") and not i.startswith(
          "methods_of"):
        result.append((i, getattr(obj, i)))
    return result

  def __init__(self):

    parser = argparse.ArgumentParser('orastats', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-g', '--group', default='all', help="Check Database Group, all", required=False)
    parser.add_argument('-n', '--node', default='all', help="Check Database Ip, all", required=False)
    parser.add_argument('-s', '--servicename', help="Database Service Name", required=False)
    parser.add_argument('-t', '--type',default='sqlite3', help="Database Type sqlnite,oracle,mysql", required=False)
    parser.add_argument('--savedb',action="store_true", dest="savedb", default=False, help="Save Query Data to database")
    parser.add_argument('-v', '--version', action='version', version=' %(prog)s '+ __version__ + ' by ' + __author__)
    parser.add_argument("-D", "--debug", action="store_true", dest="debug", default=False,
              help="Debug mode ,print more info")
    parser.add_argument("-c", "--csv", action="store_true", dest="print_csv", default=False,
              help="Print SQL Resute Csv format")
    # parser.add_argument('-i', '--ipaddress', default='192.168.56.65', help="Database Ip Address", required=False)
    # parser.add_argument('-p', '--port', default='1521', help="Database Port ", required=False)
    # parser.add_argument('-s', '--servicename',default='all', help="Database Service Name", required=False)
    # parser.add_argument('-d', '--database', default='orcl', help="Database Service Name", required=False)
    # parser.add_argument('-U', '--username', default='zabbix', help="Database Username with sys views grant",
    #           required=False)
    # parser.add_argument('-P', '--passwd', default='zabbix', help="Database Username Password", required=False)
    subparsers = parser.add_subparsers(dest='stat')

    for (name, action_fn) in self.methods_of():
      helpdesc = getattr(action_fn, '__doc__', None)
      p = subparsers.add_parser(name, help=helpdesc)
      action_kwargs = []
      for args, kwargs in getattr(action_fn, 'args', []):
        kwargs.setdefault('dest', args[0][2:])
        if kwargs['dest'].startswith('action_kwarg_'):
            action_kwargs.append(
                    kwargs['dest'][len('action_kwarg_'):])
        else:
            action_kwargs.append(kwargs['dest'])
            kwargs['dest'] = 'action_kwarg_' + kwargs['dest']
        p.add_argument(*args, **kwargs)
      p.set_defaults(action_fn=action_fn)
      p.set_defaults(action_kwargs=action_kwargs)
      p.add_argument('action_args', nargs='*',help=argparse.SUPPRESS)


    parser_a = subparsers.add_parser('add', help='add Database Information',formatter_class=argparse.ArgumentDefaultsHelpFormatter )
    parser_a.add_argument('-ng', '--newgroup', help="Database Group Name", required=True)
    parser_a.add_argument('-ni', '--newip', help="Database Ip Address", required=True)
    parser_a.add_argument('-np', '--newport', help="Database Port ", required=True)
    parser_a.add_argument('-ns', '--newservicename', help="Database Service Name", required=True)
    parser_a.add_argument('-nu', '--newusername', help="Database Username with sys views grant", required=True)
    parser_a.add_argument('-nP', '--newpasswd', help="Database Username Password", required=True)

    parser_d = subparsers.add_parser('del', help='del database Information',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_d.add_argument('-ng', '--newgroup', help="Database Group Name", required=True)
    parser_d.add_argument('-ni', '--newip', help="Database Ip Address", required=True)
    parser_d.add_argument('-np', '--newport', help="Database Port ", required=True)
    parser_d.add_argument('-ns', '--newservicename', help="Database Service Name", required=True)
    parser_d.add_argument('-nu', '--newusername', default='', help="Database Username with sys views grant", required=False)
    parser_d.add_argument('-nP', '--newpasswd', default='', help="Database Username Password", required=False)


    parser_i = subparsers.add_parser('init', help='init Database and create table ora_db_info', )
    parser_i.add_argument('-t', '--type',default='sqlnite', help="Database Type sqlnite,oracle,mysql", required=False)

    parser_l = subparsers.add_parser('list', help='list Database ', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_l.add_argument('-g', '--group',default='all', help="Database Group Name", required=False)
    parser_l.add_argument('-n', '--node', default='all', help="Database Ip, all", required=False)
    parser_l.add_argument('-s', '--servicename', help="Database Service Name", required=False)

    # for automatic add tablespace datafile
    parser_add = subparsers.add_parser('addfile', help='automatic add tablespace datafile',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_add.add_argument('-tw', '--tbswar',    default=80,     help="Tablespace Waring Pct "   , required=False)
    parser_add.add_argument('-dn', '--dbfnum',    default=1,      help="add Datafile number"      , required=False)
    parser_add.add_argument('-as', '--asmfsize',  default=61440,  help="asm free size(Mb)"        , required=False)
    parser_add.add_argument('-ds', '--dbfsize',   default=20480,  help="Database Port "           , required=False)
    parser_add.add_argument('-tn', '--tbsname',   default=None,   help="Database Tablespace Name ", required=False)
    parser_add.add_argument('-test', '--test',    action="store_true", default=False, help="Database Tablespace Name ", required=False)

    parser_add = subparsers.add_parser('savedbadd', help='save query data to database,only support mysql ',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_add.add_argument( '--sip',         default='127.0.0.1',      help="Mysql Database Machine IP"   , required=True)
    parser_add.add_argument( '--sport',       default=3306,             help="Mysql Database Machine Port" , required=True)
    parser_add.add_argument( '--sdbname',     default='oramon',         help="Mysql Database Name"        , required=True)
    parser_add.add_argument( '--susername',   default='zabbix',         help="Database Port "           , required=True)
    parser_add.add_argument( '--spwd',        default='zabbix',         help="Database Tablespace Name ", required=True)
    parser_add.add_argument( '--scharset',    default='UTF8',           help="Database Tablespace Name ", required=True)

    self.args = parser.parse_args()

  def db_connect(self, username, password, address, port, database):
    try:
      return cx_Oracle.connect(username, password, '//' + address + ':' + port + '/' + database)
    except Exception, dberror:
      print str(dberror)
      # return False

  def db_close(self):
    self.db.close()

  def db_conn(self, row):
    self.db = self.db_connect(row[0], row[1], row[2], row[3], row[4])
    if self.db != None:
      try:
        self.cur = self.db.cursor()
        return True
      except Exception, dberror:
        print str(dberror)
        return False

  def db_add(self):
    if self.args.newusername == None:
      dbusername = 'NULL,'
    else:
      dbusername = "'" + self.args.newusername + "',"

    if self.args.newpasswd == None:
      dbuserpasswd = 'NULL'
    else:
      dbuserpasswd = "'" + self.args.newpasswd + "'"
    sql = "INSERT INTO ORA_DB_INFO(DB_GROUP,DB_IPADDR,DB_PORT,DB_SERVICENAME,DB_USER,DB_PASS) VALUES ('"
    sql += self.args.newgroup + "','"
    sql += self.args.newip + "','"
    sql += self.args.newport + "','"
    sql += self.args.newservicename + "',"
    sql += dbusername
    sql += dbuserpasswd + ')'
    # print sql
    try:
      self.oracur.execute(sql)
    finally:
      self.oracur.close()
      self.oradb.commit()
      print "add database Successfully"

  def db_del(self):
    sql = "delete from ora_db_info where DB_GROUP = '" + self.args.newgroup + "' and db_ipaddr = '" + self.args.newip + "' and db_port = '" + self.args.newport + "' and db_servicename='" + self.args.newservicename + "'"
    try:
      self.oracur.execute(sql)
    finally:
      self.oracur.close()
      self.oradb.commit()
      print "Delete database Successfully"

  def db_init(self):
    sql_ora_db_info = '''
          CREATE TABLE "ORA_DB_INFO"
          (
            "DB_GROUP"           VARCHAR2(40),
            "DB_ID"              NUMBER,
            "DB_IPADDR"          VARCHAR2(20),
            "DB_PORT"            VARCHAR2(6),
            "DB_SERVICENAME"     VARCHAR2(20 ),
            "DB_USER"            VARCHAR2(30),
            "DB_PASS"            VARCHAR2(30),
            "DB_STATUS"          CHAR(1) default 1
          )
          '''
    sql_ora_save_info = '''
          CREATE TABLE "ORA_SAVE_INFO"
          (
            "DB_IPADDR"          VARCHAR2(20),
            "DB_PORT"            VARCHAR2(6),
            "DB_SERVICENAME"     VARCHAR2(20),
            "DB_USER"            VARCHAR2(30),
            "DB_PASS"            VARCHAR2(30),
            "DB_CHARSET"         VARCHAR2(30)
          )
          '''
    try:
      self.oracur.execute(sql_ora_db_info)
      self.oracur.execute(sql_ora_save_info)
    finally:
      self.oracur.close()
      self.oradb.commit()
      print "InIt database Successfully"

  def db_list(self):
    if self.args.node != 'local':
      dbip = self.args.node
      if self.args.node == 'all':
        dbip = ''

      sql = "select DB_USER dbusers,DB_PASS dbuserspasswd,DB_IPADDR,DB_PORT,DB_SERVICENAME,DB_GROUP from ORA_DB_INFO "
      sql +="where DB_STATUS = 1 AND DB_IPADDR like '%" + dbip + "%' "

      if self.args.group != 'all':
        sql +="AND DB_GROUP = '" + self.args.group + "' "
      if self.args.servicename != None:
        sql +="AND DB_SERVICENAME = '" + self.args.servicename + "'"
      sql +="order by DB_IPADDR"

      self.oracur.execute(sql)
      rows = self.oracur.fetchall()
      self.oradb.close()
    else:
      rows = [(self.args.username, self.args.passwd,self.args.ipaddress,self.args.port,self.args.database)]
    return rows

  def db_conninit(self):
    try:
      # if self.args.type == "sqlite3":
        self.oradb  = sqlite3.connect("orastats.db")
        self.oracur = self.oradb.cursor()
      # elif self.args.type == "oracle":
      #   self.oradb = self.db_connect(self.args.username, self.args.passwd, self.args.ipaddress, self.args.port,
      #                  self.args.database)
      #   self.oracur = self.oradb.cursor()
      # else:
      #   print "not support database"
    except Exception as e:
      raise e
  # def db_addfile(self):
  #   sql = """SELECT COUNT(*) FROM V$asm_diskgroup
  #   """
  #   UserAsm=QueryResult(sql, self.cur)
  #   if UserAsm._data[0][0] == 1:
  #     TbsRes = self.tbs(self.args.tbsname,self.args.tbswar,'PERMANENT')
  #     for tbsrow in TbsRes._data:
  #       AsmRes = self.asm()
  #       for asmrow in AsmRes._data:
  #         if re.findall('_DATA$',asmrow[0]) and asmrow[7] > int(self.args.asmfsize):
  #           sql = "ALTER TABLESPACE " + tbsrow[1] + " ADD DATAFILE "
  #           sql += "'+"+asmrow[0]+"' SIZE "+ str(self.args.dbfsize) +'M AUTOEXTEND OFF'
  #           try:
  #             if self.args.test:
  #               print sql
  #             else:
  #               self.cur.execute(sql)
  #               print ('Tablespace : %-20s Add Datafile Successfully !' % tbsrow[1] )
  #           except Exception, e:
  #             print str(e)
  #         else:
  #           print "[\033[1;31;40m!!! Asm Diskgroup Is Not Enough Size ["+ self.args.asmfsize+"MB] !!!\033[0m]"
  #   else:
  #     print "[\033[1;31;40m!!! Database Is Not Use Asm !!!\033[0m]"
  def savedbadd(self):
    sql = "select count(*) from ORA_SAVE_INFO"
    self.oracur.execute(sql)
    rows = self.oracur.fetchall()
    if rows[0][0] == 0 :
      sql = "INSERT INTO ORA_SAVE_INFO(DB_IPADDR,DB_PORT,DB_SERVICENAME,DB_USER,DB_PASS,DB_CHARSET) VALUES ('"
      sql += self.args.sip + "','"
      sql += self.args.sport + "','"
      sql += self.args.sdbname + "','"
      sql += self.args.susername + "','"
      sql += self.args.spwd + "','"
      sql += self.args.scharset + "')"
      try:
        self.oracur.execute(sql)
      finally:
        self.oracur.close()
        self.oradb.commit()
        print "add database Successfully"
    else:
        print "save database Exist"

    # try:
    #   pass
    # except Exception as e:
    #   raise e
  def __call__(self):
    try:
      q_dbinfo = dict()
      self.db_conninit()
      if self.args.debug:
        OraStats.debug = self.args.debug
      if self.args.stat == "add":
        self.db_add()
      elif self.args.stat == "savedbadd":
        self.savedbadd()
      elif self.args.stat == "del":
        self.db_del()
      elif self.args.stat == "init":
        self.db_init()
      elif self.args.stat == "list":
        for row in self.db_list():
          print ('Group : [\033[1;31;40m%-10s\033[0m] Database : [\033[1;31;40m%-15s\033[0m] Port : [\033[1;31;40m%-6s\033[0m] Service_Name : [\033[1;31;40m%-10s\033[0m]' % (row[5],row[2],row[3],row[4]))
      else:
        a = self.args
        fn = a.action_fn
        fn_args = [arg.decode('utf-8') for arg in a.action_args]
        fn_kwargs = {}
        for k in a.action_kwargs:
            v = getattr(a, 'action_kwarg_' + k)
            if v is None:
                continue
            if isinstance(v, six.string_types):
                v = v.decode('utf-8')
            fn_kwargs[k] = v
        # if self.args.savedb:
        #   sql = "select DB_IPADDR,DB_PORT,DB_SERVICENAME,DB_USER,DB_PASS,DB_CHARSET from ORA_SAVE_INFO"
        #   self.oracur.execute(sql)
        #   savedbarows = self.oracur.fetchall()
        #   b = orastatdb(savedbarows)
        #   b.connect()
        for row in self.db_list():
          if self.args.print_csv == False:
            print ('Group : [\033[1;31;40m%-10s\033[0m] Database : [\033[1;31;40m%-15s\033[0m] Port : [\033[1;31;40m%-6s\033[0m] Service_Name : [\033[1;31;40m%-10s\033[0m]' % (row[5],row[2],row[3],row[4]))
          q_dbinfo['db_ip']   = row[2]
          q_dbinfo['db_name']  = row[4]
          if self.db_conn(row):
            try:
              Res = fn(*fn_args, **fn_kwargs)
              if self.args.print_csv:
                Res.show_rows_csv(q_dbinfo)
              else:
                Res.show_rows()
            except Exception, err:
              print str(err)
            finally:
              self.db_close()
    except Exception, err:
      print str(err)

def run():
  main = Main()
  main()

if __name__ == "__main__":
  run()



