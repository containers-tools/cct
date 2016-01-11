#!/bin/sh
# Openshift EAP launch script

CONFIG_FILE=$JBOSS_HOME/standalone/configuration/standalone-openshift.xml
LOGGING_FILE=$JBOSS_HOME/standalone/configuration/logging.properties

#For backward compatibility
ADMIN_USERNAME=${EAP_ADMIN_USERNAME-eapadmin}
ADMIN_PASSWORD=$EAP_ADMIN_PASSWORD
NODE_NAME=$EAP_NODE_NAME
HTTPS_NAME=$EAP_HTTPS_NAME
HTTPS_PASSWORD=$EAP_HTTPS_PASSWORD
HTTPS_KEYSTORE_DIR=$EAP_HTTPS_KEYSTORE_DIR
HTTPS_KEYSTORE=$EAP_HTTPS_KEYSTORE
SECDOMAIN_USERS_PROPERTIES=${EAP_SECDOMAIN_USERS_PROPERTIES-users.properties}
SECDOMAIN_ROLES_PROPERTIES=${EAP_SECDOMAIN_ROLES_PROPERTIES-roles.properties}
SECDOMAIN_NAME=$EAP_SECDOMAIN_NAME
SECDOMAIN_PASSWORD_STACKING=$EAP_SECDOMAIN_PASSWORD_STACKING

. $JBOSS_HOME/bin/launch/messaging.sh
inject_brokers
configure_hornetq

. $JBOSS_HOME/bin/launch/datasource.sh
inject_datasources

. $JBOSS_HOME/bin/launch/admin.sh
configure_administration

. $JBOSS_HOME/bin/launch/ha.sh
configure_ha
configure_jgroups_encryption

. $JBOSS_HOME/bin/launch/https.sh
configure_https

. $JBOSS_HOME/bin/launch/json_logging.sh
configure_json_logging

. $JBOSS_HOME/bin/launch/security-domains.sh
configure_security_domains

echo "Running $JBOSS_IMAGE_NAME image, version $JBOSS_IMAGE_VERSION-$JBOSS_IMAGE_RELEASE"

exec $JBOSS_HOME/bin/standalone.sh -c standalone-openshift.xml -bmanagement 127.0.0.1 $JBOSS_HA_ARGS ${JBOSS_MESSAGING_ARGS}
