
clean: clean-build clean-pyc

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

lint:
	flake8 *.py

test:
	pytest

install: clean
	python setup.py install

install-develop: clean
	pip install -e .[dev,test]


dev-server:
	flipper-server --loglevel=INFO --host=localhost --port=5000
