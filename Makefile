PYTHON_FILES = $(shell find mldl -type f -name "*.py")

.PHONY: all check-schema

all: dist

dist: $(PYTHON_FILES) *.txt setup.py
	rm -rf dist build
	python3 setup.py sdist bdist_wheel
	rm -rf build

upload-legacy: dist
	@ python3 -m awscli s3 cp --recursive dist s3://zensors-ml-utils/mldl --acl public-read
	@ python3 -m awscli s3 ls s3://zensors-ml-utils/mldl/ | rev | cut -d ' ' -f 1 | rev | grep whl | while read line; do echo "<a href=\"$$line\">$$line</a><br>"; done > index.html
	@ python3 -m awscli s3 cp index.html s3://zensors-ml-utils/mldl/index.html --acl public-read
	@ rm -f index.html

test:
	python3 -m pytest tests/**/test_*.py

# if you find this not working for you
# ensure that you have registered https://zpi.admin.zensors.live in your
# ~/.pypirc with the appropriate credentials and the name "zensors"
upload:
	@ python setup.py bdist_wheel upload -r zensors
