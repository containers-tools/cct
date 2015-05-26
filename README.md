# cct
containers configuration tool

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
cct can be executed in a two ways:

### one command execution
in this scenario you can execute any suported module command in a way:
``` bash
python cct/cli/main.py -v run dummy foo bar baz
```

### yaml file format processing
in this scenatio you can process simple yaml file containing multiple instructions:
``` bash
python cct/cli/main.py -v process dummy.yaml
```