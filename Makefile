test: prepare
	tox -- tests

test-py27: prepare
	tox -e py27 -- tests

test-py34: prepare
	tox -e py34 -- tests

clean:
	@find . -name "*.pyc" -exec rm -rf {} \;
	@rm -rf target

prepare: clean
	@mkdir target
