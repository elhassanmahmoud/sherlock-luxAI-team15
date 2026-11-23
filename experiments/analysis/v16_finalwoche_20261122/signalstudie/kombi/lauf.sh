#!/bin/sh
set -eu
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 BLIS_NUM_THREADS=1 JAX_PLATFORMS=cpu
export PYTHONHASHSEED=0 CUDA_VISIBLE_DEVICES='' XLA_FLAGS='--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1'
task=$1
shift
case "$task" in technik|frisch) ;; *) exit 2;; esac
exec "${PYTHON:-python}" "$(dirname "$0")/$task.py" "$@"
