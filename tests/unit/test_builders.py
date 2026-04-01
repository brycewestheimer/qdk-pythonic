"""Tests for circuit builder functions."""

from __future__ import annotations

import math

import pytest

from qdk_pythonic.builders import (
    bell_state,
    ghz_state,
    inverse_qft,
    qft,
    random_circuit,
    w_state,
)
from qdk_pythonic.core.instruction import Instruction, Measurement
from qdk_pythonic.exceptions import CircuitError

# ------------------------------------------------------------------
# bell_state
# ------------------------------------------------------------------


class TestBellState:
    @pytest.mark.unit
    def test_returns_circuit(self) -> None:
        circ = bell_state()
        assert circ.qubit_count() == 2

    @pytest.mark.unit
    def test_gate_sequence(self) -> None:
        circ = bell_state()
        instrs = [i for i in circ.instructions if isinstance(i, Instruction)]
        assert len(instrs) == 2
        assert instrs[0].gate.name == "H"
        assert instrs[1].gate.name == "CNOT"

    @pytest.mark.unit
    def test_no_measurements_by_default(self) -> None:
        circ = bell_state()
        measurements = [i for i in circ.instructions if isinstance(i, Measurement)]
        assert len(measurements) == 0

    @pytest.mark.unit
    def test_measure_flag(self) -> None:
        circ = bell_state(measure=True)
        measurements = [i for i in circ.instructions if isinstance(i, Measurement)]
        assert len(measurements) == 2

    @pytest.mark.unit
    def test_qsharp_generation(self) -> None:
        qs = bell_state().to_qsharp()
        assert "H(" in qs
        assert "CNOT(" in qs

    @pytest.mark.unit
    def test_openqasm_generation(self) -> None:
        qasm = bell_state().to_openqasm()
        assert "h " in qasm
        assert "cx " in qasm


# ------------------------------------------------------------------
# ghz_state
# ------------------------------------------------------------------


class TestGHZState:
    @pytest.mark.unit
    def test_qubit_count(self) -> None:
        assert ghz_state(5).qubit_count() == 5

    @pytest.mark.unit
    def test_gate_sequence_3_qubits(self) -> None:
        circ = ghz_state(3)
        instrs = [i for i in circ.instructions if isinstance(i, Instruction)]
        assert len(instrs) == 3  # H + 2 CNOT
        assert instrs[0].gate.name == "H"
        assert all(i.gate.name == "CNOT" for i in instrs[1:])

    @pytest.mark.unit
    def test_n_equals_2_matches_bell(self) -> None:
        ghz = ghz_state(2)
        bell = bell_state()
        ghz_instrs = [i for i in ghz.instructions if isinstance(i, Instruction)]
        bell_instrs = [i for i in bell.instructions if isinstance(i, Instruction)]
        assert len(ghz_instrs) == len(bell_instrs)
        for g, b in zip(ghz_instrs, bell_instrs):
            assert g.gate.name == b.gate.name

    @pytest.mark.unit
    def test_n_less_than_2_raises(self) -> None:
        with pytest.raises(CircuitError, match="n >= 2"):
            ghz_state(1)

    @pytest.mark.unit
    def test_measure_flag(self) -> None:
        circ = ghz_state(3, measure=True)
        measurements = [i for i in circ.instructions if isinstance(i, Measurement)]
        assert len(measurements) == 3

    @pytest.mark.unit
    def test_qsharp_generation(self) -> None:
        qs = ghz_state(3).to_qsharp()
        assert "H(" in qs
        assert "CNOT(" in qs

    @pytest.mark.unit
    def test_openqasm_generation(self) -> None:
        qasm = ghz_state(3).to_openqasm()
        assert "h " in qasm
        assert "cx " in qasm


# ------------------------------------------------------------------
# w_state
# ------------------------------------------------------------------


class TestWState:
    @pytest.mark.unit
    def test_qubit_count(self) -> None:
        assert w_state(3).qubit_count() == 3

    @pytest.mark.unit
    def test_3_qubit_gate_count(self) -> None:
        circ = w_state(3)
        instrs = [i for i in circ.instructions if isinstance(i, Instruction)]
        # X + 2*(Ry + CX) = 5
        assert len(instrs) == 5

    @pytest.mark.unit
    def test_starts_with_x(self) -> None:
        circ = w_state(3)
        instrs = [i for i in circ.instructions if isinstance(i, Instruction)]
        assert instrs[0].gate.name == "X"

    @pytest.mark.unit
    def test_ry_angles_correct(self) -> None:
        n = 4
        circ = w_state(n)
        instrs = [i for i in circ.instructions if isinstance(i, Instruction)]
        ry_instrs = [i for i in instrs if i.gate.name == "Ry"]
        assert len(ry_instrs) == n - 1
        for k, instr in enumerate(ry_instrs):
            expected = 2.0 * math.asin(math.sqrt(1.0 / (n - k)))
            assert math.isclose(instr.params[0], expected, rel_tol=1e-12)

    @pytest.mark.unit
    def test_n_less_than_2_raises(self) -> None:
        with pytest.raises(CircuitError, match="n >= 2"):
            w_state(1)

    @pytest.mark.unit
    def test_measure_flag(self) -> None:
        circ = w_state(3, measure=True)
        measurements = [i for i in circ.instructions if isinstance(i, Measurement)]
        assert len(measurements) == 3

    @pytest.mark.unit
    def test_qsharp_generation(self) -> None:
        qs = w_state(3).to_qsharp()
        assert "X(" in qs
        assert "Ry(" in qs

    @pytest.mark.unit
    def test_openqasm_generation(self) -> None:
        qasm = w_state(3).to_openqasm()
        assert "x " in qasm
        assert "ry(" in qasm


# ------------------------------------------------------------------
# qft
# ------------------------------------------------------------------


class TestQFT:
    @pytest.mark.unit
    def test_qubit_count(self) -> None:
        assert qft(4).qubit_count() == 4

    @pytest.mark.unit
    def test_1_qubit_is_just_h(self) -> None:
        circ = qft(1)
        instrs = [i for i in circ.instructions if isinstance(i, Instruction)]
        assert len(instrs) == 1
        assert instrs[0].gate.name == "H"

    @pytest.mark.unit
    def test_2_qubit_gate_sequence(self) -> None:
        circ = qft(2)
        instrs = [i for i in circ.instructions if isinstance(i, Instruction)]
        # H(0), controlled-R1(0), H(1), SWAP(0,1)
        assert len(instrs) == 4
        assert instrs[0].gate.name == "H"
        assert instrs[1].gate.name == "R1"
        assert len(instrs[1].controls) == 1
        assert instrs[2].gate.name == "H"
        assert instrs[3].gate.name == "SWAP"

    @pytest.mark.unit
    def test_controlled_r1_angle(self) -> None:
        circ = qft(2)
        instrs = [i for i in circ.instructions if isinstance(i, Instruction)]
        r1_instr = instrs[1]
        assert math.isclose(r1_instr.params[0], math.pi / 2, rel_tol=1e-12)

    @pytest.mark.unit
    def test_3_qubit_has_correct_controlled_rotations(self) -> None:
        circ = qft(3)
        instrs = [i for i in circ.instructions if isinstance(i, Instruction)]
        controlled = [i for i in instrs if len(i.controls) > 0]
        # For n=3: 3 controlled-R1 gates (j=0: k=1,2; j=1: k=2)
        assert len(controlled) == 3

    @pytest.mark.unit
    def test_n_less_than_1_raises(self) -> None:
        with pytest.raises(CircuitError, match="n >= 1"):
            qft(0)

    @pytest.mark.unit
    def test_qsharp_generation(self) -> None:
        qs = qft(3).to_qsharp()
        assert "H(" in qs
        assert "Controlled R1(" in qs

    @pytest.mark.unit
    def test_openqasm_generation(self) -> None:
        qasm = qft(3).to_openqasm()
        assert "h " in qasm


# ------------------------------------------------------------------
# inverse_qft
# ------------------------------------------------------------------


class TestInverseQFT:
    @pytest.mark.unit
    def test_qubit_count(self) -> None:
        assert inverse_qft(4).qubit_count() == 4

    @pytest.mark.unit
    def test_1_qubit_is_just_h(self) -> None:
        circ = inverse_qft(1)
        instrs = [i for i in circ.instructions if isinstance(i, Instruction)]
        assert len(instrs) == 1
        assert instrs[0].gate.name == "H"

    @pytest.mark.unit
    def test_negated_rotation_angles(self) -> None:
        n = 3
        fwd = qft(n)
        inv = inverse_qft(n)
        fwd_r1 = [
            i for i in fwd.instructions
            if isinstance(i, Instruction) and i.gate.name == "R1"
        ]
        inv_r1 = [
            i for i in inv.instructions
            if isinstance(i, Instruction) and i.gate.name == "R1"
        ]
        assert len(fwd_r1) == len(inv_r1)
        fwd_angles = sorted(i.params[0] for i in fwd_r1)
        inv_angles = sorted(-i.params[0] for i in inv_r1)
        for a, b in zip(fwd_angles, inv_angles):
            assert math.isclose(a, b, rel_tol=1e-12)

    @pytest.mark.unit
    def test_n_less_than_1_raises(self) -> None:
        with pytest.raises(CircuitError, match="n >= 1"):
            inverse_qft(0)

    @pytest.mark.unit
    def test_qsharp_generation(self) -> None:
        qs = inverse_qft(3).to_qsharp()
        assert "H(" in qs

    @pytest.mark.unit
    def test_openqasm_generation(self) -> None:
        qasm = inverse_qft(3).to_openqasm()
        assert "h " in qasm


# ------------------------------------------------------------------
# random_circuit
# ------------------------------------------------------------------


class TestRandomCircuit:
    @pytest.mark.unit
    def test_qubit_count(self) -> None:
        circ = random_circuit(5, 3, seed=42)
        assert circ.qubit_count() == 5

    @pytest.mark.unit
    def test_has_instructions(self) -> None:
        circ = random_circuit(4, 5, seed=42)
        assert len(circ.instructions) > 0

    @pytest.mark.unit
    def test_seed_reproducibility(self) -> None:
        c1 = random_circuit(4, 3, seed=123)
        c2 = random_circuit(4, 3, seed=123)
        assert c1.to_qsharp() == c2.to_qsharp()

    @pytest.mark.unit
    def test_different_seeds_differ(self) -> None:
        c1 = random_circuit(4, 5, seed=1)
        c2 = random_circuit(4, 5, seed=2)
        assert c1.to_qsharp() != c2.to_qsharp()

    @pytest.mark.unit
    def test_n_qubits_less_than_1_raises(self) -> None:
        with pytest.raises(CircuitError, match="n_qubits >= 1"):
            random_circuit(0, 3)

    @pytest.mark.unit
    def test_depth_less_than_1_raises(self) -> None:
        with pytest.raises(CircuitError, match="depth >= 1"):
            random_circuit(3, 0)

    @pytest.mark.unit
    def test_single_qubit_no_two_qubit_gates(self) -> None:
        circ = random_circuit(1, 10, seed=42)
        instrs = [i for i in circ.instructions if isinstance(i, Instruction)]
        for instr in instrs:
            assert instr.gate.num_qubits == 1

    @pytest.mark.unit
    def test_qsharp_generation(self) -> None:
        qs = random_circuit(3, 3, seed=42).to_qsharp()
        assert "Qubit" in qs

    @pytest.mark.unit
    def test_openqasm_generation(self) -> None:
        qasm = random_circuit(3, 3, seed=42).to_openqasm()
        assert "OPENQASM" in qasm
