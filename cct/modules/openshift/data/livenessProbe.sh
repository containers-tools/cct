#!/bin/sh

if [ true = "${DEBUG}" ] ; then
    # short circuit liveness check in dev mode
    exit 0
fi

OUTPUT=/tmp/liveness-output
ERROR=/tmp/liveness-error
LOG=/tmp/liveness-log

# liveness failure before management interface is up will cause the probe to fail
COUNT=30
SLEEP=1
DEBUG_SCRIPT=false

EVALUATE_SCRIPT=`cat <<EOF
import json
import os
import sys

with open("${OUTPUT}") as results_data:
  results = json.load(results_data)
  if results["outcome"] == "success":
    server_state = results["result"]["step-1"]
    deployment_states = results["result"]["step-2"]
    if server_state["result"] == "running":
      for deployment in deployment_states["result"]:
        if deployment["result"]["enabled"] and deployment["result"]["status"] != "OK":
          sys.stderr.write("detected failed deployment: " + deployment["result"]["runtime-name"] +"\n")
          sys.exit(3)
EOF`

if [ $# -gt 0 ] ; then
    COUNT=$1
fi

if [ $# -gt 1 ] ; then
    SLEEP=$2
fi

if [ $# -gt 2 ] ; then
    DEBUG_SCRIPT=$3
fi

if [ true = "${DEBUG_SCRIPT}" ] ; then
    echo "Count: ${COUNT}, sleep: ${SLEEP}" > ${LOG}
fi

while : ; do
    curl -s --digest -L http://localhost:9990/management --header "Content-Type: application/json" -d '{"operation":"composite","steps":[{"operation":"read-attribute","name":"server-state"},{"operation":"read-resource","address":["deployment","*"],"include-runtime":"true"}],"json.pretty":1}' > ${OUTPUT} 2>${ERROR}

    CONNECT_RESULT=$?
    python -c "$EVALUATE_SCRIPT" 2>>${ERROR}
    GREP_RESULT=$?
    if [ true = "${DEBUG_SCRIPT}" ] ; then
        (
            echo "$(date) Connect: ${CONNECT_RESULT}, Grep: ${GREP_RESULT}"
            echo "========================= OUTPUT ========================="
            cat ${OUTPUT}
            echo "========================= ERROR =========================="
            cat ${ERROR}
            echo "=========================================================="
        ) >> ${LOG}
    fi

    rm -f ${OUTPUT} ${ERROR}

    if [ ${GREP_RESULT} -eq 0 ] ; then
        exit 0;
    fi

    COUNT=$(expr $COUNT - 1)
    if [ $COUNT -eq 0 ] ; then
        exit 1;
    fi
    sleep ${SLEEP}
done
