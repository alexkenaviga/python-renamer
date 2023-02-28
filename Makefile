setup: requirements.txt
	test -d .env || python3 -m venv .env
	.env/bin/python -m pip install -U pip
	.env/bin/python -m pip install -r requirements.txt
	touch .env/bin/activate

clean:
	rm -r .env