# README

## SETUP
install `python3` command on your machine
```
make setup
```

## RUN THE COMMAND
**Suggested:** activate the `virtualenv`
```
source .env/vin/activate
```
Run renamer:
```
python renamer.py <directory> <matcher> <replace_string>
```
to run it directly `chmod +x renamer.py`:
```
./renamer.py <directory> <matcher> <replace_string>
```
where parameters are:
- `directory`: root directory containing files to rename 
  - **warn:** the script works recursively on subdirectories
- `matcher`: regexp matching the part of a filename to replace
- `replace_string`: string to use for replacement