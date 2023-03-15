# README

## SETUP
install `python3` command on your machine
```shell
make setup
```
**Suggested:** activate the `virtualenv`
```shell
source .env/vin/activate
```

## RUN RENAMER:
```shell
python renamer.py <options> <directory> <matcher> <replace_string>
```
to run it directly `chmod +x renamer.py`:
```shell
./renamer.py <directory> <matcher> <replace_string>
```
where parameters are:
- `options`: 
  - **d:** dry_run, no renaming
  - **q:** quiet, no logging
  - **c:** clean, no journal (WARN: no rollback available with no journal)
  - **r:** regexp_match, evaluates the matcher as a regexp on the whole file, allows group indicators in `replace_string` (i.e.: $1, $2, etc.)
- `directory`: root directory containing files to rename 
  - **warn:** the script works recursively on subdirectories
- `matcher`: regexp matching the part of a filename to replace
- `replace_string`: string to use for replacement

example (*generates only journal*): 
```shell
python renamer.py dq test '\.jpeg' '.jpg' 
```

## RUN RENAMER:
```shell
python prepender.py <options> <directory> <matcher> <prefix>
```
to run it directly `chmod +x renamer.py`:
```shell
./prepender.py <directory> <matcher> <prefix>
```
where parameters are:
- `options`: 
  - **d:** dry_run, no renaming
  - **q:** quiet, no logging
  - **c:** clean, no journal (WARN: no rollback available with no journal)
- `directory`: root directory containing files to rename 
  - **warn:** the script works recursively on subdirectories
- `matcher`: regexp matching the part of a filename to replace
- `prefix`: string to use as a prefix

example (*generates only journal*): 
```shell
python renamer.py dq test '\.jpeg' '.jpg' 
```

## RUN ROLLBACK:
```shell
python rollback.py <options> <journal_file>
```
to run it directly `chmod +x rollback.py`:
```shell
./rollback.py <options> <journal_file>
```
where parameters are:
- `options`: 
  - **d:** dry_run, no renaming
  - **q:** quiet, no logging
- `journal_file`: journal file to rollback

example (*log only actions*): 
```shell
python rename_rollback.py d test/rename-journal_test_1677664708.yaml 
```
