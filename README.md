[TOC]

# 安装依赖环境
swith user to zabbix or oramon(useradd oramon)
```shell
mkdir media
mkdir python
```
依赖环境统一安装在 用户家目录python下


## 安装zlib
```shell
yum install zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel
```




## 安装Python
```shell
gzip -dc Python-2.7.10.tgz|tar -xf -
cd Python-2.7.10
./configure --prefix=$HOME/python --with-zlib=$HOME/python
make;make install
cd ..
rm -rf Python-2*
```

下载地址https://pypi.python.org/

## 安装setuptools
```shell
export PATH=$HOME/bin:$HOME/python/bin:$PATH
echo "export PATH=\$HOME/bin:\$HOME/python/bin:\$PATH" >> ~/.bash_profile
tar -zxf setuptools-18.1.tar.gz
cd setuptools-18.1
python setup.py install
cd ..
rm -rf setuptools-18*
```

## 安装pip/six/configparser-3.5.0.tar.gz
```shell

tar -zxf pip-8.1.1.tar.gz
cd pip-8.1.1
python setup.py install
cd ..
rm -rf pip-8.1*
```
如果已安装cx_Oracle请忽略

## 验证方式
```python
python
Python 2.7.10 (default, Jul 30 2016, 18:31:42)
[GCC 4.2.1 Compatible Apple LLVM 8.0.0 (clang-800.0.34)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import cx_Oracle
>>>
如果没有报错就是已安装
```

<a name="安装简版oracle客户端"></a>
## 安装oracle客户端
可以安装完整版客户端也可以安装简版客户端 
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
## 安装cx_Oracle
安装cx_Oracle的用户必须配置Oracle的环境变量
```shell
gzip -dc cx_Oracle-5.2.tar.gz|tar -xf -
cd cx_Oracle-5.2/
python setup.py install
cd ..
rm -rf cx_Oracle*
```


# 初始化数据库
修改脚本中连接数据库的信息,
```python

#初始化数据库
./orastat.py init 

InIt database Successfully


```
# 添加数据库
```python
./orastat.py add -h
usage: orastat add [-h] -ni NEWIP [-nu NEWUSERNAME] [-nP NEWPASSWD] -np
                    NEWPORT -ns NEWSERVICENAME -ng NEWGROUP

optional arguments:
  -h, --help            show this help message and exit
  -ni NEWIP, --newip NEWIP
                        Database Ip Address (default: None)
  -nu NEWUSERNAME, --newusername NEWUSERNAME
                        Database Username with sys views grant (default: None)
  -nP NEWPASSWD, --newpasswd NEWPASSWD
                        Database Username Password (default: None)
  -np NEWPORT, --newport NEWPORT
                        Database Port (default: None)
  -ns NEWSERVICENAME, --newservicename NEWSERVICENAME
                        Database Service Name (default: None)
  -ng NEWGROUP, --newgroup NEWGROUP  --此数据库属于那个组
                        Database Group Name (default: None)
添加要查询的数据库信息
  -ng <组名> -ni <ip地址> -np <端口> -ns <服务名> -nu <用户名> -nP <密码>

demo
./orastat.py add -ng TRAVEL -ni 192.168.56.65 -np 1521 -ns orcl -nu zabbix -nP zabbix
add database Successfully
./orastat.py add -ng TRAVEL -ni 192.168.56.65 -np 1521 -ns orastat1 -nu zabbix -nP zabbix
add database Successfully
# -nu -nP 可不设置,默认为NULL,如果不输入则判断为zbbix
```

# 查看数据库
```python
./orastat.py list -h
usage: orastat list [-h] [-n NODE]

optional arguments:
  -h, --help            show this help message and exit
  -n NODE, --node NODE  Database Ip, all (default: all)
  -g GROUP, --group GROUP
                        Database Group Name (default: all)
  -s SERVICENAME, --servicename SERVICENAME
                        Database Service Name (default: all)
# 查看所有
./orastat.py list
Group : [B         ] Database : [1.1.1.1        ] Port : [1521  ] Service_Name : [xxxx      ]
Group : [B         ] Database : [111.111.111.111] Port : [1521  ] Service_Name : [xxxx      ]
Group : [ALL       ] Database : [192.168.56.65  ] Port : [1521  ] Service_Name : [orcl      ]
# 查看某个组
./orastat.py list -g M
Group : [M         ] Database : [xxx.xxx.xxx.xxx  ] Port : [1521  ] Service_Name : [xxxx1]
Group : [M         ] Database : [xxx.xxx.xxx.xxx  ] Port : [1521  ] Service_Name : [xxxx2]
Group : [M         ] Database : [xxx.xxx.xxx.xxx  ] Port : [1521  ] Service_Name : [xxxx3]
Group : [M         ] Database : [xxx.xxx.xxx.xxx  ] Port : [1521  ] Service_Name : [xxxx4]
# 查看某个节点
./orastat.py list -n 192.168.56.65
Group : [ALL       ] Database : [192.168.56.65] Port : [1521] Service_Name : [orcl]
Group : [ALL       ] Database : [192.168.56.65] Port : [1521] Service_Name : [test1]

```

# 查看参数
```python
usage: orastat [-h] [-U USERNAME] [-P PASSWD] [-i IPADDRESS] [-p PORT]
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



./orastat.py version
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
找到 class orastat(object)

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


./orastat.py -h
usage: orastat [-h] [-U USERNAME] [-P PASSWD] [-i IPADDRESS] [-p PORT]
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

./orastat.py lock
Database : [192.168.56.65] Port : [1521] Service_Name : [orcl] Information :
数据库对象锁信息如下
BLOCKINFO                                                    SCHEMANAME                STATUS   BLOCKED_SCHEMANAME        BLOCKED_OWNER             BLOCKED_OBJECT_NAME            BLOCKED_ROWID
------------------------------------------------------------ ------------------------- -------- ------------------------- ------------------------- ------------------------------ -------------
node 1 session 147,761 blocking node 1 session 143,291       TRAVEL                    INACTIVE TRAVEL                    TRAVEL                    T1                             AAAlYuAAEAAAKoLAAA

```
