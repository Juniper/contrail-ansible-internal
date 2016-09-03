# Contrail-ansible
Ansible code to provision contrail system

Currently we follow an all-in-one repo for all playbooks and contrail specific roles.

Also we are taking a different approach than standard single tiny reusable roles approach, to have a hierarchical
roles and subroles approach to have a composable hierarchical role[s], so that I can have all code in same repo but
keeping logical separation with subroles and tags to make the code composable.

If things go unmanageable in future, we could go towards splitting roles.
