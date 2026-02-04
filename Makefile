default: setup

setup: requirements.txt
	test -d .venv || python3 -m venv .venv
	.venv/bin/python -m pip install -U pip
	.venv/bin/python -m pip install -r requirements.txt
	touch .venv/bin/activate

install: 
	.venv/bin/pip install -e .

uninstall: 
	.venv/bin/pip uninstall renamer

clean:
	rm -r .venv