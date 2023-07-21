#!/usr/bin/env bash

black --quiet . --line-length 79

echo -e "\n=== MyPy ===\n"

mypy --strict .

echo -e "\n=== PyLint ===\n"

pylint apm
