# Contrail-ansible-internal
Ansible code to provision contrail services

This ansible code help to provision contrail services running within the container.
This code is supposed to run by contrailctl and not to run by user. contrailctl
read its configuration file, pass the configurations to ansible as variables and
run this ansible code with appropriate high level playbook found directly under
playbooks/ directory.

Any changes that need to go to any internal service configuration file, any internal
service management and other things related to internal services within the container
should go here.
