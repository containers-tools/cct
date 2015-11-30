configure_security_domains() {
  domains="<!-- no additional security domains configured -->"
  if [ -n "$SECDOMAIN_NAME" ]; then
      if [ -n "$SECDOMAIN_PASSWORD_STACKING" ]; then
          stack="<module-option name=\"password-stacking\" value=\"useFirstPass\"/>"
      else
          stack=""
      fi
      domains="\
        <security-domain name=\"$SECDOMAIN_NAME\" cache-type=\"default\">\
            <authentication>\
                <login-module code=\"UsersRoles\" flag=\"required\">\
                    <module-option name=\"usersProperties\" value=\"$SECDOMAIN_USERS_PROPERTIES\"/>\
                    <module-option name=\"rolesProperties\" value=\"$SECDOMAIN_ROLES_PROPERTIES\"/>\
                    $stack\
                </login-module>\
            </authentication>\
        </security-domain>"
  fi
  sed -i "s|<!-- ##ADDITIONAL_SECURITY_DOMAINS## -->|$domains|" "$CONFIG_FILE"
}
