# Python3.10 SciPy repair — stable library environment

Completed03Nov2026,00:49UTC, inside the20-minute bound. Only the isolated
`/tmp/sherlock-continue-20261102/venv310` SciPy dependency was replaced. No repo,
shared3.13 environment, engine source, model or submission was changed. No agent,
environment instance, game, course runner or checkpoint load was executed here.
Root owns all actual V14 course/replay validation after this handoff.

## Result

| Component | Before | Final |
|---|---|---|
| CPython |3.10.22|3.10.22|
| SciPy |1.15.3, macOS14 ARM64|1.14.1, macOS14 ARM64|
| Torch |2.2.2|2.2.2|
| NumPy |1.26.4|1.26.4|
| JAX / JAXlib |0.4.35 /0.4.35|0.4.35 /0.4.35|
| Lux engine |0.2.1, exact course patch|unchanged|

Final `uv pip check`: **60packages, all compatible**, exit0.
Final isolated library smoke: **PASS**, exit0,9.545seconds. It imported SciPy
signal/sparse.linalg/ndimage/linalg/optimize/integrate/special/fft/stats, all four
PROPACK extensions, Torch, NumPy, JAX, JAXlib, Gymnax and `luxai_s3.env`. A tiny
`convolve2d` calculation exactly matched its explicit3×3 reference. No `agents`,
`scripts` or course-runner modules were imported; no model or environment object
was constructed. This is library compatibility evidence, **not** a passed V14
course test or release approval.

## Diagnosis and wheel selection

The original course attempt failed before games, while Solution92's import of
`scipy.signal.convolve2d` transitively loaded PROPACK. The minimal independent
reproduction `from scipy.signal import convolve2d` failed identically under
isolated3.10 (`-I -B`) without importing any project code.

Read-only Mach-O parsing confirmed installed `_spropack`'s `__DATA/__thread_bss`
section had type18 (thread-local zero-fill), size8, offset114992. The local
macOS27.0.1 loader rejected that nonzero offset. The original binary's SHA256:
`dad5761989d85578a9daa55821c31e92ecea17fab414a0bd2075fd27f11c405f`.
The same before hash is recorded in `py310_repair_before.json`.

The official alternate SciPy1.15.3 macOS12 ARM64 wheel had19 malformed zero-fill
sections, including the same PROPACK offset; it was inspected only, not installed.
Older official1.14.1/1.13.1/1.11.4 macOS12 wheels had none. SciPy1.14.1 satisfies
JAX/JAXlib's `scipy>=1.10` and NumPy1.26.4 satisfies its `numpy>=1.23.5,<2.3`.

The first1.14.1 macOS12 wheel imported successfully, but was rejected by
`uv pip check` because its internal `WHEEL` tag said `macosx_12_3_arm64` whereas
its official filename said `macosx_12_0_arm64`. That intermediate result was
preserved rather than reported as fully compatible. The final official1.14.1
**macOS14** wheel has matching `cp310-cp310-macosx_14_0_arm64` metadata, zero
malformed sections in202 inspected zero-fill sections, and passed package checks
and all library smokes. No native headers or package metadata were patched.

Final wheel:

`scipy-1.14.1-cp310-cp310-macosx_14_0_arm64.whl`

SHA256: `8bddf15838ba768bb5f5083c1ea012d64c9a444e16192762bd858f1e126196d0`.

Downloaded with normal verified HTTPS from its official PyPI-listed
[files.pythonhosted.org asset](https://files.pythonhosted.org/packages/07/42/0e0bea9666fcbf2cb6ea0205db42c81b1f34d7b729ba251010edf9c80ebd/scipy-1.14.1-cp310-cp310-macosx_14_0_arm64.whl),
then checked against the official PyPI JSON SHA before installation. The SciPy
project issue records this same failure shape, while noting newer versions and
nonreproduction on another macOS version; this report's conclusion relies on the
local controlled before/after evidence, not a claim that all machines are
affected. [SciPy issue25635](https://github.com/scipy/scipy/issues/25635).

## Exact mutation commands

Only SciPy was installed, twice from local verified wheels; no dependency
resolution changes, native builds, TLS bypass, security change or binary patch:

```sh
UV_CACHE_DIR=/tmp/sherlock-continue-20261102/py310_repair_uv_cache \
  /tmp/sherlock-continue-20261102/tooling/uv/bin/uv pip install \
  --python /tmp/sherlock-continue-20261102/venv310/bin/python \
  --reinstall-package scipy --no-deps --no-index --link-mode copy \
  /tmp/sherlock-continue-20261102/py310_repair_wheels/scipy-1.14.1-cp310-cp310-macosx_12_0_arm64.whl

UV_CACHE_DIR=/tmp/sherlock-continue-20261102/py310_repair_uv_cache \
  /tmp/sherlock-continue-20261102/tooling/uv/bin/uv pip install \
  --python /tmp/sherlock-continue-20261102/venv310/bin/python \
  --reinstall-package scipy --no-deps --no-index --link-mode copy \
  /tmp/sherlock-continue-20261102/py310_repair_wheels/scipy-1.14.1-cp310-cp310-macosx_14_0_arm64.whl

/tmp/sherlock-continue-20261102/tooling/uv/bin/uv pip check \
  --python /tmp/sherlock-continue-20261102/venv310/bin/python
```

`otool -l` could not run because Xcode's license is unaccepted; its failure log
was retained. No license, Xcode or security setting was changed. Equivalent
read-only section parsing used stdlib `struct` and `zipfile` on the actual bytes.

## Preserved identities and evidence

All59 other distributions have unchanged versions and `RECORD` hashes; the only
changed distribution is SciPy. The interpreter binary remains SHA
`c21b8f194a501a60896bc83a39835b72a6c684302a40f7e72d8f0629ada47e5f`.
All10 Lux engine `.py` files remain byte-identical, including exact course
`params.py` SHA `74511d1415879ca65ffa9b4e6b3918e8f85d711ae47b458425bebe39694df666`.
Both active V14 weights remain SHA
`98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`;
current ZIP remains SHA
`88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`.

Under `/tmp/sherlock-continue-20261102/`:

- `py310_original_runner_failed.log`: byte-preserved original failed course log.
- `py310_scipy_import_before.log`: minimal failing reproduction.
- `py310_scipy_1153_forensics/`: original four PROPACK binaries +METADATA/WHEEL/RECORD.
- `py310_repair_before.json`, `py310_repair_binary_before.json`,
  `py310_repair_package_records_before.json`: original state and protected hashes.
- `py310_scipy_reinstall.log`, `py310_uv_check_after.log`,
  `py310_scipy_import_after.log`: preserved intermediate macOS12 attempt.
- `py310_scipy_reinstall_macos14.log`, `py310_uv_check_final.log`,
  `py310_library_smoke_final.log`: final successful installation/library evidence.
- `py310_repair_after.json`: final state, exact package delta and preservation checks.
- `py310_wheel_analysis_*.json`, official `py310_scipy_*_pypi.json`,
  `py310_repair_wheels/`: inspected official wheel provenance and section analysis.

`/tmp/py310_repair_report.json` binds these artifacts and commands. Root was
notified stable at00:49UTC. No further dependency mutation is planned by this
agent; Root may now own the actual unchanged-V143.10 course/replay checks.
