#! /bin/bash

ssh zion-7.cs.ucla.edu 'cd ~/push-policy && ./mk_eval_tar.sh eval_results_dir eval_results.tgz' || exit 1
ssh zion-8.cs.ucla.edu 'cd ~/push-policy && ./mk_eval_tar.sh eval_results_dir eval_results.tgz' || exit 1
scp zion-7.cs.ucla.edu:'~/push-policy/eval_results.tgz' /tmp/eval_results_7.tgz                 || exit 1
scp zion-8.cs.ucla.edu:'~/push-policy/eval_results.tgz' /tmp/eval_results_8.tgz                 || exit 1

pushd /tmp
    rm -rf eval_results_dir
    tar -xzf eval_results_7.tgz && ls -l eval_results_dir | wc -l
    tar -xzf eval_results_8.tgz && ls -l eval_results_dir | wc -l
popd
