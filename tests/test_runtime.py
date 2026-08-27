# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Tools"))

from vao04_runtime import (  # noqa: E402
    Interpreter,
    PCG32,
    RejectionSample,
    RuntimeError04,
    Xoshiro256StarStar,
    canonical_bytes,
    categorical_index,
    condition_matches,
    scaled_index,
    utf8_order,
)


class RuntimeTests(unittest.TestCase):
    @staticmethod
    def _manifest(transitions: list[dict]) -> dict:
        semantics = {"maximumMicrosteps": 100}
        return {
            "runtime": {
                "executionSemantics": semantics,
                "randomSources": [],
            },
            "interactionModel": {
                "executionSemantics": semantics,
                "eventTypes": [
                    {"id": "urn:test:event:a"},
                    {"id": "urn:test:event:b"},
                ],
                "stateVariables": [
                    {
                        "id": "urn:test:state",
                        "valueType": "integer",
                        "defaultValue": 0,
                    }
                ],
                "transitions": transitions,
                "processModels": [],
                "routingRules": [],
                "renderBindings": [],
                "randomSources": [],
            },
        }

    def test_rfc8785_canonicalization(self) -> None:
        self.assertEqual(b'{"a":0.000001,"b":1}', canonical_bytes({"b": 1, "a": 1e-6}))

    def test_string_order_is_explicit_utf8_byte_order(self) -> None:
        values = ["z", "a", "\u00e9", "\U0001f600"]
        self.assertEqual(
            ["a", "z", "\u00e9", "\U0001f600"], sorted(values, key=utf8_order)
        )

    def test_pcg32_vector(self) -> None:
        generator = PCG32.from_record(
            {"seed": "000000000000002a", "stream": "0000000000000036"}
        )
        self.assertEqual(
            [2707161783, 2068313097, 3122475824, 2211639955],
            [generator.next_uint32() for _ in range(4)],
        )

    def test_xoshiro_vector(self) -> None:
        generator = Xoshiro256StarStar.from_record(
            {
                "seed": "0000000000000001000000000000000200000000000000030000000000000004",
            }
        )
        self.assertEqual(
            [11520, 0, 1509978240, 1215971899390074240],
            [generator.next_uint64() for _ in range(4)],
        )

    def test_xoshiro_forbids_zero_state_and_binary64_one(self) -> None:
        with self.assertRaises(ValueError):
            Xoshiro256StarStar.from_record({"seed": "0" * 64})

        class MaximumWord(Xoshiro256StarStar):
            def next_uint64(self) -> int:
                return (1 << 64) - 1

        value = MaximumWord([1, 0, 0, 0]).uniform()
        self.assertEqual((2**53 - 1) / 2**53, value)
        self.assertLess(value, 1.0)

    def test_exact_integer_selection_boundaries(self) -> None:
        self.assertEqual(0, scaled_index(0, 64, 7))
        self.assertEqual(6, scaled_index((1 << 64) - 3, 64, 7))
        with self.assertRaises(RejectionSample):
            scaled_index((1 << 64) - 1, 64, 7)
        self.assertEqual(0, categorical_index(0, 32, [1, 3]))
        self.assertEqual(1, categorical_index(1 << 30, 32, [1, 3]))
        self.assertEqual(1, categorical_index((1 << 32) - 1, 32, [1, 3]))

    def test_rejection_mapping_is_exactly_unbiased(self) -> None:
        self.assertEqual([0, 0, 1, 1, 2, 2], [scaled_index(x, 3, 3) for x in range(6)])
        for word in (6, 7):
            with self.assertRaises(RejectionSample):
                scaled_index(word, 3, 3)
        self.assertEqual(
            [0, 0, 1, 1, 1, 1],
            [categorical_index(x, 3, [1, 2]) for x in range(6)],
        )

    def test_schema_operator_spellings_match_interpreter(self) -> None:
        state = {"urn:test:state": 2}
        self.assertTrue(
            condition_matches(
                {
                    "stateVariableId": "urn:test:state",
                    "operator": "less-than-or-equal",
                    "value": 2,
                },
                state,
            )
        )
        self.assertTrue(
            condition_matches(
                {
                    "stateVariableId": "urn:test:state",
                    "operator": "greater-than-or-equal",
                    "value": 2,
                },
                state,
            )
        )

    def test_identical_writes_retain_highest_rank_for_later_conflicts(self) -> None:
        transitions = [
            {
                "id": f"urn:test:transition:{name}",
                "eventTypeId": "urn:test:event:a",
                "priority": priority,
                "conflictPolicy": "priority",
                "actions": [
                    {
                        "operation": "set-state",
                        "targetId": "urn:test:state",
                        "value": value,
                        "executionGroup": group,
                    }
                ],
            }
            for name, priority, value, group in (
                ("high", 30, 1, "a"),
                ("low-identical", 10, 1, "b"),
                ("middle-conflict", 20, 2, "c"),
            )
        ]
        result = Interpreter(self._manifest(transitions)).execute(
            [
                {
                    "eventTypeId": "urn:test:event:a",
                    "timestamp": "2026-01-01T00:00:00Z",
                    "sequence": 0,
                }
            ]
        )
        self.assertEqual(1, result["state"]["urn:test:state"])

    def test_rejection_redraws_are_bounded_by_maximum_microsteps(self) -> None:
        transition = {
            "id": "urn:test:transition:start",
            "eventTypeId": "urn:test:event:a",
            "priority": 0,
            "conflictPolicy": "priority",
            "actions": [{"operation": "start-process", "targetId": "urn:test:process"}],
        }
        manifest = self._manifest([transition])
        manifest["runtime"]["executionSemantics"]["maximumMicrosteps"] = 3
        source = {
            "id": "urn:test:random",
            "algorithm": "pcg32",
            "seed": "0000000000000001",
            "stream": "0000000000000001",
        }
        manifest["runtime"]["randomSources"] = [source]
        manifest["interactionModel"]["processModels"] = [
            {
                "id": "urn:test:process",
                "processKind": "stochastic",
                "ordering": "stochastic",
                "terminationPolicy": "completed",
                "randomSourceId": "urn:test:random",
                "probabilityDistribution": {"kind": "uniform"},
                "actions": [
                    {"operation": "emit-event", "targetId": f"urn:test:event:{x}"}
                    for x in ("a", "b", "a")
                ],
            }
        ]

        class AlwaysRejected:
            @staticmethod
            def next_word() -> tuple[int, int]:
                return 3, 2

        interpreter = Interpreter(manifest)
        interpreter.random["urn:test:random"] = AlwaysRejected()
        with self.assertRaises(RuntimeError04):
            interpreter.execute(
                [
                    {
                        "eventTypeId": "urn:test:event:a",
                        "timestamp": 0,
                        "sequence": 0,
                    }
                ]
            )

    def test_offline_trace_rejects_scheduled_or_delayed_process_semantics(self) -> None:
        transition = {
            "id": "urn:test:transition:start",
            "eventTypeId": "urn:test:event:a",
            "priority": 0,
            "conflictPolicy": "priority",
            "actions": [{"operation": "start-process", "targetId": "urn:test:process"}],
        }
        event = {"eventTypeId": "urn:test:event:a", "timestamp": 0, "sequence": 0}

        manifest = self._manifest([transition])
        manifest["interactionModel"]["processModels"] = [
            {
                "id": "urn:test:process",
                "processKind": "repeating",
                "ordering": "sequential",
                "terminationPolicy": "on-control-release",
                "timingConstraintIds": ["urn:test:timing"],
                "actions": [
                    {"operation": "emit-event", "targetId": "urn:test:event:b"}
                ],
            }
        ]
        with self.assertRaises(RuntimeError04):
            Interpreter(manifest).execute([event])

        manifest["interactionModel"]["processModels"] = [
            {
                "id": "urn:test:process",
                "processKind": "one-shot",
                "ordering": "single",
                "terminationPolicy": "completed",
                "actions": [
                    {
                        "operation": "emit-event",
                        "targetId": "urn:test:event:b",
                        "delayConstraintId": "urn:test:timing",
                    }
                ],
            }
        ]
        with self.assertRaises(RuntimeError04):
            Interpreter(manifest).execute([event])

    def test_process_trace_record_preserves_semantic_inputs_and_lineage(self) -> None:
        transition = {
            "id": "urn:test:transition:start",
            "eventTypeId": "urn:test:event:a",
            "priority": 0,
            "conflictPolicy": "priority",
            "actions": [
                {"operation": "start-process", "targetId": "urn:test:process:parent"}
            ],
        }
        manifest = self._manifest([transition])
        manifest["interactionModel"]["processModels"] = [
            {
                "id": "urn:test:process:parent",
                "processKind": "compound",
                "ordering": "sequential",
                "terminationPolicy": "completed",
                "childProcessIds": ["urn:test:process:child"],
                "actions": [],
            },
            {
                "id": "urn:test:process:child",
                "processKind": "one-shot",
                "ordering": "single",
                "terminationPolicy": "completed",
                "actions": [
                    {
                        "operation": "set-state",
                        "targetId": "urn:test:state",
                        "value": 7,
                    }
                ],
            },
        ]
        result = Interpreter(manifest).execute(
            [{"eventTypeId": "urn:test:event:a", "timestamp": 5, "sequence": 0}]
        )
        self.assertEqual(
            [
                {
                    "processId": "urn:test:process:child",
                    "operation": "set-state",
                    "targetId": "urn:test:state",
                    "value": 7,
                    "timestamp": 5,
                    "sourceTransitionId": "urn:test:transition:start",
                }
            ],
            result["emittedEvents"],
        )
        self.assertEqual(0, result["state"]["urn:test:state"])

        schema = json.loads(
            (ROOT / "Schemas/vao-manifest-0.4.0.schema.json").read_text(
                encoding="utf-8"
            )
        )
        validator = Draft202012Validator(schema).evolve(
            schema=schema["$defs"]["traceEmittedEvent"]
        )
        self.assertEqual([], list(validator.iter_errors(result["emittedEvents"][0])))
        incomplete = dict(result["emittedEvents"][0])
        incomplete.pop("value")
        self.assertTrue(list(validator.iter_errors(incomplete)))

    def test_stochastic_process_selects_before_expanding_child(self) -> None:
        transition = {
            "id": "urn:test:transition:start",
            "eventTypeId": "urn:test:event:a",
            "priority": 0,
            "conflictPolicy": "priority",
            "actions": [{"operation": "start-process", "targetId": "urn:test:parent"}],
        }
        manifest = self._manifest([transition])
        parent_source = {
            "id": "urn:test:random:parent",
            "algorithm": "pcg32",
            "seed": "0000000000000001",
            "stream": "0000000000000001",
        }
        child_source = {
            "id": "urn:test:random:child",
            "algorithm": "pcg32",
            "seed": "0000000000000002",
            "stream": "0000000000000002",
        }
        manifest["runtime"]["randomSources"] = [parent_source, child_source]
        manifest["interactionModel"]["processModels"] = [
            {
                "id": "urn:test:parent",
                "processKind": "stochastic",
                "ordering": "stochastic",
                "terminationPolicy": "completed",
                "randomSourceId": parent_source["id"],
                "probabilityDistribution": {"kind": "uniform", "parameters": {}},
                "actions": [
                    {"operation": "emit-event", "targetId": "urn:test:event:a"}
                ],
                "childProcessIds": ["urn:test:child"],
            },
            {
                "id": "urn:test:child",
                "processKind": "stochastic",
                "ordering": "stochastic",
                "terminationPolicy": "completed",
                "randomSourceId": child_source["id"],
                "probabilityDistribution": {"kind": "uniform", "parameters": {}},
                "actions": [
                    {"operation": "emit-event", "targetId": "urn:test:event:b"}
                ],
            },
        ]

        class SelectFirst:
            @staticmethod
            def next_word() -> tuple[int, int]:
                return 0, 1

        class MustNotDraw:
            @staticmethod
            def next_word() -> tuple[int, int]:
                raise AssertionError("an unselected stochastic child was expanded")

        interpreter = Interpreter(manifest)
        interpreter.random[parent_source["id"]] = SelectFirst()
        interpreter.random[child_source["id"]] = MustNotDraw()
        result = interpreter.execute(
            [{"eventTypeId": "urn:test:event:a", "timestamp": 0, "sequence": 0}]
        )
        self.assertEqual("urn:test:event:a", result["emittedEvents"][0]["targetId"])
        self.assertEqual("urn:test:parent", result["emittedEvents"][0]["processId"])

    def test_process_expansion_does_not_depend_on_python_recursion(self) -> None:
        transition = {
            "id": "urn:test:transition:start",
            "eventTypeId": "urn:test:event:a",
            "priority": 0,
            "conflictPolicy": "priority",
            "actions": [{"operation": "start-process", "targetId": "urn:test:p:0"}],
        }
        manifest = self._manifest([transition])
        process_count = 1_500
        manifest["interactionModel"]["processModels"] = [
            {
                "id": f"urn:test:p:{index}",
                "processKind": "compound" if index + 1 < process_count else "one-shot",
                "ordering": "sequential" if index + 1 < process_count else "single",
                "terminationPolicy": "completed",
                "actions": (
                    []
                    if index + 1 < process_count
                    else [{"operation": "emit-event", "targetId": "urn:test:event:b"}]
                ),
                **(
                    {"childProcessIds": [f"urn:test:p:{index + 1}"]}
                    if index + 1 < process_count
                    else {}
                ),
            }
            for index in range(process_count)
        ]
        result = Interpreter(manifest).execute(
            [{"eventTypeId": "urn:test:event:a", "timestamp": 0, "sequence": 0}]
        )
        self.assertEqual("urn:test:event:b", result["emittedEvents"][0]["targetId"])

    def test_microstep_bound_applies_per_run_to_completion_cycle(self) -> None:
        transition = {
            "id": "urn:test:transition:two-actions",
            "eventTypeId": "urn:test:event:a",
            "priority": 0,
            "conflictPolicy": "priority",
            "actions": [
                {
                    "operation": "set-state",
                    "targetId": "urn:test:state",
                    "value": value,
                }
                for value in (1, 2)
            ],
        }
        manifest = self._manifest([transition])
        manifest["runtime"]["executionSemantics"]["maximumMicrosteps"] = 2
        result = Interpreter(manifest).execute(
            [
                {
                    "eventTypeId": "urn:test:event:a",
                    "timestamp": timestamp,
                    "sequence": timestamp,
                }
                for timestamp in (0, 1)
            ]
        )
        self.assertEqual(2, result["state"]["urn:test:state"])

    def test_reference_total_microstep_limit_bounds_long_traces(self) -> None:
        transition = {
            "id": "urn:test:transition:two-actions",
            "eventTypeId": "urn:test:event:a",
            "priority": 0,
            "conflictPolicy": "priority",
            "actions": [
                {
                    "operation": "set-state",
                    "targetId": "urn:test:state",
                    "value": value,
                }
                for value in (1, 2)
            ],
        }
        manifest = self._manifest([transition])
        manifest["runtime"]["executionSemantics"]["maximumMicrosteps"] = 2
        events = [
            {
                "eventTypeId": "urn:test:event:a",
                "timestamp": timestamp,
                "sequence": timestamp,
            }
            for timestamp in (0, 1)
        ]
        with (
            patch("vao04_runtime.MAX_REFERENCE_TOTAL_MICROSTEPS", 3),
            self.assertRaises(RuntimeError04),
        ):
            Interpreter(manifest).execute(events)


if __name__ == "__main__":
    unittest.main()
