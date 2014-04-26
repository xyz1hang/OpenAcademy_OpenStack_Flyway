import sys

from flow import flow
from common import config
from utils.db_handlers.environment_config import *


def main():
    # the configuration will be read into the cfg.CONF global data structure
    args = ['--config-file']
    if len(sys.argv) > 2 and sys.argv[1] == '--config-file':
        args.append(sys.argv[2])
        config.parse(args)
        config.setup_logging()
        if not cfg.CONF.config_file:
            sys.exit(
                "ERROR: Unable to find configuration " +
                "file via the '--config-file' option!")

        initialize_environment()

        # store cloud "environment" (connection details) into database
        update_environment()

    # else select a pre-stored source-destination clouds pair to
    # begin the migration between them
    elif len(sys.argv) > 4 and sys.argv[1] == '-src' and sys.argv[3] == '-dst':
        src_config = read_environment(sys.argv[2])
        print src_config
        if not src_config:
            print "Cloud " + sys.argv[2] + \
                  ' does not exist in the database, ' \
                  'please configure flyway.conf!'

        dst_config = read_environment(sys.argv[4])
        if not dst_config:
            sys.exit("Cloud " + sys.argv[4] +
                     ' does not exist in the database, '
                     'please configure flyway.conf!')

        #TODO: Is there a solution to load config data from database
        #TODO: directly into config object here ?
        write_to_file('etc/flyway.conf', config_content(src_config, dst_config))
        args.append('./etc/flyway.conf')
        config.parse(args)
        config.setup_logging()

    try:
        flow.execute()
    except RuntimeError, e:
        sys.exit("ERROR: %s" % e)


if __name__ == "__main__":
    main()