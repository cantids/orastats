#!/usr/bin/env python
# coding: utf-8
import argparse
import cx_Oracle
import sqlite3
import inspect
import json
import six
import re
import configparser
import os

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
    # cursor.close()
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
      self.cursor.close()
      print str(e)
      raise e

    return ((time() - start_time) * 1000)

  def getcolformatstr(self, coldef):
    if coldef[1] == cx_Oracle.NUMBER:
      collength = 12;
    else:
      if coldef[2] <= 10:
        collength = coldef[2]
      elif coldef[2] > 10  and coldef[2] <= 20 :
        collength = coldef[2] - 2
      elif coldef[2] > 20  and coldef[2] <= 32 :
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
          print ('Scale : \033[1;31;40m%4s\033[0m' % str(col[5])),
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
    sql = """select banner from v$version where rownum=1"""
    self.cur.execute(sql)
    res = self.cur.fetchall()
    print "数据库版本信息如下"
    return QueryResult(sql, self.cur)

  def checkdb(self):
    """Check Database Connect"""
    sql = '''select 'ConnectOK' as "DB_STATUS" from dual'''
    return QueryResult(sql, self.cur)

  @args('--tbsname', dest='tbsname', metavar='<Tablespace Name>',         help="Database Tablespace Name ", required=False)
  @args('--tbswar',  dest='tbswar',  metavar='<Tablespace User Pct>',     help="Tablespace Waring Pct "   , required=False)
  def tbs(self,tbsname=None,tbswar=0,tbstype=None):
    """Print Database tablespace usage"""
    sql = """
    SELECT * from (SELECT
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
            ORDER BY PCT_USED
            ) where PCT_USED > """ + str(tbswar)
    if tbsname != None:
      sql += " and NAME = upper('"+tbsname+"')"
    if tbstype != None:
      sql += " and TYPE = upper('"+tbstype+"')"
    return QueryResult(sql, self.cur)

  def dbf(self):
    """Print Database Datafile usage"""
    sql = """SELECT /*+ ordered */
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
        """
    return QueryResult(sql, self.cur)

  @args('--asmwar',  dest='asmwar',  metavar='<AsmDiskgroup User Pct>',     help="AsmDiskgroup Waring Pct "   , required=False)
  def asm(self,asmwar=0):
    """Print Database ASM Diskgroup usage"""
    sql = """ SELECT * FROM ( SELECT
            name                                     group_name
          , sector_size                              sector_size
          , block_size                               block_size
          , allocation_unit_size                     au_size
          , state                                    state
          , type                                     type
          , total_mb                                 total_mb
          , free_mb                                  free_mb
          , (total_mb - free_mb)                     used_mb
          , ROUND((1- (free_mb / total_mb))*100, 2)  pct_used
        FROM
            v$asm_diskgroup
            -- asm
        WHERE
            total_mb != 0
        ORDER BY
            name
            ) where pct_used > """ + str(asmwar)

    return QueryResult(sql, self.cur)

  def userlock(self):
    """Print Database User Lock Information """
    sql = """SELECT
             username,
             account_status
        FROM dba_users
        WHERE (account_status LIKE '%EXPIRED%'
              OR account_status LIKE '%LOCKED%\')
            AND username NOT in('DBSNMP','DMSYS','ORACLE_OCM', 'OLAPSYS', 'WMSYS', 'XDB', 'SCOTT', 'OUTLN', 'PERFSTAT', 'MGMT_VIEW', 'SYS',
            'SYSTEM','TSMSYS', 'DIP', 'SYSMAN','ANONYMOUS', 'MONI', 'BACKUP', 'ORASYSSI','ORDDATA','SI_INFORMTN_SCHEMA','ORDPLUGINS','XS$NULL',
            'TIVOLI','EXFSYS','APPQOSSYS', 'CTXSYS','MDSYS','ORDSYS','APEX_030200','OWBSYS','SQLTXADMIN','SPA','SPATIAL_CSW_ADMIN_USR',
            'OWBSYS_AUDIT','APEX_PUBLIC_USER','MDDATA', 'FLOWS_FILES','SPATIAL_WFS_ADMIN_USR')
        """
    return QueryResult(sql, self.cur)

  @args('--pname', dest='pname', metavar='<Parameter Name>',help="Database Parameter Name ", required=True)
  def pm(self,pname=None):
    """Print Database Parameter """
    sql = """
    SELECT  name,VALUE  from v$parameter
    """
    if pname != None:
      sql += " where upper(NAME) like upper('%"+pname+"%')"
    return QueryResult(sql, self.cur)

  def lock(self):

    """Print Database Lock"""

    sql = """ SELECT 'NODE ' || A_S.INST_ID || ' SESSION ' || A_S.SID || ',' || A_S.SERIAL# ||
           ' BLOCKING NODE ' || B_S.INST_ID || ' SESSION ' || B_S.SID || ',' ||
           B_S.SERIAL# BLOCKINFO
           -- , A_S.INST_ID
           -- , A_S.SID
           -- , A_S.SERIAL#
           , A_S.SCHEMANAME
           -- , A_S.MODULE
           , A_S.STATUS
           -- , TMP.SECONDS_IN_WAIT||'S' SECONDS_IN_WAIT
           -- ,'BLOCK_INFO'
           -- , B_S.INST_ID BLOCKED_INST_ID
           -- , B_S.SID BLOCKED_SID
           , B_S.SCHEMANAME BLOCKED_SCHEMANAME
           -- , B_S.EVENT BLOCKED_EVENT
           -- , B_S.MODULE BLOCKED_MODULE
           -- , B_S.STATUS BLOCKED_STATUS
           -- , B_S.SQL_ID BLOCKED_SQL_ID
           -- , VSQL.SQL_TEXT
           , OBJ.OWNER BLOCKED_OWNER
           , OBJ.OBJECT_NAME BLOCKED_OBJECT_NAME
           -- , OBJ.OBJECT_TYPE BLOCKED_OBJECT_TYPE
           , CASE
              WHEN B_S.ROW_WAIT_OBJ# <> -1 THEN
               DBMS_ROWID.ROWID_CREATE(1,
                                       OBJ.DATA_OBJECT_ID,
                                       B_S.ROW_WAIT_FILE#,
                                       B_S.ROW_WAIT_BLOCK#,
                                       B_S.ROW_WAIT_ROW#)
              ELSE
               '-1'
             END BLOCKED_ROWID --被阻塞数据的ROWID
           -- ,DECODE(OBJ.OBJECT_TYPE,
           --        'TABLE',
           --        'SELECT * FROM ' || OBJ.OWNER || '.' || OBJ.OBJECT_NAME ||
           --        ' WHERE ROWID=''' ||
           --        DBMS_ROWID.ROWID_CREATE(1,
           --                                OBJ.DATA_OBJECT_ID,
           --                                B_S.ROW_WAIT_FILE#,
           --                                B_S.ROW_WAIT_BLOCK#,
           --                                B_S.ROW_WAIT_ROW#) || '''',
           --        NULL) BLOCKED_DATA_QUERYSQL
      FROM GV$SESSION A_S,
           GV$SESSION B_S,
           DBA_OBJECTS OBJ,
           V$SQL VSQL,
           (SELECT SB.SID AS TMPSID,
                   SB.SERIAL# AS TMPSERIAL# ,
                   SB.USERNAME,
                   'BLOCKED',
                   SW.SID,
                   SW.SERIAL#,
                   SW.USERNAME,
                   SWT.SECONDS_IN_WAIT
              FROM V$LOCK         LB,
                   V$LOCK         LW,
                   V$SESSION      SB,
                   V$SESSION      SW,
                   V$SQL          QB,
                   V$SQL          QW,
                   V$SESSION_WAIT SWT
             WHERE LB.SID = SB.SID
               AND LW.SID = SW.SID
               AND LB.SID = SWT.SID
               AND SB.PREV_SQL_ADDR = QB.ADDRESS
               AND SW.SQL_ADDRESS = QW.ADDRESS
               AND LB.ID1 = LW.ID1
               AND SB.LOCKWAIT IS NULL
               AND SW.LOCKWAIT IS NOT NULL
               AND LB.BLOCK = 1) TMP
     WHERE B_S.BLOCKING_INSTANCE IS NOT NULL
       AND B_S.BLOCKING_SESSION IS NOT NULL
       AND A_S.INST_ID = B_S.BLOCKING_INSTANCE
       AND A_S.SID = B_S.BLOCKING_SESSION
       AND B_S.ROW_WAIT_OBJ# = OBJ.OBJECT_ID(+)
       AND VSQL.SQL_ID = B_S.SQL_ID
       AND TMP.TMPSID = A_S.SID
       AND TMP.TMPSERIAL# = A_S.SERIAL#
     ORDER BY A_S.INST_ID, A_S.SID
    """
    print "数据库对象锁信息如下"
    return QueryResult(sql,self.cur,self.debug)

  def log(self):
     """Print Database Log InfoMaion"""
     sql = """
           SELECT
        l.thread#,
        l.group#,
        l.sequence#,
        l.bytes/1024/1024 bytes,
        l.ARCHIVED,
        l.STATUS,
        l.FIRST_TIME,
        l.NEXT_TIME,
        lf.member logfile_member
      from
        v$log l,
        v$logfile lf
      where
        l.group# = lf.group#
      order by
        l.thread#,l.group#
     """
     return QueryResult(sql, self.cur)

  def dgstatus(self):
    """Print DataGuard Status"""
    sql = """
    SELECT PROCESS, STATUS, THREAD#, SEQUENCE#, BLOCK#, BLOCKS FROM V$MANAGED_STANDBY
    """
    return QueryResult(sql, self.cur)

  def dbrole(self):
    """Print DataGuard Role"""
    sql = """
    select name,database_role,db_unique_name,open_mode,protection_mode,protection_level,switchover_status,supplemental_log_data_pk,supplemental_log_data_ui from v$database
    """
    return QueryResult(sql, self.cur)

  def pmdefault(self):
    """Print DataGuard Role"""
    sql = """
    select name,VALUE from v$parameter where ISDEFAULT='FALSE'
    """
    return QueryResult(sql, self.cur)

  def alterseq(self):
    """Print DataGuard Role"""
    sql = """
    declare
      v_sql varchar2(200);
      v_result Varchar2(50);
    begin
       for rec in (select SEQUENCE_OWNER,SEQUENCE_NAME,MIN_VALUE,MAX_VALUE,INCREMENT_BY,LAST_NUMBER
        from dba_sequences where SEQUENCE_OWNER not IN
      ('DBSNMP','DMSYS','ORACLE_OCM', 'OLAPSYS', 'WMSYS', 'XDB', 'SCOTT', 'OUTLN',
       'PERFSTAT', 'MGMT_VIEW', 'SYS', 'SYSTEM','TSMSYS', 'DIP', 'SYSMAN','ANONYMOUS',
      'MONI', 'BACKUP', 'ORASYSSI','ORDDATA','SI_INFORMTN_SCHEMA','ORDPLUGINS','XS$NULL',
      'TIVOLI','EXFSYS','APPQOSSYS','CTXSYS','MDSYS','ORDSYS','APEX_030200','OWBSYS','SQLTXADMIN',
      'SPA','SPATIAL_CSW_ADMIN_USR','OWBSYS_AUDIT','APEX_PUBLIC_USER','MDDATA','FLOWS_FILES','SPATIAL_WFS_ADMIN_USR')
      and SEQUENCE_OWNER='TRAVEL')
      loop
          v_sql:='alter SEQUENCE ' || rec.SEQUENCE_OWNER || '.' || rec.SEQUENCE_NAME || ' Increment By 200000  MAXVALUE 99999999999999999999999999 ';
          -- dbms_output.put_line(v_sql);
          execute immediate v_sql;
          v_sql:='select ' || rec.SEQUENCE_OWNER || '.' || rec.SEQUENCE_NAME || '.nextval from dual '  ;
          -- dbms_output.put_line(v_sql);
          execute immediate v_sql into v_result;
          -- dbms_output.put_line(v_result);
          v_sql:='alter SEQUENCE ' || rec.SEQUENCE_OWNER || '.' || rec.SEQUENCE_NAME || ' Increment By '||rec.INCREMENT_BY;
          -- dbms_output.put_line(v_sql);
          execute immediate v_sql;
       end loop;
    end;
    """
    return QueryResult(sql, self.cur)

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
    parser.add_argument('-t', '--type',default='sqlnite', help="Database Type sqlnite,oracle,mysql", required=False)
    parser.add_argument('-v', '--version', action='version', version=' %(prog)s '+ __version__ + ' by ' + __author__)
    parser.add_argument("-D", "--debug", action="store_true", dest="debug", default=False,
              help="Debug mode ,print more info")
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
    parser_l.add_argument('-s', '--servicename',default='all', help="Database Service Name", required=False)

    # for automatic add tablespace datafile
    parser_add = subparsers.add_parser('addfile', help='automatic add tablespace datafile',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_add.add_argument('-tw', '--tbswar',    default=80,     help="Tablespace Waring Pct "   , required=False)
    parser_add.add_argument('-dn', '--dbfnum',    default=1,      help="add Datafile number"      , required=False)
    parser_add.add_argument('-as', '--asmfsize',  default=61440,  help="asm free size(Mb)"        , required=False)
    parser_add.add_argument('-ds', '--dbfsize',   default=20480,  help="Database Port "           , required=False)
    parser_add.add_argument('-tn', '--tbsname',   default=None,   help="Database Tablespace Name ", required=False)
    parser_add.add_argument('-test', '--test',    action="store_true", default=False, help="Database Tablespace Name ", required=False)

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
    sql = '''
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
      sql = "select DB_USER dbusers,DB_PASS dbuserspasswd,DB_IPADDR,DB_PORT,DB_SERVICENAME,DB_GROUP from ORA_DB_INFO "
      sql +="where DB_STATUS = 1 AND DB_IPADDR like '%" + dbip + "%'"
      if self.args.group != 'all':
        sql +="AND DB_GROUP = '" + self.args.group + "'"
      if self.args.servicename != 'all':
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
      if self.args.type == "sqlnite":
        self.oradb  = sqlite3.connect("orastats.db")
        self.oracur = self.oradb.cursor()
      elif self.args.type == "oracle":
        self.oradb = self.db_connect(self.args.username, self.args.passwd, self.args.ipaddress, self.args.port,
                       self.args.database)
        self.oracur = self.oradb.cursor()
      else:
        print "not support database"
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

  def __call__(self):
    try:
      self.db_conninit()
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
          print ('Group : [\033[1;31;40m%-10s\033[0m] Database : [\033[1;31;40m%-15s\033[0m] Port : [\033[1;31;40m%-6s\033[0m] Service_Name : [\033[1;31;40m%-10s\033[0m]' % (row[5],row[2],row[3],row[4]))
      else:
        for row in self.db_list():
          print ('Group : [\033[1;31;40m%-10s\033[0m] Database : [\033[1;31;40m%-15s\033[0m] Port : [\033[1;31;40m%-6s\033[0m] Service_Name : [\033[1;31;40m%-10s\033[0m]' % (row[5],row[2],row[3],row[4]))
          if self.db_conn(row):
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
            try:
              Res = fn(*fn_args, **fn_kwargs)
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



