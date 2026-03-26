#!/bin/bash -eu
python3 -m pip install .
python3 -m pip install --require-hashes -r .clusterfuzzlite/requirements.txt
# compile fuzzer
compile_python_fuzzer "$SRC/vector-topic-modeling/tests/fuzz_sanitize.py"
