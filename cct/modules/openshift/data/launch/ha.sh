function configure_ha() {
  # Set HA args
  IP_ADDR=`hostname -i`
  JBOSS_HA_ARGS="-b ${IP_ADDR}"
  if [ -n "${NODE_NAME}" ]; then
      JBOSS_NODE_NAME="${NODE_NAME}"
  elif [ -n "${container_uuid}" ]; then
      JBOSS_NODE_NAME="${container_uuid}"
  elif [ -n "${HOSTNAME}" ]; then
      JBOSS_NODE_NAME="${HOSTNAME}"
  fi
  if [ -n "${JBOSS_NODE_NAME}" ]; then
      JBOSS_HA_ARGS="${JBOSS_HA_ARGS} -Djboss.node.name=${JBOSS_NODE_NAME}"
  fi

  if [ -z "${JGROUPS_CLUSTER_PASSWORD}" ]; then
      >&2 echo "====================WARNING: No password defined for JGroups cluster.  AUTH protocol will be disabled.  Please define JGROUPS_CLUSTER_PASSWORD."
      JGROUPS_AUTH="<!--WARNING: No password defined for JGroups cluster.  AUTH protocol has been disabled.  Please define JGROUPS_CLUSTER_PASSWORD. -->"
  else
    JGROUPS_AUTH="\n\
                <protocol type=\"AUTH\">\n\
                    <property name=\"auth_class\">org.jgroups.auth.MD5Token</property>\n\
                    <property name=\"token_hash\">SHA</property>\n\
                    <property name=\"auth_value\">$JGROUPS_CLUSTER_PASSWORD</property>\n\
                </protocol>\n"
  fi

  sed -i "s|<!-- ##JGROUPS_AUTH## -->|${JGROUPS_AUTH}|g" $CONFIG_FILE

}

function configure_jgroups_encryption() {
  jgroups_encrypt=""

  if [ -n "${JGROUPS_ENCRYPT_SECRET}" ]; then
    jgroups_encrypt="\
        <protocol type=\"ENCRYPT\">\
          <property name=\"key_store_name\">${JGROUPS_ENCRYPT_KEYSTORE_DIR}/${JGROUPS_ENCRYPT_KEYSTORE}</property>\
          <property name=\"store_password\">${JGROUPS_ENCRYPT_PASSWORD}</property>\
          <property name=\"alias\">${JGROUPS_ENCRYPT_NAME}</property>\
        </protocol>"
  fi

  sed -i "s|<!-- ##JGROUPS_ENCRYPT## -->|$jgroups_encrypt|g" "$CONFIG_FILE"
}
