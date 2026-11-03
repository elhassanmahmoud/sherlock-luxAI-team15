"""Offline AST/NumPy contracts; never import the training wrapper/model stack.

The executable snippets contain only _arm, rollout_plan, validation_plan and
_config, extracted from the candidate's AST with no import statements.
"""
import ast
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
import unittest

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "scripts/targeting_adapt.py"
BACKUP = ROOT / "scripts/targeting_adapt_backup.py"
CHANGED_CONSTANTS = {"PROTOCOL", "_VARIANT", "ARMS"}
PURE_FUNCTIONS = {"_arm", "rollout_plan", "validation_plan", "_config"}


def parse(path):
    return ast.parse(path.read_text(), filename=str(path))


def assignments(tree):
    return {node.targets[0].id: node.value for node in tree.body
            if isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)}


def normalized(tree):
    nodes = []
    for index, node in enumerate(tree.body):
        if index == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name) and node.targets[0].id in CHANGED_CONSTANTS):
            continue
        nodes.append(node)
    return ast.dump(ast.Module(body=nodes, type_ignores=[]), include_attributes=False)


def pure_namespace(tree):
    constants = assignments(tree)
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in PURE_FUNCTIONS]
    if {node.name for node in nodes} != PURE_FUNCTIONS:
        raise AssertionError("Missing an explicitly allowed pure contract function")
    namespace = {"np": np, "ARMS": ast.literal_eval(constants["ARMS"])}
    module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    exec(compile(module, str(BACKUP), "exec"), namespace)
    return namespace


class BackupAdaptationContractTests(unittest.TestCase):
    def candidate(self):
        self.assertTrue(BACKUP.is_file(), "The separately named backup wrapper is missing")
        return parse(BACKUP)

    def test_separately_named_backup_source_exists(self):
        self.assertTrue(BACKUP.is_file(), "The separately named backup wrapper is missing")

    def test_only_named_constants_and_module_docstring_differ_from_reviewed_source(self):
        original, backup = parse(ORIGINAL), self.candidate()
        self.assertEqual(normalized(backup), normalized(original))
        original_functions = {node.name: ast.dump(node, include_attributes=False) for node in original.body
                              if isinstance(node, ast.FunctionDef)}
        backup_functions = {node.name: ast.dump(node, include_attributes=False) for node in backup.body
                            if isinstance(node, ast.FunctionDef)}
        self.assertEqual(backup_functions, original_functions)

    def test_exact_new_adaptation_roster_and_distinct_protocol_variant(self):
        tree = self.candidate()
        constants = assignments(tree)
        self.assertEqual(ast.literal_eval(constants["ARMS"]),
                         {"adapt18": (18, 30, True), "adapt19": (19, 31, True)})
        self.assertEqual(ast.literal_eval(constants["_VARIANT"]), "targeting_adaptation_backup_20261102")
        protocol = constants["PROTOCOL"]
        self.assertIsInstance(protocol, ast.BinOp)
        self.assertIsInstance(protocol.op, ast.Div)
        self.assertEqual(ast.dump(protocol.left), ast.dump(ast.Name(id="ROOT", ctx=ast.Load())))
        self.assertEqual(ast.literal_eval(protocol.right),
                         "docs/superpowers/plans/2026-11-02-conditional-backup-adaptation.md")
        self.assertTrue((ROOT / ast.literal_eval(protocol.right)).is_file())
        namespace = pure_namespace(tree)
        for forbidden in ("control18", "control19", "adapt20"):
            with self.subTest(arm=forbidden), self.assertRaises(ValueError):
                namespace["_arm"](forbidden)

    def test_exact_30_31_maps_sides_counts_and_opponent_rng(self):
        namespace = pure_namespace(self.candidate())
        for arm, run_seed, first_train, last_train, first_prefill, last_prefill in (
                ("adapt18", 30, 504200, 504499, 505000, 505059),
                ("adapt19", 31, 514200, 514499, 515000, 515059)):
            with self.subTest(arm=arm):
                rows = namespace["rollout_plan"](arm)
                self.assertEqual(len(rows), 720)
                self.assertEqual(Counter(row["phase"] for row in rows), {"prefill": 120, "train": 600})
                self.assertEqual((rows[0]["seed"], rows[119]["seed"], rows[120]["seed"], rows[-1]["seed"]),
                                 (first_prefill, last_prefill, first_train, last_train))
                self.assertEqual([(rows[i]["side"], rows[i + 1]["side"]) for i in range(0, 720, 2)],
                                 [("player_0", "player_1")]*360)
                self.assertEqual([(rows[i]["seed"], rows[i + 1]["seed"]) for i in range(0, 120, 2)],
                                 [(seed, seed) for seed in range(first_prefill, last_prefill + 1)])
                self.assertEqual([(rows[i]["seed"], rows[i + 1]["seed"]) for i in range(120, 720, 2)],
                                 [(seed, seed) for seed in range(first_train, last_train + 1)])
                self.assertEqual([row["game"] for row in rows[:120]], list(range(120)))
                self.assertEqual([row["game"] for row in rows[120:]], list(range(600)))
                # Independent wire reference, not the production schedule helper.
                rng = np.random.default_rng(run_seed + 4200)
                indices = rng.choice(4, size=720, p=[.6, .2, .1, .1])
                names = ("solution92", "sol92_sq", "default", "rush")
                self.assertEqual([row["opponent"] for row in rows], [names[index] for index in indices])

    def test_known_validation_stays_96_games_per_arm_and_1632_total(self):
        namespace = pure_namespace(self.candidate())
        rows = namespace["validation_plan"]()
        expected = [(after, opponent, seed, side) for after in (0, 300, 600)
                    for opponent in ("default", "solution92") for seed in range(500000, 500008)
                    for side in ("player_0", "player_1")]
        self.assertEqual([(r["after_games"], r["opponent"], r["seed"], r["side"]) for r in rows], expected)
        self.assertEqual(len(rows), 96)
        self.assertEqual(sum(len(namespace["rollout_plan"](arm)) + len(rows)
                             for arm in namespace["ARMS"]), 1632)

    def test_training_config_changes_only_existing_overrides_and_both_p_flags(self):
        namespace = pure_namespace(self.candidate())
        source = dict(frozen=True, lr=.0003, w_discovery=7., w_explore=8.,
                      rules_in_training=False, rules_in_training_all=False,
                      point_pair_swap=False, art_move_guard=False,
                      eps_end=.05, eps_decay_steps=60000, reward_fix=True,
                      marker="preserve full source config")
        original = dict(source)
        for _, _, enabled in namespace["ARMS"].values():
            actual = namespace["_config"](source, enabled)
            self.assertEqual(actual, dict(source, frozen=False, lr=.0001, w_discovery=.5,
                w_explore=.3, rules_in_training=True, rules_in_training_all=True,
                point_pair_swap=True, art_move_guard=True))
        self.assertEqual(source, original)
        constants = assignments(self.candidate())
        self.assertEqual(ast.literal_eval(constants["MIX"]),
                         "solution92=0.6,sol92_sq=0.2,default=0.1,rush=0.1")
        self.assertEqual(ast.literal_eval(constants["EVAL_SEED"]), 20261102)

    def test_no_training_model_or_environment_module_was_imported(self):
        # Other tests legitimately import these modules in the pytest process.
        # Exercise the actual AST helpers in a fresh interpreter so any forbidden
        # import here belongs to this contract, regardless of test ordering.
        probe = """
import json
import runpy
import sys

sys.path.insert(0, sys.argv[1])
contract = runpy.run_path(sys.argv[2])
namespace = contract["pure_namespace"](contract["parse"](contract["BACKUP"]))
namespace["rollout_plan"]("adapt18")
prefixes = ("torch", "agents", "luxai_s3", "lux.runner", "scripts.targeting_adapt",
            "scripts.targeting_adapt_backup", "scripts.experiment", "scripts.finetune")
print(json.dumps(sorted(name for name in sys.modules
                        if any(name == prefix or name.startswith(prefix + ".")
                               for prefix in prefixes))))
"""
        result = subprocess.run(
            [sys.executable, "-I", "-B", "-c", probe, str(ROOT), str(Path(__file__).resolve())],
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [], "Forbidden imports in isolated AST contract")


if __name__ == "__main__":
    unittest.main()
