# Environment variables


## Variables provided in runtime for your scripts

To make CCT modules easier to develop, CCT provides some environment variables for you to use:

### Modules variables

Every shell/script CCT module introduce its file system path via variable `CCT_MODULE_PATH_MODULE_<NAME>`. There is also special variable `CCT_MODULE_PATH` - which points you to current module path.

*Example*: If you have CCT module named **CE_MODULE** its location will be available via variable `CCT_MODULE_PATH_CE_MODULE`.

### Artifact variables

Each artifact defined in module.yaml is accessible via environment variable `CCT_ARTIFACT_<NAME>_PATH`.

*Example*: If you have following section in module.yaml:

``` yaml
artifacts:
  - name: jolokia
    chksum: md5:240381af7039461f3472b7796fe9cd4b
```
It will be available for you as: `CCT_ARTIFACT_JOLOKIA_PATH`.
