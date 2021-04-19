# GNU makefile.

.PHONY: clean, wheel, test

test:
	python3 -m pytest

wheel:
	python3 -m build
	mv dist/*.whl .

clean:
	-rm *.whl *.tar.gz
	rm -rf build dist src/*.egg-info
