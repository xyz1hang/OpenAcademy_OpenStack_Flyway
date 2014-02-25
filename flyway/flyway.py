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


def main():
    # the configuration will be read into the cfg.CONF global data structure
    args = ['--config-file']
    if len(sys.argv) > 2:
        args.append(sys.argv[2])
    config.parse(args)
    config.setup_logging()
    if not cfg.CONF.config_file:
        sys.exit("ERROR: Unable to find configuration file via the "
                 "'--config-file' option!")

    try:
        flow.execute()
    except RuntimeError, e:
        sys.exit("ERROR: %s" % e)


if __name__ == "__main__":
    main()
