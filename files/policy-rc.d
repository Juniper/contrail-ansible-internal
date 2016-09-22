#!/bin/bash
if [ "${1}" = "--quiet" ]; then
  name="$2"
else
  name="$1"
fi
sensitive_services_list=/etc/sensitive_services
grep -x "$name" "$sensitive_services_list" && exit 101
exit 0
