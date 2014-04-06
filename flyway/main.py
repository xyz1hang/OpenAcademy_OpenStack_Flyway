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
from utils import db_handler


def main():
    # the configuration will be read into the cfg.CONF global data structure
    args = ['--config-file']
    if len(sys.argv) > 2 and sys.argv[1] == '--config-file':
        args.append(sys.argv[2])
        config.parse(args)
        config.setup_logging()
        if not cfg.CONF.config_file:
            sys.exit(
                "ERROR: Unable to find configuration file via the "
                "'--config-file' option!")

        # store cloud "environment" (connection details) into database
        try:
            db_handler.update_environment()
        except db_handler.MySQLdb.Error, e:
            print 'MySQL Error\n' \
                  'Details: ' + str(e)

    elif len(sys.argv) > 4 and sys.argv[1] == '-src' and sys.argv[3] == '-dst':
        src_config = db_handler.read_environment(sys.argv[2])
        if not src_config:
            print "Cloud " + sys.argv[2] + \
                  ' does not exist in the database, ' \
                  'please configure flyway.conf!'

        dst_config = db_handler.read_environment(sys.argv[4])
        if not dst_config:
            sys.exit("Cloud " + sys.argv[4] +
                     ' does not exist in the database, '
                     'please configure flyway.conf!')

        # TODO: We've used database here and yet
        # TODO: need to write to file again ?
        # TODO: Is there a way to load those connection details read from
        # TODO: database directly into the CONF (or use them directly)?
        db_handler.write_to_file('etc/flyway.conf',
                                 db_handler.config_content(src_config,
                                                           dst_config))
        args.append('./etc/flyway.conf')
        config.parse(args)
        config.setup_logging()

    try:
        flow.execute()
    except RuntimeError, e:
        sys.exit("ERROR: %s" % e)


if __name__ == "__main__":
    main()
