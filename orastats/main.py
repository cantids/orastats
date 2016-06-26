#!/usr/bin/env python
# coding: utf-8
import argparse
import cx_Oracle
import inspect
import json
import re
from time import time
# from termcolor import colored
from .__init__ import __version__
from .__init__ import __author__

def args(*args, **kwargs):
  def _decorator(func):
    func.__dict__.setdefault('args', []).insert(0, (args, kwargs))
    return func

  return _decorator

class ColumnHeader(object):
  def __init__(self, title):
    self.title = title.strip()
    self.summary = None

  def add_summary(self, column):
    self.summary = ColumnSummary(self, column)

  def __unicode__(self):
    return self.title

  def __str__(self):
    return self.title

class ColumnStat(object):
  def __init__(self, label, statfn, precision=2, handles_null=False):
    self.label = label
    self.statfn = statfn
    self.precision = precision
    self.handles_null = handles_null

  def __call__(self, coldata):
    self.value = round(float(self.statfn(coldata)), self.precision) if coldata else 0

  def __unicode__(self):
    return self.label

  def foo(self):
    return "foobar"

class ColumnSummary(object):
  def __init__(self, header, col):
    self._header = header
    self._stats = [
      ColumnStat("Sum", sum),
      ColumnStat("Avg", lambda x: float(sum(x)) / float(len(x))),
      ColumnStat("Min", min),
      ColumnStat("Max", max),
      ColumnStat("NUL", lambda x: int(sum(map(lambda y: 1 if y is None else 0, x))), 0, True)
    ]
    without_nulls = list(map(lambda x: 0 if x is None else x, col))

    for stat in self._stats:
      stat(col) if stat.handles_null else stat(without_nulls)

  @property
  def stats(self):
    # dict comprehensions are not supported in Python 2.6, so do this instead
    return dict((c.label, c.value) for c in self._stats)

  def __str__(self):
    return str(self._header)

class QueryResult(object):
  def __init__(self, sql, cursor, debug=False):

    self.sql = sql
    self.cursor = cursor
    duration = self.execute_query()

    self._description = cursor.description or []
    # if self.args.debug:
    #         print sql
    self._debug=debug
    self._data = [list(r) for r in cursor.fetchall()]
    self.duration = duration
    cursor.close()
    self._headers = self._get_headers()
    self._summary = {}

  @property
  def data(self):
    return self._data or []

  @property
  def headers(self):
    return self._headers or []

  def _get_headers(self):
    return [ColumnHeader(d[0]) for d in self._description] if self._description else [ColumnHeader('--')]

  def _get_numerics(self):
    # conn = get_connection()
    if hasattr(conn.Database, "NUMBER"):
      return [ix for ix, c in enumerate(self._description) if
          hasattr(c, 'type_code') and c.type_code in conn.Database.NUMBER.values]
    elif self.data:
      d = self.data[0]
      return [ix for ix, _ in enumerate(self._description) if
          not isinstance(d[ix], six.string_types) and six.text_type(d[ix]).isnumeric()]
    return []

  def _get_transforms(self):
    transforms = dict(app_settings.EXPLORER_TRANSFORMS)
    return [(ix, transforms[str(h)]) for ix, h in enumerate(self.headers) if str(h) in transforms.keys()]

  def column(self, ix):
    return [r[ix] for r in self.data]

  def process(self):
    start_time = time()

    self.process_columns()
    self.process_rows()

    # logger.info("Explorer Query Processing took %sms." % ((time() - start_time) * 1000))

  def process_columns(self):
    for ix in self._get_numerics():
      self.headers[ix].add_summary(self.column(ix))

  def process_rows(self):
    transforms = self._get_transforms()
    if transforms:
      for r in self.data:
        for ix, t in transforms:
          r[ix] = t.format(str(r[ix]))

  def execute_query(self):
    start_time = time()
    try:
      self.cursor.execute(self.sql)
    except Exception as e:
      self.cur.close()
      print str(e)
      raise e

    return ((time() - start_time) * 1000)

  def getcolformatstr(self, coldef):
    if coldef[1] == cx_Oracle.NUMBER:
      collength = 12;
    else:
      if coldef[2] <= 10:
        collength = coldef[2]
      elif coldef[2] > 10  and coldef[2] <= 32 :
        collength = coldef[2] - 5
      elif coldef[2] > 32  and coldef[2] < 64:
        collength = 30
      elif coldef[2] > 64  and coldef[2] <= 128:
        collength = 30
      elif coldef[2] > 128 and coldef[2] <= 600:
        collength = 60
      else:
        collength = 32
      if coldef[2] < len(coldef[0]):
        collength = len(coldef[0])

    return collength

  def show_rows(self):

    if self._data != []:
      if self._debug:
        print ('-' * 128)
        for col in self._description:
          print ('Name: \033[1;31;40m%-20s\033[0m' % col[0]),
          print ('Type: \033[1;31;40m%10s\033[0m' % str(col[1])),
          print ('Display Size: \033[1;31;40m%5s\033[0m' % str(col[2])),
          print ('Internal Size: \033[1;31;40m%5s\033[0m' % str(col[3])),
          print ('Precision : \033[1;31;40m%5s\033[0m' % str(col[4])),
          print ('Scale : \033[1;31;40m%2s\033[0m' % str(col[5])),
          print ('Nullable : \033[1;31;40m%2s\033[0m' % str(col[6])),
          print ('Print Display : \033[1;31;40m%5s\033[0m' % str(self.getcolformatstr(col)))
        print ('-' * 128 + "\n")

      for col in self._description:
        colformatstr = ('%-' + str(self.getcolformatstr(col)) + 's')
        print(colformatstr % (col[0])),
      print('');
      for col in self._description:
        print('-' * self.getcolformatstr(col)),
      print('');

      for row in self._data:
        for i in range(len(row)):
          colformatstr = ('%-' + str(self.getcolformatstr(self._description[i])) + 's')
          if row[i] != None:
            print(colformatstr % row[i]), ;
          else:
            print(colformatstr % ''), ;
        print('')

class OraStats(object):
  '''
    query database infomartion
  '''
  debug=False
  def version(self):

    """Print Oracle version (Banner)"""
    sql = "select banner from v$version where rownum=1"
    self.cur.execute(sql)
    res = self.cur.fetchall()
    print "数据库版本信息如下"
    Res=QueryResult(sql, self.cur)
    Res.show_rows()

  def checkdb(self):
    """Check Database Connect"""
    sql = "select 'ConnectOK' from dual"
    self.cur.execute(sql)
    res = self.cur.fetchall()
    for row in res:
      if row[0] == "ConnectOK":
        print "数据库连接正常"
      else:
        print "数据库连接异常"

  def tbs(self):
    """Print Database tablespace usage"""
    sql = '''SELECT
                D.STATUS                                                      STATUS
              , D.TABLESPACE_NAME                                             NAME
              , D.CONTENTS                                                    TYPE
              , D.EXTENT_MANAGEMENT                                           EXTENT_MGT
              , D.SEGMENT_SPACE_MANAGEMENT                                    SEGMENT_MGT
              , NVL(A.BYTES, 0)/1024/1024                                     TS_SIZE
              , ROUND(A.MAXBYTES/1048576)                                     MAX_MB
              , ROUND(NVL(A.BYTES -  NVL(F.BYTES, 0), 0)/1024/1024,2)         USED
              , ROUND(F.BYTES/1048576)                                        FREE_MB
              , ROUND(NVL((A.BYTES - NVL(F.BYTES, 0)) / A.BYTES * 100, 0),2)  PCT_USED
              , ROUND(F.BYTES/A.BYTES * 100 ,2)                               PCT_FREE
              , ROUND((A.MAXBYTES-A.BYTES+F.BYTES)/ A.MAXBYTES * 100,2)       MAX_PCT_FREE
            FROM
                SYS.DBA_TABLESPACES D
              , ( SELECT TABLESPACE_NAME, SUM(BYTES) BYTES,SUM(DECODE(MAXBYTES, 0, BYTES, MAXBYTES)) MAXBYTES
                  FROM DBA_DATA_FILES
                  GROUP BY TABLESPACE_NAME
                ) A
              , ( SELECT TABLESPACE_NAME, SUM(BYTES) BYTES
                  FROM DBA_FREE_SPACE
                  GROUP BY TABLESPACE_NAME
                ) F
            WHERE
                  D.TABLESPACE_NAME = A.TABLESPACE_NAME(+)
              AND D.TABLESPACE_NAME = F.TABLESPACE_NAME(+)
              AND NOT (
                D.EXTENT_MANAGEMENT LIKE 'LOCAL'
                AND
                D.CONTENTS LIKE 'TEMPORARY'
              )
            UNION ALL
            SELECT
                D.STATUS                                                  STATUS
              , D.TABLESPACE_NAME                                         NAME
              , D.CONTENTS                                                TYPE
              , D.EXTENT_MANAGEMENT                                       EXTENT_MGT
              , D.SEGMENT_SPACE_MANAGEMENT                                SEGMENT_MGT
              , NVL(A.BYTES, 0)/1024/1024                                 TS_SIZE
              , ROUND(A.MAXBYTES/1048576)                                 MAX_MB
              , ROUND(NVL(T.BYTES, 0)/1024/1024,2)                        USED
              , ROUND((A.BYTES-NVL(T.BYTES,0))/1048576)                   FREE_MB
              , ROUND(NVL(T.BYTES / A.BYTES * 100, 0),2)                  PCT_USED
              , ROUND((A.BYTES-NVL(T.BYTES,0)) / A.BYTES * 100,2)         PCT_FREE
              , ROUND((A.MAXBYTES-NVL(T.BYTES,0)) / A.MAXBYTES * 100,2)   MAX_PCT_FREE
            FROM
                SYS.DBA_TABLESPACES D
              , ( SELECT TABLESPACE_NAME, SUM(BYTES) BYTES,SUM(DECODE(MAXBYTES, 0, BYTES, MAXBYTES)) MAXBYTES
                  FROM DBA_TEMP_FILES
                  GROUP BY TABLESPACE_NAME
                ) A
              , ( SELECT TABLESPACE_NAME, SUM(BYTES_CACHED) BYTES
                  FROM V$TEMP_EXTENT_POOL
                  GROUP BY TABLESPACE_NAME
                ) T
            WHERE
                  D.TABLESPACE_NAME = A.TABLESPACE_NAME(+)
              AND D.TABLESPACE_NAME = T.TABLESPACE_NAME(+)
              AND D.EXTENT_MANAGEMENT LIKE 'LOCAL'
              AND D.CONTENTS LIKE 'TEMPORARY'
            ORDER BY PCT_USED'''

    Res=QueryResult(sql, self.cur)
    Res.show_rows()

  def dbf(self):
    """Print Database Datafile usage"""
    sql = '''SELECT /*+ ordered */
            d.tablespace_name                     tablespace
          , d.file_name                           filename
          , round(d.bytes/1024/1024)              filesize
          , d.autoextensible                      autoextensible
          , d.increment_by * e.value/1024/1024    increment_by
          , round(d.maxbytes/1024/1024)           maxbytes
          , d.status                              STATUS
        FROM
            sys.dba_data_files d
          , v$datafile v
          , (SELECT value
             FROM v$parameter
             WHERE name = 'db_block_size') e
        WHERE
          (d.file_name = v.name)
        UNION
        SELECT
            d.tablespace_name                     tablespace
          , d.file_name                           filename
          , round(d.bytes/1024/1024)              filesize
          , d.autoextensible                      autoextensible
          , d.increment_by * e.value/1024/1024    increment_by
          , round(d.maxbytes/1024/1024)           maxbytes
          , d.status                              STATUS
        FROM
            sys.dba_temp_files d
          , (SELECT value
             FROM v$parameter
             WHERE name = 'db_block_size') e
        ORDER BY
            1
          , 2
        '''
    Res=QueryResult(sql, self.cur)
    Res.show_rows()

  def asm(self):
    """Print Database ASM Diskgroup usage"""
    sql = '''SELECT
            name                                     group_name
          , sector_size                              sector_size
          , block_size                               block_size
          , allocation_unit_size                     allocation_unit_size
          , state                                    state
          , type                                     type
          , total_mb                                 total_mb
          , (total_mb - free_mb)                     used_mb
          , ROUND((1- (free_mb / total_mb))*100, 2)  pct_used
        FROM
            v$asm_diskgroup
        WHERE
            total_mb != 0
        ORDER BY
            name
        '''
    Res = QueryResult(sql, self.cur)
    Res.show_rows()

  def userlock(self):
    """Print Database User Lock Information """
    sql = '''SELECT
             username,
             account_status
        FROM dba_users
        WHERE (account_status LIKE '%EXPIRED%'
              OR account_status LIKE '%LOCKED%\')
            AND username NOT in('DBSNMP','DMSYS','ORACLE_OCM', 'OLAPSYS', 'WMSYS', 'XDB', 'SCOTT', 'OUTLN', 'PERFSTAT', 'MGMT_VIEW', 'SYS',
            'SYSTEM','TSMSYS', 'DIP', 'SYSMAN','ANONYMOUS', 'MONI', 'BACKUP', 'ORASYSSI','ORDDATA','SI_INFORMTN_SCHEMA','ORDPLUGINS','XS$NULL',
            'TIVOLI','EXFSYS','APPQOSSYS', 'CTXSYS','MDSYS','ORDSYS','APEX_030200','OWBSYS','SQLTXADMIN','SPA','SPATIAL_CSW_ADMIN_USR',
            'OWBSYS_AUDIT','APEX_PUBLIC_USER','MDDATA', 'FLOWS_FILES','SPATIAL_WFS_ADMIN_USR')
        '''
    Res=QueryResult(sql, self.cur)
    Res.show_rows()

  def lock(self):

    """Print Database Lock"""
    sql = """
          Select 'node ' || a_s.INST_ID || ' session ' || a_s.sid || ',' || a_s.SERIAL# ||
           ' blocking node ' || b_s.INST_ID || ' session ' || b_s.SID || ',' ||
           b_s.SERIAL# blockinfo
           -- , a_s.INST_ID
           -- , a_s.SID
           -- , a_S.SERIAL#
           , a_s.SCHEMANAME
           -- , a_s.MODULE
           , a_s.STATUS
           -- , tmp.SECONDS_IN_WAIT||'s' SECONDS_IN_WAIT
           -- ,'block_info'
           -- , b_s.INST_ID blocked_inst_id
           -- , b_s.SID blocked_sid
           , b_s.SCHEMANAME blocked_SCHEMANAME
           -- , b_s.EVENT blocked_event
           -- , b_s.MODULE blocked_module
           -- , b_s.STATUS blocked_status
           -- , b_s.SQL_ID blocked_sql_id
           -- , vsql.SQL_TEXT
           , obj.owner blocked_owner
           , obj.object_name blocked_object_name
           -- , obj.OBJECT_TYPE blocked_OBJECT_TYPE
           , case
              when b_s.ROW_WAIT_OBJ# <> -1 then
               dbms_rowid.rowid_create(1,
                                       obj.DATA_OBJECT_ID,
                                       b_s.ROW_WAIT_FILE#,
                                       b_s.ROW_WAIT_BLOCK#,
                                       b_s.ROW_WAIT_ROW#)
              else
               '-1'
             end blocked_rowid --被阻塞数据的rowid
           -- ,decode(obj.object_type,
           --        'TABLE',
           --        'select * from ' || obj.owner || '.' || obj.object_name ||
           --        ' where rowid=''' ||
           --        dbms_rowid.rowid_create(1,
           --                                obj.DATA_OBJECT_ID,
           --                                b_s.ROW_WAIT_FILE#,
           --                                b_s.ROW_WAIT_BLOCK#,
           --                                b_s.ROW_WAIT_ROW#) || '''',
           --        NULL) blocked_data_querysql
      from gv$session a_s,
           gv$session b_s,
           dba_objects obj,
           v$sql vsql,
           (select sb.sid as tmpsid,
                   sb.serial# as tmpserial# ,
                   sb.username,
                   'blocked',
                   sw.sid,
                   sw.serial#,
                   sw.username,
                   swt.SECONDS_IN_WAIT
              from v$lock         lb,
                   v$lock         lw,
                   v$session      sb,
                   v$session      sw,
                   v$sql          qb,
                   v$sql          qw,
                   v$session_wait swt
             where lb.sid = sb.sid
               and lw.sid = sw.sid
               and lb.sid = swt.sid
               and sb.prev_sql_addr = qb.address
               and sw.sql_address = qw.address
               and lb.id1 = lw.id1
               and sb.lockwait is null
               and sw.lockwait is not null
               and lb.block = 1) tmp
     where b_s.BLOCKING_INSTANCE is not null
       and b_s.BLOCKING_SESSION is not null
       and a_s.INST_ID = b_s.BLOCKING_INSTANCE
       and a_s.SID = b_s.BLOCKING_SESSION
       and b_s.ROW_WAIT_OBJ# = obj.object_id(+)
       and vsql.SQL_ID = b_s.SQL_ID
       and tmp.tmpsid = a_s.SID
       and tmp.tmpserial# = a_S.SERIAL#
     order by a_s.inst_id, a_s.sid
    """
    self.cur.execute(sql)
    res = self.cur.fetchall()
    print "数据库对象锁信息如下"
    Res=QueryResult(sql,self.cur,self.debug)
    Res.show_rows()

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
    parser.add_argument('-U', '--username', default='zabbix', help="Database Username with sys views grant",
              required=False)
    parser.add_argument('-P', '--passwd', default='zabbix', help="Database Username Password", required=False)
    parser.add_argument('-i', '--ipaddress', default='192.168.56.65', help="Database Ip Address", required=False)
    parser.add_argument('-p', '--port', default='1521', help="Database Port ", required=False)
    parser.add_argument('-d', '--database', default='orcl', help="Database Service Name", required=False)
    parser.add_argument('-n', '--node', default='all', help="Check Database Ip, all", required=False)
    parser.add_argument('-v', '--version', action='version', version=' %(prog)s '+ __version__ + ' by ' + __author__)
    parser.add_argument("-D", "--debug", action="store_true", dest="debug", default=False,
              help="Debug mode ,print more info")

    subparsers = parser.add_subparsers(dest='stat')

    for (name, method) in self.methods_of():
      helpdesc = getattr(method, '__doc__', None)
      p = subparsers.add_parser(name, help=helpdesc)
      argnames = inspect.getargspec(method).args[1:]
      for argname in argnames:
        p.add_argument(argname)
      p.set_defaults(func=method, argnames=argnames)

    parser_a = subparsers.add_parser('add', help='add Database Information',formatter_class=argparse.ArgumentDefaultsHelpFormatter )
    parser_a.add_argument('-ni', '--newip', help="Database Ip Address", required=True)
    parser_a.add_argument('-nu', '--newusername', help="Database Username with sys views grant", required=False)
    parser_a.add_argument('-nP', '--newpasswd', help="Database Username Password", required=False)
    parser_a.add_argument('-np', '--newport', help="Database Port ", required=True)
    parser_a.add_argument('-ns', '--newservicename', help="Database Service Name", required=True)

    parser_d = subparsers.add_parser('del', help='del database Information',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_d.add_argument('-ni', '--newip', help="Database Ip Address", required=True)
    parser_d.add_argument('-nu', '--newusername', default='', help="Database Username with sys views grant", required=False)
    parser_d.add_argument('-nP', '--newpasswd', default='', help="Database Username Password", required=False)
    parser_d.add_argument('-np', '--newport', help="Database Port ", required=True)
    parser_d.add_argument('-ns', '--newservicename', help="Database Service Name", required=True)

    parser_i = subparsers.add_parser('init', help='init Database and create table ora_db_info', )

    parser_l = subparsers.add_parser('list', help='list Database ', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_l.add_argument('-n', '--node', default='all', help="Database Ip, all", required=False)

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
    sql = "INSERT INTO ORA_DB_INFO(DB_IPADDR,DB_PORT,DB_SERVICENAME,DB_USER,DB_PASS) VALUES ('"
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
    sql = "delete from ora_db_info where db_ipaddr = '" + self.args.newip + "' and db_port = '" + self.args.newport + "' and db_servicename='" + self.args.newservicename + "'"
    try:
      self.oracur.execute(sql)
    finally:
      self.oracur.close()
      self.oradb.commit()
      print "Delete database Successfully"

  def db_init(self):
    sql = '''
          CREATE TABLE "ORA_DB_INFO"
          (
            "DB_ID"              NUMBER,
            "DB_IPADDR"          VARCHAR2(20 BYTE),
            "DB_PORT"            VARCHAR2(6 BYTE),
            "DB_SERVICENAME"     VARCHAR2(20  BYTE),
            "DB_USER"            VARCHAR2(30 BYTE),
            "DB_PASS"            VARCHAR2(30 BYTE),
            "DB_STATUS"          CHAR(1) default 1
          )
          '''
    try:
      self.oracur.execute(sql)
    finally:
      self.oracur.close()
      self.oradb.commit()
      print "InIt database Successfully"

  def db_list(self):
    if self.args.node != 'local':
      dbip = self.args.node
      if self.args.node == 'all':
        dbip = ''
      sql = "select nvl(DB_USER,'zabbix') dbusers,nvl(DB_USER,'zabbix') dbuserspasswd,DB_IPADDR,DB_PORT,DB_SERVICENAME from ORA_DB_INFO where DB_STATUS = 1 AND DB_IPADDR like '%" + dbip + "%'"
      self.oracur.execute(sql)
      rows = self.oracur.fetchall()
      self.oradb.close()
    else:
      rows = [(self.args.username, self.args.passwd,self.args.ipaddress,self.args.port,self.args.database)]
    return rows

  def __call__(self):
    try:
      self.oradb = self.db_connect(self.args.username, self.args.passwd, self.args.ipaddress, self.args.port,
                     self.args.database)
      self.oracur = self.oradb.cursor()
      if self.args.debug:
        OraStats.debug = self.args.debug
      if self.args.stat == "add":
        self.db_add()
      elif self.args.stat == "del":
        self.db_del()
      elif self.args.stat == "init":
        self.db_init()
      elif self.args.stat == "list":
        for row in self.db_list():
          print "Database : [\033[1;31;40m" + row[2] + "\033[0m] Port : [\033[1;31;40m" + row[3] + "\033[0m] Service_Name : [\033[1;31;40m" + row[4]+"\033[0m]"
      else:
        for row in self.db_list():
          print "Database : [\033[1;31;40m" + row[2] + "\033[0m] Port : [\033[1;31;40m" + row[3] + "\033[0m] Service_Name : [\033[1;31;40m" + row[4
            ]+"\033[0m]"+ " Information :"
          if self.db_conn(row):
            a = self.args
            callargs = [getattr(a, name) for name in a.argnames]
            try:
              self.args.func(*callargs)
            finally:
              self.db_close()
    except Exception, err:
      print str(err)

def run():
  main = Main()
  main()

if __name__ == "__main__":
  run()



