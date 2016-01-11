. $JBOSS_HOME/bin/launch/launch-common.sh
. $JBOSS_HOME/bin/launch/tx-datasource.sh

# Arguments:
# $1 - service name
# $2 - datasource jndi name
# $3 - datasource username
# $4 - datasource password
# $5 - datasource host
# $6 - datasource port
# $7 - datasource databasename
# $8 - connection checker class
# $9 - exception sorter class
# $10 - driver
function generate_datasource() {

  case "${10}" in
    "mysql") ds="
                  <xa-datasource jndi-name=\"$2\" pool-name=\"$1\" use-java-context=\"true\" enabled=\"true\">
                      <xa-datasource-property name=\"ServerName\">$5</xa-datasource-property>
                      <xa-datasource-property name=\"Port\">$6</xa-datasource-property>
                      <xa-datasource-property name=\"DatabaseName\">$7</xa-datasource-property>
                      <driver>${10}</driver>"
      if [ -n "$tx_isolation" ]; then
        ds="$ds 
                      <transaction-isolation>$tx_isolation</transaction-isolation>"
      fi
      if [ -n "$min_pool_size" ] || [ -n "$max_pool_size" ]; then
        ds="$ds
                      <xa-pool>"
        if [ -n "$min_pool_size" ]; then
          ds="$ds
                          <min-pool-size>$min_pool_size</min-pool-size>"
        fi
        if [ -n "$max_pool_size" ]; then
          ds="$ds
                          <max-pool-size>$max_pool_size</max-pool-size>"
        fi
        ds="$ds
                      </xa-pool>"
      fi
      ds="$ds
                      <security>
                          <user-name>$3</user-name>
                          <password>$4</password>
                      </security>
                      <validation>
                          <validate-on-match>true</validate-on-match>
                          <valid-connection-checker class-name=\"$8\"></valid-connection-checker>
                          <exception-sorter class-name=\"$9\"></exception-sorter>
                      </validation>
                  </xa-datasource>"
      ;;
    "postgresql") ds="                <xa-datasource jndi-name=\"$2\" pool-name=\"$1\" use-java-context=\"true\" enabled=\"true\">
                    <xa-datasource-property name=\"ServerName\">$5</xa-datasource-property>
                    <xa-datasource-property name=\"PortNumber\">$6</xa-datasource-property>
                    <xa-datasource-property name=\"DatabaseName\">$7</xa-datasource-property>
                    <driver>${10}</driver>"
      if [ -n "$tx_isolation" ]; then
        ds="$ds 
                      <transaction-isolation>$tx_isolation</transaction-isolation>"
      fi
      if [ -n "$min_pool_size" ] || [ -n "$max_pool_size" ]; then
        ds="$ds
                      <xa-pool>"
        if [ -n "$min_pool_size" ]; then
          ds="$ds
                          <min-pool-size>$min_pool_size</min-pool-size>"
        fi
        if [ -n "$max_pool_size" ]; then
          ds="$ds
                          <max-pool-size>$max_pool_size</max-pool-size>"
        fi
        ds="$ds
                      </xa-pool>"
      fi
      ds="$ds
                    <security>
                        <user-name>$3</user-name>
                        <password>$4</password>
                    </security>
                    <validation>
                        <validate-on-match>true</validate-on-match>
                        <valid-connection-checker class-name=\"$8\"></valid-connection-checker>
                        <exception-sorter class-name=\"$9\"></exception-sorter>
                    </validation>
                </xa-datasource>"
      ;;
    *) ds="                <datasource jndi-name=\"java:jboss/datasources/ExampleDS\" pool-name=\"ExampleDS\" enabled=\"true\" use-java-context=\"true\">
                    <connection-url>jdbc:h2:mem:test;DB_CLOSE_DELAY=-1;DB_CLOSE_ON_EXIT=FALSE</connection-url>
                    <driver>h2</driver>
                    <security>
                        <user-name>sa</user-name>
                        <password>sa</password>
                    </security>
                </datasource>"
      ;;
  esac

  echo $ds | sed ':a;N;$!ba;s|\n|\\n|g'
}

# Finds the name of the database services and generates data sources
# based on this info
function inject_datasources() {
  # Find all databases in the $DB_SERVICE_PREFIX_MAPPING separated by ","
  IFS=',' read -a db_backends <<< $DB_SERVICE_PREFIX_MAPPING

  if [ "${#db_backends[@]}" -eq "0" ]; then
    datasources=$(generate_datasource)
  else
    for db_backend in ${db_backends[@]}; do

      service_name=${db_backend%=*}
      service=${service_name^^}
      service=${service//-/_}
      db=${service##*_}
      prefix=${db_backend#*=}

      if [[ "$service" != *"_"* ]]; then
          echo "There is a problem with the DB_SERVICE_PREFIX_MAPPING environment variable!"
          echo "You provided the following database mapping (via DB_SERVICE_PREFIX_MAPPING): $db_backend. The mapping does not contain the database type."
          echo
          echo "Please make sure the mapping is of the form <name>-<database_type>=PREFIX, where <database_type> is either MYSQL or POSTGRESQL."
          echo
          echo "WARNING! The datasource for $prefix service WILL NOT be configured."
          continue
      fi

      host=$(find_env "${service}_SERVICE_HOST")
      port=$(find_env "${service}_SERVICE_PORT")

      if [ -z $host ] || [ -z $port ]; then
        echo "There is a problem with your service configuration!"
        echo "You provided following database mapping (via DB_SERVICE_PREFIX_MAPPING environment variable): $db_backend. To configure datasources we expect ${service}_SERVICE_HOST and ${service}_SERVICE_PORT to be set."
        echo
        echo "Current values:"
        echo
        echo "${service}_SERVICE_HOST: $host"
        echo "${service}_SERVICE_PORT: $port"
        echo
        echo "Please make sure you provided correct service name and prefix in the mapping. Additionally please check that you do not set portalIP to None in the $service_name service. Headless services are not supported at this time."
        echo
        echo "WARNING! The ${db,,} datasource for $prefix service WILL NOT be configured."
        continue
      fi

      # Custom JNDI environment variable name format: [NAME]_[DATABASE_TYPE]_JNDI
      jndi=$(find_env "${prefix}_JNDI" "java:jboss/datasources/${service,,}")

      # Database username environment variable name format: [NAME]_[DATABASE_TYPE]_USERNAME
      username=$(find_env "${prefix}_USERNAME")

      # Database password environment variable name format: [NAME]_[DATABASE_TYPE]_PASSWORD
      password=$(find_env "${prefix}_PASSWORD")

      # Database name environment variable name format: [NAME]_[DATABASE_TYPE]_DATABASE
      database=$(find_env "${prefix}_DATABASE")

      if [ -z $jndi ] || [ -z $username ] || [ -z $password ] || [ -z $database ]; then
        echo "Ooops, there is a problem with the ${db,,} datasource!"
        echo "In order to configure ${db,,} datasource for $prefix service you need to provide following environment variables: ${prefix}_USERNAME, ${prefix}_PASSWORD, ${prefix}_DATABASE."
        echo
        echo "Current values:"
        echo
        echo "${prefix}_USERNAME: $username"
        echo "${prefix}_PASSWORD: $password"
        echo "${prefix}_DATABASE: $database"
        echo
        echo "WARNING! The ${db,,} datasource for $prefix service WILL NOT be configured."
        continue
      fi

      # Transaction isolation level environment variable name format: [NAME]_[DATABASE_TYPE]_TX_ISOLATION
      tx_isolation=$(find_env "${prefix}_TX_ISOLATION")
    
      # min pool size environment variable name format: [NAME]_[DATABASE_TYPE]_MIN_POOL_SIZE
      min_pool_size=$(find_env "${prefix}_MIN_POOL_SIZE")
    
      # max pool size environment variable name format: [NAME]_[DATABASE_TYPE]_MAX_POOL_SIZE
      max_pool_size=$(find_env "${prefix}_MAX_POOL_SIZE")

      case "$db" in
        "MYSQL")
          driver="mysql"
          checker="org.jboss.jca.adapters.jdbc.extensions.mysql.MySQLValidConnectionChecker"
          sorter="org.jboss.jca.adapters.jdbc.extensions.mysql.MySQLExceptionSorter"
          ;;
        "POSTGRESQL")
          driver="postgresql"
          checker="org.jboss.jca.adapters.jdbc.extensions.postgres.PostgreSQLValidConnectionChecker"
          sorter="org.jboss.jca.adapters.jdbc.extensions.postgres.PostgreSQLExceptionSorter"
          ;;
        "MONGODB")
          continue
          ;;
        *)
          echo "There is a problem with the DB_SERVICE_PREFIX_MAPPING environment variable!"
          echo "You provided the following database mapping (via DB_SERVICE_PREFIX_MAPPING): $db_backend."
          echo "The mapping contains the following database type: ${db}, which is not supported. Currently, only MYSQL and POSTGRESQL are supported."
          echo
          echo "Please make sure you provide the correct database type in the mapping."
          echo
          echo "WARNING! The ${db,,} datasource for $prefix service WILL NOT be configured."
          continue
          ;;
      esac

      datasources="$datasources$(generate_datasource ${service,,} $jndi $username $password $host $port $database $checker $sorter $driver)\n"
    done
  fi

  datasources="$datasources$(inject_tx_datasource)"

  sed -i "s|<!-- ##DATASOURCES## -->|${datasources%$'\n'}|" $CONFIG_FILE
}
