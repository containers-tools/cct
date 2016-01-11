function configure_json_logging() {
  sed -i "s|^.*\.module=org\.jboss\.logmanager\.ext$||" $LOGGING_FILE
}
