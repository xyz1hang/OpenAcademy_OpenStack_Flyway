Flyway
======

Forklift Resources from One Cloud to Another

    1 - Users and their respective roles in projects
    2 - Projects with related metadata
    3 - Project quotas
    4 - Private Keys
    5 - Images/Snapshots and their metadata.
    6 - VMs
    7 - Flavor mappings


Usage
=====

Execute the command below in the root directory of project:
    
    python flyway.py --config-file ./etc/flyway.conf

Note: 
    If vagrant is used as the host of openstack, please configure 'os_bypass_url' in the flyway.conf file and add 'bypass_url' parameter to each nova instantiation
