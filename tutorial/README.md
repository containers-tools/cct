## Introduction

For our first demo we will use the `jboss/wildfly` image, version 10.0.0.Final.
We will build a derivative image that wraps wildfly in cct.

Build the following image (see the included `Dockerfile`,
or just pull `jmtd/wildfly-cct`):

    FROM jboss/wildfly:10.0.0.Final
    USER root

    # Install packages necessary to install cct
    RUN yum -y install python python-setuptools git && yum clean all

    # Install cct
    RUN git clone https://github.com/containers-tools/cct \
         && cd cct \
         && easy_install . \
         && cd .. \
         && rm -rf cct

    USER jboss
    # register cct in the image
    ENTRYPOINT ["/usr/bin/cct", "-vc"]

    CMD ["/opt/jboss/wildfly/bin/standalone.sh", "-b", "0.0.0.0"]

The rest of this tutorial will assume that the image was named `wildfly-cct`.

Some points:

  * We use Docker's `ENTRYPOINT` command to ensure that cct is invoked
    when a container is started, regardless of what `CMD` is set to.

## First `cct` test

Take a look at the file `dummy.yaml`, which contains our first instructions
for cct.

One way to instruct `cct` as to what to do is via the `CCT_CHANGES` environment
variable. You can set this to a comma-separated (check) list of URLs or
filesystem paths to check for instructions. Try

    docker run -it -v $(pwd)/tutorial:/mnt -e CCT_CHANGES=/mnt/dummy.yaml wildfly-cct

You should see a bunch of test `cct` output to standard out (or the docker
container's log), such as the following

    cct - DEBUG - Executing shell command: 'pwd'
    cct - DEBUG - Captured stdout: /opt/jboss

This should be followed by the usual log output of the Wildfly service
starting up in standalone mode.

## Second `cct` test

The second test will make a change to the wildfly instance. Take a look at
`samples/jboss_cli.yaml`. It makes use of a `cct` module to invoke the JBoss
CLI and run commands against the running Wildfly instance. In this case we
are going to remove the data-source that has been defined named ExampleDS.
Start a container

    docker run -it -v $(pwd)/samples:/mnt -e CCT_CHANGES=/mnt/jboss_cli.yaml wildfly-cct

You should notice some log messages suggesting `cct` is doing some work.
First you may notice messages like the following

    ...cct - ERROR - Command failed, msg: Failed to connect to the controller: The controller is not available...

These are benign and you can ignore them. They are the result of `cct`
attempting to connect to the running wildfly instance before it has finished
starting up. `cct` will continue to retry until it is available.

To verify that the `ExampleDS` data-source has been removed, try something like

    docker exec -ti $containername /opt/jboss/wildfly/bin/jboss-cli.sh -c /subsystem=datasources:read-resource

And observe that `ExampleDS` is not present in the output.

    {
        "outcome" => "success",
        "result" => {
            "data-source" => undefined,
            "jdbc-driver" => {"h2" => undefined},
            "xa-data-source" => undefined
        }
    }

