#!/usr/bin/env python
# coding: utf-8

from Column import QueryResult

def args(*args, **kwargs):
  def _decorator(func):
    func.__dict__.setdefault('args', []).insert(0, (args, kwargs))
    return func
  return _decorator


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

  def segsum(self):
    """Check Database Connect"""
    # print self.db_ip
    sql = """select sysdate , sum(bytes)/1024/1024 SEG_SIZE_MB from dba_segments"""
    return QueryResult(sql, self.cur)
