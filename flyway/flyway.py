# -*- coding: utf-8 -*-

#    Copyright (C) 2012 eBay, Inc. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import sys

from oslo.config import cfg

from common import config
from flow import flow
from dns import * 

DNScredentials = {'host': '172.16.45.169',
		  'user': 'root',
		  'passwd': 'openstack',
	          'db': 'keystone'}

def main():
    # the configuration will be read into the cfg.CONF global data structure
    args = ['--config-file']
    if len(sys.argv) > 2 and sys.argv[1] == '--config-file':
        args.append(sys.argv[2])
    	config.parse(args)
    	config.setup_logging()
	print 'hahhahahahahah:',cfg.CONF.config_file
	if not cfg.CONF.config_file:
		sys.exit("ERROR: Unable to find configuration file via the "
		         "'--config-file' option!")
	db = connect(**DNScredentials)
	cursor = getCursor(db)
	createDNS(db, cursor)
	insertTargetDNS(db, cursor)
	insertSourceDNS(db, cursor)
	db.close()	
    elif len(sys.argv) > 4 and sys.argv[1] == '--src' and sys.argv[3] == '--dst':
	db = connect(**DNScredentials)
	cursor = getCursor(db)
	srcConfig = readDNS(db, cursor, sys.argv[2])
	if not srcConfig:
		print "Cloud " + sys.argv[2] + ' does not exist in the database, please configure flyway.conf!'
	
	dstConfig = readDNS(db, cursor, sys.argv[4])
	if not dstConfig:
		sys.exit("Cloud " + sys.argv[4] + ' does not exist in the database, please configure flyway.conf!')
	
	writeToFile('etc/flyway.conf', configContent(srcConfig, dstConfig))
	args.append('./etc/flyway.conf')
	config.parse(args)
    	config.setup_logging()
	db.close()
    
    try:
        flow.execute()
    except RuntimeError, e:
        sys.exit("ERROR: %s" % e)
    
if __name__ == "__main__":
    main()
