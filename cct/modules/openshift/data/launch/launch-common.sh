#!/bin/sh
# common subroutines used in various places of the launch scripts

# Finds the environment variable  and returns its value if found.
# Otherwise returns the default value if provided.
#
# Arguments:
# $1 env variable name to check
# $2 default value if environment variable was not set
function find_env() {
#  echo "${1-$2}"
  var=`printenv "$1"`

  # If environment variable exists
  if [ -n "$var" ]; then
    echo $var
  else
    echo $2
  fi
}
