# STOP cleanup tests: calendar independence (2026-11-04)

- Before: reproduced exactly the two reported failures with the project interpreter. Both expected `STOP` but received `Hard game deadline reached` (2 failed in 0.16s).
- Root cause: their study modules retain historical fixed `GAME_END` timestamps. Once those dates pass, the admission guard rejects the synthetic job before its real stdlib sleeping child and STOP callback can exercise cleanup.
- Change: inside each affected test only, set `study.GAME_END` to `time.time() + 60` using pytest monkeypatch. Real wall-clock behavior, production deadlines, child commands, and all cleanup assertions remain unchanged.
- After: `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B -m pytest -q tests/test_final_battle_study.py tests/test_network_breadth_study.py` → **43 passed in 5.07s** (exit 0).
- Scope: two test functions only; no games, training, agent/script/weight changes, or commits. Root to include this result in the shared Arbeitsstand during integration; no open issue in this fix.
