function configure_administration() {
  if [ -n "${ADMIN_PASSWORD}" ]; then
        $JBOSS_HOME/bin/add-user.sh -u "$ADMIN_USERNAME" -p "$ADMIN_PASSWORD"
  fi
}
