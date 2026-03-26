#!/bin/bash -eu
pip3 install .
pip3 install atheris
# compile fuzzer
compile_python_fuzzer $SRC/vector-topic-modeling/tests/fuzz_sanitize.py fuzz_sanitize
