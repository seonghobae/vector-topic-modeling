#!/bin/bash -eu
python3 -m pip install --require-hashes -r .clusterfuzzlite/requirements.txt
python3 -m pip install --no-deps -e .

# compile fuzzer
compile_python_fuzzer "$SRC/vector-topic-modeling/tests/fuzz_sanitize.py"
