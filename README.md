# Deprecated
This tool is deprecated you should use [Concreate](https://github.com/jboss-container-images/concreate) instead.
# CCT
containers configuration tool

[![Stories in Ready](https://badge.waffle.io/containers-tools/cct.png?label=ready&title=Ready)](https://waffle.io/containers-tools/cct)
[![Circle CI](https://circleci.com/gh/containers-tools/cct.svg?style=svg)](https://circleci.com/gh/containers-tools/cct)
[![Join the chat at https://gitter.im/containers-tools/cct](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/containers-tools/cct?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

## Installation

not supported yet, use tool directly from git

```bash
$ export PYTHONPATH="${CCT_REPO_PATH}:${PYTHONPATH}"
```
then you can run in project dir:
```bash
$ python cct/cli/main.py -h
```

## Usage

``` bash
python cct/cli/main.py -v dummy.yaml
```

if command completes successfully you should get 0 result code and no error logged on stdout
