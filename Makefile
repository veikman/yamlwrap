# GNU makefile.

.PHONY: wheel test clean

wheel:
	python3 setup.py bdist_wheel
	mv dist/*.whl .

test:
	python3 runtests.py

clean:
	-rm *.whl *.deb *.tar.gz
	rm -rf build dist deb_dist *.egg-info
