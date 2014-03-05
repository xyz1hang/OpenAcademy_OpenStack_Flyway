import MySQLdb
from oslo.config import cfg
import sys

def connect(host=None, user="root", passwd=None, db=None):
	db = MySQLdb.connect(host=host, 
                     	     user=user, 
                             passwd=passwd, 
                             db=db) 
	return db

def getCursor(db):
	return db.cursor()

def createDNS(db, cursor):
	createDNS = "CREATE TABLE IF NOT EXISTS dns ( id INT NOT NULL AUTO_INCREMENT, cloudname VARCHAR(32) NOT NULL, auth_url VARCHAR(128) NOT NULL, bypass_url VARCHAR(128), tenant_id VARCHAR(128), tenant_name VARCHAR(128) NOT NULL, username VARCHAR(128) NOT NULL, password VARCHAR(512) NOT NULL, endpoint VARCHAR(256) NOT NULL, UNIQUE(cloudname), PRIMARY KEY(id))"
	
	try:
		cursor.execute(createDNS)
		db.commit()
	except:
		db.rollback()
		
def insertTargetDNS(db, cursor):
	insertDNS = "INSERT INTO dns VALUES ('','" + cfg.CONF.TARGET.os_cloudname + "','" + cfg.CONF.TARGET.os_auth_url + "','" + cfg.CONF.TARGET.os_bypass_url + "','" + cfg.CONF.TARGET.os_tenant_id + "','" + cfg.CONF.TARGET.os_tenant_name + "','" + cfg.CONF.TARGET.os_username + "','" + cfg.CONF.TARGET.os_password + "','" + cfg.CONF.TARGET.os_endpoint + "')"                           
	try:
		cursor.execute(insertDNS)
		db.commit()
	except:
		db.rollback()
		
def insertSourceDNS(db, cursor):
	insertDNS = "INSERT INTO dns VALUES ('','" + cfg.CONF.SOURCE.os_cloudname + "','" + cfg.CONF.SOURCE.os_auth_url + "','" + cfg.CONF.SOURCE.os_bypass_url + "','" + cfg.CONF.SOURCE.os_tenant_id + "','" + cfg.CONF.SOURCE.os_tenant_name + "','" + cfg.CONF.SOURCE.os_username + "','" + cfg.CONF.SOURCE.os_password + "','" + cfg.CONF.SOURCE.os_endpoint + "')"                           
	try:
		cursor.execute(insertDNS)
		db.commit()
	except:
		db.rollback()
		
def readDNS(db, cursor, name):
	count = "SELECT COUNT(*) FROM dns WHERE cloudname = '" + name + "'"
	cursor.execute(count)
	num = cursor.fetchone()
	
	if num[0] < 1:
		return None
	else:
		readDNS = "SELECT * FROM dns WHERE cloudname = '" + name + "'"
		cursor.execute(readDNS)
		row  = cursor.fetchone()
		data = {'auth_url': row[2],
			'by_pass_url': row[3],
			'tenant_id': row[4],
			'tenant_name': row[5],
			'username': row[6],
			'password': row[7],
			'endpoint': row[8],
			'cloudname':row[1]}
		return data
	
def configContent(srcConfig, dstConfig):
	config = '[SOURCE]\n'
	config += 'os_auth_url = ' + srcConfig['auth_url'] + '\n'
	config += 'os_bypass_url = ' + srcConfig['by_pass_url'] + '\n'
	config += 'os_tenant_id = ' + srcConfig['tenant_id'] + '\n'
	config += 'os_tenant_name = ' + srcConfig['tenant_name'] + '\n'
	config += 'os_username = ' + srcConfig['username'] + '\n'
	config += 'os_password = ' + srcConfig['password'] + '\n'
	config += 'os_endpoint = ' + srcConfig['endpoint'] + '\n'
	config += 'os_cloudname = ' + srcConfig['cloudname'] + '\n'
	config += '\n\n'
	config += '[TARGET]\n'
	config += 'os_auth_url = ' + dstConfig['auth_url'] + '\n'
	config += 'os_bypass_url = ' + dstConfig['by_pass_url'] + '\n'
	config += 'os_tenant_id = ' + dstConfig['tenant_id'] + '\n'
	config += 'os_tenant_name = ' + dstConfig['tenant_name'] + '\n'
	config += 'os_username = ' + dstConfig['username'] + '\n'
	config += 'os_password = ' + dstConfig['password'] + '\n'
	config += 'os_endpoint = ' + dstConfig['endpoint'] + '\n'
	config += 'os_cloudname = ' + dstConfig['cloudname'] + '\n'
	config += '\n\n'
	config += '[DEFAULT]\n'
	config += '# loglevels can be CRITICAL, ERROR, WARNING, INFO, DEBUG\n'
	config += 'loglevel = DEBUG\n'
	config += 'logfile = /tmp/flyway.log\n'
	config += 'logformat = %(asctime)s %(levelname)s [%(name)s] %(message)s\n'
	return config
	
def writeToFile(filepath, content):
	with open(filepath,'w') as file:
		file.write(content)
		
		
