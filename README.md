# Contrail-ansible
Ansible code to provision contrail system

Currently we follow an all-in-one repo for all playbooks and contrail specific roles.

Also we are taking a different approach than standard single tiny reusable roles approach, to have a hierarchical
roles and subroles approach to have a composable hierarchical role[s], so that I can have all code in same repo but
keeping logical separation with subroles and tags to make the code composable.

If things go unmanageable in future, we could go towards splitting roles.

NOTE: Current code only tested with single node setup, there are little bit more work needed to support to have multi-node setup.

## Running contrail containers using contrail-ansible
Part of the code in contrail-ansible is supposed to create a native ansible interface to setup base system and orchestrate
/provision contrail containers on top of them, if people don't want to use more featured orchestration/provisioning
systems like server manager. This functionality is supposed to provide a basic ansible native interface and will only
handle operating system setup on base nodes and run/orchestrate containers on top of them. This section brief about the
process to run contrail containers using contrail-ansible.

1. Install ansible version >= 2.0 - please refer http://docs.ansible.com/ansible/intro_installation.html
2. Get contrail-ansible code - you may get from github repository or any other packaged versions.
3. Install any dependent roles - this step will eventually go away once we moved all dependent roles inside contrail-ansible

    ```
    $ cd contrail-ansible
    $ ansible-galaxy install -r requirements.yml
    ```

4. Create an inventory file - please refer the [sample inventory file provided](playbooks/inventory/examples/single-controller-multi-compute-svl)
   to create one for you. For a standard single controller, multi-compute setup, it would only need to add/change the IP
   addresses. You may also have to refer ansible code and variable defaults for more advanced configurations
5. Run ansible-playbook with base_host.yml pointing to your own inventory file

    ```
    $ cd playbooks
    $ ansible-playbook -i inventory/examples/single-controller-multi-compute-svl base_host.yml
    ```

Now contrail-controller node should have all contrail-controller specific containers running and all computes have agent
container running. 

Note that containers will take few minutes to come up completely, once they are up, you will be able to connect to webui
using static auth and will be able to see the system status and would be able to do various operations.

Note: 
* This code support only single controller node at this moment, but you can have multiple compute nodes.
* Currently no openstack setup is supported, only contrail components setup supported.
* Default configuration (without openstack) use webui static auth since there is no authentication service. So users
have to use static auth credentials to connect to webui.
