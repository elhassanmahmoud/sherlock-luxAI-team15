# Independent Fog influence data/math audit

**PASS** — 10000 sampled rows, 9996 exact unique feature/mask pairs, four duplicate rows beyond unique. All four original replay hashes and sequential PCG64(0) indices reproduced exactly, with matching nonterminal ns/mask rows and2500 rows per arm.

All40 stored member arrays finite and correctly ordered; NumPy36/38 means agree with recorded means under the declared atol=1e-6, rtol=1e-6 comparison (maximum absolute difference 1.52587890625e-5; accepted by the relative term), and stored independently forwarded candidate means equal recorded candidate means exactly. Every member/ensemble legal argmax agrees for actualAgent −inf and diagnostic −1e9. All 1906 summary fields/statistics independently reproduced from stored arrays.

Control changes143/10000 (SAPto3/from5); neutral139/10000 (to4/from4). New members versus parent18: control41=2055, control42=1889, neutral41=1962, neutral42=1895.

Post hoc, nonselectable arithmetic INIT38 check: {"label": "POST HOC interpretation check only; nonselectable arithmetic reference", "definition": "INIT38=mean(original36 stored Q arrays + two copies of stored original18 Q); NumPy float32 reduction", "INIT38_vs_V14": {"rows": 10000, "changed": 142, "to_sap": 4, "from_sap": 3}, "CONTROL38_vs_INIT38": {"rows": 10000, "changed": 117, "to_sap": 2, "from_sap": 5}, "NEUTRAL38_vs_INIT38": {"rows": 10000, "changed": 116, "to_sap": 3, "from_sap": 4}, "limits": "Different baselines: 19\u201321% versus parent18 cannot be compared directly with 1.4% versus V14. Low ensemble disagreement does not prove averaging suppresses helpful learning. No action-quality or causal reward conclusion."}

Independent NumPy/stdlib recomputation of stored output arithmetic and original replay sampling. No Torch/model import, independent neural forward, tests, games, fitting or weight file. Recorded model member identity is checked against admitted/historically accepted hash metadata and model-file byte bindings, not newly recomputed tensor hashes. Source/HEAD/runtime/input/protected hashes verified unchanged before and after. Original summary was not modified.
