Flyway
======

Forklift Resources from One Cloud to Another which can be executed in Ubuntu, Debian operating systems

    1 - Users and their respective roles in projects
    2 - Projects with related metadata
    3 - Project quotas
    4 - Private Keys
    5 - Images/Snapshots and their metadata.
    6 - VMs
    7 - Flavor mappings
    
This project includes two interfaces:

    1 - Command Line Interface
    2 - Graphical User Interface

CLI
===

1 - Configuration
=================

Configuration has to be made before using Flyway CLI. Please execute the below command for implementing configurations in the 'preconfiguration' directory of project:
    
    1 - sudo sh pythonutils.sh
    2 - sudo pip install -r openstack_requirements.txt


2 - Usage
=========

Execute the command below in the 'flyway' directory of project:
    
    python flyway.py -src sourcecloudname -dst targetcloudname

which retrieves the corresponding cloud infos from DNS database.
    
If sourcecloudname or targetcloudname does not exist in the DNS database, please configure new clouds in the flyway.conf file and execute the command below, the new clouds will be automatically stored in DNS database for future migration.
    
    python flyway.py --config-file ./etc/flyway.conf

Note: 
    If vagrant is used as the host of openstack, please configure 'os_bypass_url' in the flyway.conf file and add 'bypass_url' parameter to each nova instantiation
    
    
GUI
===

1 - Configuration
=================
Configuration has to be made before using Flyway GUI. Please execute the below command for implementing configurations in the 'GUI' directory of project:
    
    sudo sh configuration.sh

2 - Usage
=========

Execute command:
    
    python gui.py

