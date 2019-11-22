# GNU makefile.

.PHONY: wheel deb-package deb-install test clean

NAME := vedm
UNDERSCORE = $(subst -,_,$(NAME))
DEBNAME = python3-$(NAME)

wheel:
	python3 setup.py bdist_wheel
	mv dist/*.whl .

# Python setuptools does not support runtests.py. Loading the unittest module
# without the precautions in that script will crash, so DEB_BUILD_OPTIONS is
# set to prevent testing as part of the build process.
deb-package:
	DEB_BUILD_OPTIONS=nocheck python3 setup.py --command-packages=stdeb.command bdist_deb
	mv deb_dist/$(DEBNAME)_*.deb .
	rm $(UNDERSCORE)-*.tar.gz
	rm -rf deb_dist dist $(UNDERSCORE).egg-info

deb-install: deb-package
	sudo dpkg -i $(DEBNAME)_*.deb

test:
	python3 runtests.py

clean:
	-rm -rf *.whl
	-rm -rf build
	-rm dist/*
	-rmdir dist/
	-rm -rf deb_dist
	-rm *tar.gz
	-rm *.egg-info/* && rmdir *.egg-info/
