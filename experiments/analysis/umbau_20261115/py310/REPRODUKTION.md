# Kursprüfung erneut ausführen

Verwendet wurde der veröffentlichte Quellstand `b2bd67e43f213cd99669bf3eee759e3fdeb1c0f5`. Die Verzeichnisse in diesem Beispiel liegen außerhalb des Arbeitsverzeichnisses der Abgabe. Die beiden Quelldateien für die Gewichte stammen aus diesem Commit. Falls die zusätzlichen Prüfdateien in einem späteren Commit liegen, `CHECK` auf den absoluten Pfad zur [Prüfdatei](verify_contents.py) setzen.

```sh
WORK=$(mktemp -d)
mkdir "$WORK/src"
git archive b2bd67e43f213cd99669bf3eee759e3fdeb1c0f5 agents scripts lux Paths.csv experiments/candidates/umbau_20261115 | tar -x -C "$WORK/src"
cd "$WORK/src"
STUDENT="$WORK/src/experiments/candidates/umbau_20261115/student_v4.pth"
V14="$WORK/src/agents/sherlock/weights/agent_p0.pth"
"$P" -m scripts.imitate pack-hybrid --student "$STUDENT" --mode mixed --combat-radius 5 --set imit_stay_bias=1.5 --set imit_unstack=true --out "$WORK/candidate/weights/agent.pth"
"$P" -m scripts.build_submission --battle --from-run "$WORK/candidate" --out "$WORK/Gruppe15_V15.zip"
"$P" "$CHECK" --v14 "$V14" --student "$STUDENT" --packed "$WORK/candidate/weights/agent.pth" --zip "$WORK/Gruppe15_V15.zip"
"$P" -I scripts/xversion_replay.py record "$WORK/Gruppe15_V15.zip" "$WORK/7171093.pkl" --seed 7171093
for INTERPRETER in "$P" "$P310" "$P310OLD"; do
  "$INTERPRETER" -I scripts/xversion_replay.py replay "$WORK/Gruppe15_V15.zip" "$WORK/7171093.pkl"
done
"$P310" -c 'from scripts import check_candidate_runner as check; check.SEEDS=(7171094,7171095); check.main()' --weights "$WORK/candidate/weights/agent.pth" --out "$WORK/runner.json"
```

`P` bezeichnet die Kursumgebung mit Python 3.13.13, torch 2.14.1, numpy 2.5.4 und Lux 0.2.1 mit drei Matches. Wir nutzten CPython 3.10.15 für Apple Silicon aus der [veröffentlichten Distribution vom 16. Oktober 2024](https://github.com/astral-sh/python-build-standalone/releases/tag/20241016). Die heruntergeladene Datei `cpython-3.10.15+20241016-aarch64-apple-darwin-install_only.tar.gz` hatte die vom Herausgeber angegebene SHA-256 `f64776f455a44c24d50f947c813738cfb7b9ac43732c44891bc831fa7940a33c`.

`P310OLD` benötigt für das Nachspielen nur torch 2.2.2 und numpy 1.26.4. Die neuere Umgebung `P310` verwendet torch 2.14.1 und numpy 2.2.6. Für den vollständigen Runner kommen luxai-s3 0.2.1, gymnax 0.0.8, gymnasium 1.4.0, jax/jaxlib 0.6.2, flax 0.10.7, pandas 2.3.3, scipy 1.14.1 und pygame 2.6.1 hinzu. Die Kurskonfiguration setzt im **eigenen** installierten Lux-Paket in `params.py` den Default `match_count_per_episode` von 5 auf 3; das Ergebnis muss SHA-256 `74511d1415879ca65ffa9b4e6b3918e8f85d711ae47b458425bebe39694df666` haben. Im Lauf waren `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS` und `VECLIB_MAXIMUM_THREADS` auf 1 und `JAX_PLATFORMS` auf `cpu` gesetzt.

Das erste Runner-Skript verwendete das von der Paketauflösung gewählte SciPy 1.15.3. macOS 27.0.1 wies dessen native PROPACK-Bibliothek beim Import der Kursgegner zurück. Bis zu diesem Abbruch wurden null Runnerpartien begonnen. Die Replaymessungen waren zu diesem Zeitpunkt schon vollständig. Der Runner-Anschluss mit dem offiziellen Wheel von SciPy 1.14.1 verwendet dasselbe gepackte Modell und dieselben angekündigten Karten.
