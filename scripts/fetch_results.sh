#! /bin/bash

ssh nikhil@PradeepR7.cs.ucla.edu \
  'ssh nikhil@hope.cs.ucla.edu "cd /tmp/train_results && tar -czf /tmp/test.tgz *" && scp nikhil@hope.cs.ucla.edu:/tmp/test.tgz .' && \
( \
pushd /tmp/train_results && \
  rm -rf * && \
  scp nikhil@PradeepR7.cs.ucla.edu:~/test.tgz . && \
  tar -xzf test.tgz && \
  ls -l | wc -l; \
popd \
)
