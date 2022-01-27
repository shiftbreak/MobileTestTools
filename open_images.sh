#!/bin/bash

for l in `find . -name '*' -exec file {} \; | grep -o -P '^.+: \w+ image' | sed 's/:.*//g'`; do display $l & done
