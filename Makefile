# GNU makefile.

.PHONY: wheel deb-package deb-install clean

NAME := vedm
UNDERSCORE = $(subst -,_,$(NAME))
DEBNAME = python3-$(NAME)

wheel:
	python3 setup.py bdist_wheel
	mv dist/*.whl .

deb-package:
	python3 setup.py --command-packages=stdeb.command bdist_deb
	mv deb_dist/$(DEBNAME)_*.deb .
	rm $(UNDERSCORE)-*.tar.gz
	rm -rf deb_dist dist $(UNDERSCORE).egg-info

deb-install: deb-package
	sudo dpkg -i $(DEBNAME)_*.deb

clean:
	-rm -rf *.whl
	-rm -rf build
	-rm dist/* && rmdir dist/
	-rm *.egg-info/* && rmdir *.egg-info/
