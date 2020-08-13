tests:
	@python -B -m pytest -l -W ignore::DeprecationWarning \
		--color=yes \
		--cov=src \
		--cov-config=./tests/.coveragerc \
		--cov-report term \
		--cov-report html:coverage \
		--rootdir=. $${TEST};

.PHONY: tests
