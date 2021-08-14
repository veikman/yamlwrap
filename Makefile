# GNU makefile.

example/a1_wrapped.yaml: example/a0_original.yaml
	python3 -m yamlwrap write example/a0_original.yaml --wrap --target $@
example/a2_unwrapped.yaml: example/a0_original.yaml
	python3 -m yamlwrap write example/a0_original.yaml --unwrap --target $@
example/a3_rewrapped.yaml: example/a0_original.yaml
	python3 -m yamlwrap write example/a0_original.yaml --rewrap --target $@
