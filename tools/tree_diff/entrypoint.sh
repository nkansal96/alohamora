#! /bin/bash -x

# If no arguments are provided, start a shell
if [[ $# -eq 0 ]]; then
  /bin/bash

# Otherwise start server on the specified port
else
  java -jar tree_diff.jar $@
fi
