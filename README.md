[TOC]

<a name="安装依赖环境"></a>
#.安装依赖环境

<a name="安装简版oracle客户端"></a>
##.安装简版oracle客户端
Oracle Instant Client download Link [oracle](http://www.oracle.com/technetwork/database/features/instant-client/index-097480.html)
```shell
unzip instantclient-basic-linux.x64-11.2.0.4.0.zip
unzip instantclient-sdk-linux.x64-11.2.0.4.0.zip
unzip instantclient-sqlplus-linux.x64-11.2.0.4.0.zip
cd instantclient_11_2
ln -sf libclntsh.so.11.1 libclntsh.so
cd ..
mv instantclient_11_2 ../python/
rm -rf instantclient*.zip
export ORACLE_HOME=$HOME/python/instantclient_11_2
export LD_LIBRARY_PATH=$ORACLE_HOME

echo "export ORACLE_HOME=\$HOME/python/instantclient_11_2" >> ~/.bash_profile
echo "export LD_LIBRARY_PATH=\$ORACLE_HOME" >> ~/.bash_profile
echo "export PATH=\$PATH:\$ORACLE_HOME" >> ~/.bash_profile
```
<a name="安装cx_oracle"></a>
##.安装cx_Oracle
```shell
gzip -dc cx_Oracle-5.2.tar.gz|tar -xf -
cd cx_Oracle-5.2/
python setup.py install
cd ..
rm -rf cx_Oracle*
```


# 初始化数据库
修改脚本中
```python
Class Main 里的 __init__
    parser.add_argument('-U', '--username', default='zabbix', help="Database Username with sys views grant",
              required=False)
    parser.add_argument('-P', '--passwd', default='zabbix', help="Database Username Password", required=False)
    parser.add_argument('-i', '--ipaddress', default='192.168.56.65', help="Database Ip Address", required=False)
    parser.add_argument('-p', '--port', default='1521', help="Database Port ", required=False)
    parser.add_argument('-d', '--database', default='orcl', help="Database Service Name", required=False)

以上几个默认参数值

#初始化数据库
./orastats.py init

InIt database Successfully

```
# 添加数据库
```python
 ./orastats.py add -h
usage: orastats add [-h] -ni NEWIP [-nu NEWUSERNAME] [-nP NEWPASSWD] -np
                    NEWPORT -ns NEWSERVICENAME

optional arguments:
  -h, --help            show this help message and exit
  -ni NEWIP, --newip NEWIP
                        Database Ip Address
  -nu NEWUSERNAME, --newusername NEWUSERNAME
                        Database Username with sys views grant
  -nP NEWPASSWD, --newpasswd NEWPASSWD
                        Database Username Password
  -np NEWPORT, --newport NEWPORT
                        Database Port
  -ns NEWSERVICENAME, --newservicename NEWSERVICENAME
                        Database Service Name
./orastats.py add -ni 192.168.56.65 -np 1521 -ns orcl
add database Successfully
./orastats.py add -ni 192.168.56.65 -np 1521 -ns test1
add database Successfully
# -nu -nP 可不设置,默认为NULL,如果不输入则判断为zbbix
```

# 查看数据库
```python
./orastats.py list -h
usage: orastats list [-h] [-n NODE]

optional arguments:
  -h, --help            show this help message and exit
  -n NODE, --node NODE  Database Ip, all (default: all)

./orastats.py list
Database : [192.168.56.65] Port : [1521] Service_Name : [orcl]
Database : [192.168.56.65] Port : [1521] Service_Name : [test1]

./orastats.py list -n 192.168.56.65
Database : [192.168.56.65] Port : [1521] Service_Name : [orcl]
Database : [192.168.56.65] Port : [1521] Service_Name : [test1]
```

# 查看参数
```python
usage: orastats [-h] [-U USERNAME] [-P PASSWD] [-i IPADDRESS] [-p PORT]
                [-d DATABASE] [-n NODE] [-v] [-D]
                {checkdb,tbs,list,init,dbf,add,version,del,userlock,asm} ...

positional arguments:   -->这些参数是可用于查询数据库的
  {checkdb,tbs,list,init,dbf,add,version,del,userlock,asm}
    asm                 Print Database ASM Diskgroup usage
    checkdb             Check Database Connect
    dbf                 Print Database Datafile usage
    tbs                 Print Database tablespace usage
    userlock            Print Database User Lock Information
    version             Print Oracle version (Banner)
    add                 add Database Information
    del                 del database Information
    init                init Database and create table ora_db_info
    list                list Database

optional arguments:
  -h, --help            show this help message and exit
  -U USERNAME, --username USERNAME
                        Database Username with sys views grant (default:
                        zabbix)
  -P PASSWD, --passwd PASSWD
                        Database Username Password (default: zabbix)
  -i IPADDRESS, --ipaddress IPADDRESS
                        Database Ip Address (default: 192.168.56.65)
  -p PORT, --port PORT  Database Port (default: 1521)
  -d DATABASE, --database DATABASE
                        Database Service Name (default: orcl)
  -n NODE, --node NODE  Check Database Ip, all (default: all)
  -v, --version         show program's version number and exit
  -D, --debug           Debug mode ,print more info (default: False)



./orastats.py version
Database : [192.168.56.65] Port : [1521] Service_Name : [orcl] Information :
数据库版本信息如下
BANNER
--------------------------------
Oracle Database 11g Enterprise Edition Release 11.2.0.3.0 - 64bit Production
Database : [192.168.56.65] Port : [1521] Service_Name : [test1] Information :
数据库版本信息如下
BANNER
--------------------------------
Oracle Database 11g Enterprise Edition Release 11.2.0.3.0 - 64bit Production

```


# 增加查询函数

```python
找到 class OraStats(object)

增加一个类似如下的,(注意缩进)
  def lock(self):

    """Print Database Lock"""
    sql = """
         Select 'node ' || a_s.INST_ID || ' session ' || a_s.sid || ',' || a_s.SERIAL# ||
           ' blocking node ' || b_s.INST_ID || ' session ' || b_s.SID || ',' ||
           b_s.SERIAL# blockinfo,
           a_s.INST_ID,
           a_s.SID,
           a_S.SERIAL#,
           a_s.SCHEMANAME,
           a_s.MODULE,
           a_s.STATUS,
           tmp.SECONDS_IN_WAIT||'s' SECONDS_IN_WAIT,
           'block_info',
           b_s.INST_ID blocked_inst_id,
           b_s.SID blocked_sid,
           b_s.SCHEMANAME blocked_SCHEMANAME,
           b_s.EVENT blocked_event,
           b_s.MODULE blocked_module,
           b_s.STATUS blocked_status,
           b_s.SQL_ID blocked_sql_id,
           vsql.SQL_TEXT,
           obj.owner blocked_owner,
           obj.object_name blocked_object_name,
           obj.OBJECT_TYPE blocked_OBJECT_TYPE,
           case
             when b_s.ROW_WAIT_OBJ# <> -1 then
              dbms_rowid.rowid_create(1,
                                      obj.DATA_OBJECT_ID,
                                      b_s.ROW_WAIT_FILE#,
                                      b_s.ROW_WAIT_BLOCK#,
                                      b_s.ROW_WAIT_ROW#)
             else
              '-1'
           end blocked_rowid, --±»×èÈûÊý¾ÝµÄrowid
           decode(obj.object_type,
                  'TABLE',
                  'select * from ' || obj.owner || '.' || obj.object_name ||
                  ' where rowid=''' ||
                  dbms_rowid.rowid_create(1,
                                          obj.DATA_OBJECT_ID,
                                          b_s.ROW_WAIT_FILE#,
                                          b_s.ROW_WAIT_BLOCK#,
                                          b_s.ROW_WAIT_ROW#) || '''',
                  NULL) blocked_data_querysql
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
    Res=QueryResult(sql, self.cur)
    Res.show_rows()


./orastats.py -h
usage: orastats [-h] [-U USERNAME] [-P PASSWD] [-i IPADDRESS] [-p PORT]
                [-d DATABASE] [-n NODE] [-v] [-D]
                {checkdb,lock,tbs,list,init,dbf,add,version,del,userlock,asm}
                ...

positional arguments:
  {checkdb,lock,tbs,list,init,dbf,add,version,del,userlock,asm}
    asm                 Print Database ASM Diskgroup usage
    checkdb             Check Database Connect
    dbf                 Print Database Datafile usage
<<< lock                Print Database Lock ----->>>>
    tbs                 Print Database tablespace usage
    userlock            Print Database User Lock Information
    version             Print Oracle version (Banner)
    add                 add Database Information
    del                 del database Information
    init                init Database and create table ora_db_info
    list                list Database

./orastats.py lock
Database : [192.168.56.65] Port : [1521] Service_Name : [orcl] Information :
数据库对象锁信息如下
BLOCKINFO                                                    SCHEMANAME                STATUS   BLOCKED_SCHEMANAME        BLOCKED_OWNER             BLOCKED_OBJECT_NAME            BLOCKED_ROWID
------------------------------------------------------------ ------------------------- -------- ------------------------- ------------------------- ------------------------------ -------------
node 1 session 147,761 blocking node 1 session 143,291       TRAVEL                    INACTIVE TRAVEL                    TRAVEL                    T1                             AAAlYuAAEAAAKoLAAA

```
