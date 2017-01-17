[![Build Status](https://travis-ci.org/JioCloud/puppet-rjil.svg?branch=master)](https://travis-ci.org/hkumarmk/ansible-role-cassandra)
# ansible-role-cassandra
An ansible role for best practice Cassandra configuration and management.

## Why did I start writing this role?

I tried to see a good cassandra ansible role which works for multiple Linux distros - ubuntu, redhat platforms.
But I see either it they are created based on a specific purpose, like assumed to be a part of a playbook which
deploy specific set of applications, or support specific Linux distros.

Then I see a playbook for cassandra from [rackerlabs](https://github.com/rackerlabs/ansible-cassandra), which I feel
a better deployment code and they tried to implement best practices. BUT it was tightly coupled with rackspace system
and was a complete playbook and not only a role, also this is only support ubuntu/debian.

So I decided to create a role and referred rackerlabs playbook while developing this role.
