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
	find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf

example/a1_wrapped.yaml: example/a0_original.yaml
	python3 -m yamlwrap write example/a0_original.yaml --wrap --target $@
example/a2_unwrapped.yaml: example/a0_original.yaml
	python3 -m yamlwrap write example/a0_original.yaml --unwrap --target $@
example/a3_rewrapped.yaml: example/a0_original.yaml
	python3 -m yamlwrap write example/a0_original.yaml --rewrap --target $@
