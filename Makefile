# GNU makefile.

.PHONY: wheel clean

wheel:
	python3 setup.py bdist_wheel
	mv dist/*.whl .

clean:
	-rm -rf *.whl
	-rm -rf build
	-rm dist/* && rmdir dist/
	-rm *.egg-info/* && rmdir *.egg-info/
