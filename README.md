# Contrail-ansible
Ansible code to provision contrail system

Currently we follow an all-in-one repo for all playbooks and contrail specific roles.

Also we are taking a different approach than standard single tiny reusable roles approach, to have a hierarchical
roles and subroles approach to have a composable hierarchical role[s], so that I can have all code in same repo but
keeping logical separation with subroles and tags to make the code composable.

If things go unmanageable in future, we could go towards splitting roles.

## Vagrant based development environments
* Install vagrant and virtualbox (https://www.vagrantup.com/docs/installation/)
* Define your test layout
  * System use an environment variable called "layout" to read the layout from. The default for this is "vagrant\_nodes"
  *  System will look for a file "$layout".yaml in current file i.e by default, it will look for a file vagrant\_nodes.yaml
  * You can define node type, number of nodes, node size etc in that file, please refer vagrant\_nodes.yaml file included.
* Now you may manage your test environment using vagrant commands
  * vagrant up - start all VMs in your layout
  * vagrant up <node name> - start only one of the node named in the command
  * vagrant destroy - destroy all/named vms
  * vagrant --help - for the help
* Vagrant up should start the system and configure it, install docker, and start docker containers - so it should give you a
  working system in single command

I run below command to start single node all-in-one contrail system without openstack

```
# I use ansible_inventory to pass custom inventory file which should match the file name under playbooks/inventory directory
# By default it is svl_allinone_wo_os as of now

$ ansible_inventory=vagrant_registry_allinone vagrant up cc1
```

NOTE: Current code only tested with single node setup, there are little bit more work needed to support to have multi-node setup.
