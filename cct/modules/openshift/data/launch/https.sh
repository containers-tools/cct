function configure_https() {
  https="<!-- No HTTPS configuration discovered -->"
  if [ -n "${HTTPS_NAME}" -a -n "${HTTPS_PASSWORD}" -a -n "${HTTPS_KEYSTORE_DIR}" -a -n "${HTTPS_KEYSTORE}" ] ; then
    https="<connector name=\"https\" protocol=\"HTTP/1.1\" socket-binding=\"https\" scheme=\"https\" secure=\"true\"> \
                <ssl name=\"${HTTPS_NAME}\" password=\"${HTTPS_PASSWORD}\" certificate-key-file=\"${HTTPS_KEYSTORE_DIR}/${HTTPS_KEYSTORE}\"/> \
            </connector>"
  elif [ -n "${HTTPS_NAME}" -o -n "${HTTPS_PASSWORD}" -o -n "${HTTPS_KEYSTORE_DIR}" -o -n "${HTTPS_KEYSTORE}" ] ; then
    echo "WARNING! Partial HTTPS configuration, the https connector WILL NOT be configured."
  fi
  sed -i "s|<!-- ##HTTPS## -->|${https}|" $CONFIG_FILE
}
