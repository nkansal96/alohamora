#! /bin/bash -x

# If no arguments are provided, start a shell
if [[ $# -eq 0 ]]; then
  /bin/bash

# Otherwise start tree_diff with specified arguments
else
  java -jar tree_diff.jar $@
fi
