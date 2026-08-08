"""labs.lab6_ztransform

Lab 6: Z-Transforms (Remodeled)

This module provides a console-based Z-transform formatter (lab rubric)
AND a UI-compatible Lab class that displays the computed expression in
LabContainer's Information tab.

Mathematical formula used (finite causal sequence, n=0..N-1):

    X(z) = Σₙ₌₀^∞ x[n] z⁻ⁿ

ROC (finite sequence):
    ROC: Entire z-plane except possibly z=0 or z=∞

Formatting requirements (rubric-critical) are implemented in
`compute_z_transform(sequence)`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple, Optional

import numpy as np

from labs.base_lab import BaseLab


# -------------------------
# Superscript helpers
# -------------------------

_SUPERSCRIPT = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
    "-": "⁻",
}


def _to_superscript(num: int) -> str:
    """Convert an integer to its Unicode superscript representation."""
    return "".join(_SUPERSCRIPT[ch] for ch in str(num))


# -------------------------
# Rubric-critical logic
# -------------------------

def parse_sequence_from_input(user_input: str) -> List[int]:
    """Prompt/parse user input into a list of integers.

    Empty input and any non-numeric token are handled by raising ValueError.
    """
    s = (user_input or "").strip()
    if not s:
        raise ValueError("Empty input")

    tokens = s.split()
    sequence: List[int] = []
    for tok in tokens:
        try:
            sequence.append(int(tok))
        except ValueError as e:
            raise ValueError(f"Invalid token: {tok}") from e

    if not sequence:
        raise ValueError("Empty input")
    return sequence


def _format_xn_set(sequence: List[int]) -> str:
    # Display the input sequence in set notation: x(n) = {1, 2, 3}
    return "{" + ", ".join(str(v) for v in sequence) + "}"


def _format_z_expression(sequence: List[int]) -> str:
    """Build X(z) with strict sign/omission rules using superscript exponents.

    Rules:
      - x(n) == 0: omit term entirely
      - x(n) == 1: show as 'z⁻ⁿ' (or '1' when n=0)
      - x(n) == -1: show as '-z⁻ⁿ' (or '-1' when n=0)
      - x(n) negative (not -1): show as '- [abs]z⁻ⁿ' (or '- [abs]' when n=0)
      - x(n) positive (and not first non-zero term): '+ [value]z⁻ⁿ' (or '+ [value]' when n=0)
      - first non-zero term: no leading '+'
      - z⁰ is omitted (just the coefficient is shown)
      - if all zero => expression '0'
    """
    terms: List[str] = []

    for n, coef in enumerate(sequence):
        if coef == 0:
            continue

        # When n==0, omit z entirely (z⁰ = 1)
        zpow = "" if n == 0 else f"z{_to_superscript(-n)}"

        # First non-zero term: no leading '+'
        if not terms:
            if coef == 1:
                terms.append("1" if n == 0 else zpow)
            elif coef == -1:
                terms.append("-1" if n == 0 else "-" + zpow)
            elif coef < 0:
                terms.append(f"- {abs(coef)}{zpow}")
            else:
                terms.append(f"{coef}{zpow}")
            continue

        # Subsequent terms:
        if coef == 1:
            terms.append("+ " + ("1" if n == 0 else zpow))
        elif coef == -1:
            terms.append("- " + ("1" if n == 0 else zpow))
        elif coef < 0:
            terms.append(f"- {abs(coef)}{zpow}")
        else:
            terms.append(f"+ {coef}{zpow}")

    if not terms:
        return "0"

    return " ".join(terms).strip()


def _format_positive_powers(sequence: List[int]) -> str:
    """Build alternative form with positive powers of z.

    Multiply numerator and denominator by z^(N-1) where N is sequence length.
    Example: [1,2,3,4,5] (length 5) -> multiply by z^4/z^4
    Result: (z⁴ + 2z³ + 3z² + 4z + 5) / z⁴
    """
    if not sequence:
        return "0"

    N = len(sequence)
    max_power = N - 1

    # Build numerator terms
    num_terms: List[str] = []
    for n, coef in enumerate(sequence):
        if coef == 0:
            continue

        power = max_power - n  # positive power

        if power == 0:
            z_part = ""
        elif power == 1:
            z_part = "z"
        else:
            z_part = f"z{_to_superscript(power)}"

        if not num_terms:
            # First term
            if coef == 1:
                num_terms.append("1" if power == 0 else z_part)
            elif coef == -1:
                num_terms.append("-1" if power == 0 else "-" + z_part)
            elif coef < 0:
                num_terms.append(f"- {abs(coef)}{z_part}")
            else:
                num_terms.append(f"{coef}{z_part}")
        else:
            if coef == 1:
                num_terms.append("+ " + ("1" if power == 0 else z_part))
            elif coef == -1:
                num_terms.append("- " + ("1" if power == 0 else z_part))
            elif coef < 0:
                num_terms.append(f"- {abs(coef)}{z_part}")
            else:
                num_terms.append(f"+ {coef}{z_part}")

    if not num_terms:
        return "0"

    numerator = " ".join(num_terms).strip()
    # Only add parentheses if there are multiple non-zero terms in numerator
    non_zero_count = len([c for c in sequence if c != 0])
    if non_zero_count > 1:
        numerator = f"({numerator})"

    if max_power == 0:
        return numerator

    return f"{numerator} / z{_to_superscript(max_power)}"


def compute_z_transform(sequence: List[int]) -> Tuple[str, str]:
    """Compute Z-transform of a finite discrete sequence.

    X(z) = Σ x(n) * z^(-n) for n from -∞ to ∞.
    For a finite sequence, we treat:
      sequence[0] as n=0, sequence[1] as n=1, ... (causal/unilateral)

    Returns:
        (xn_set_notation, xz_expression)
    """
    xn_set = _format_xn_set(sequence)
    xz_expr = _format_z_expression(sequence)
    return xn_set, xz_expr


# -------------------------
# Console program (VS Code terminal)
# -------------------------

def main() -> None:
    # User Input Handling (rubric requirements)
    try:
        user_input = input("Enter a sequence of numbers separated by spaces: ")
        sequence = parse_sequence_from_input(user_input)
    except ValueError:
        print("Error: invalid input. Please enter only integers separated by spaces.")
        return

    # Compute and print with exact rubric formatting
    xn_set, xz_expr = compute_z_transform(sequence)
    alt_form = _format_positive_powers(sequence)

    print(f"Z-transform of x(n) = {xn_set}")
    print(f"X(z) = {xz_expr}")
    print(f"Alternative form (positive powers): X(z) = {alt_form}")
    print("ROC: Entire z-plane except possibly z=0 or z=∞")


# -------------------------
# UI-compatible Lab class
# -------------------------

class Lab6ZTransform(BaseLab):
    """UI lab interface wrapper for Z-transform."""

    def __init__(self):

        super().__init__(
            name="Z-Transform & Pole-Zero",
            description="Compute the (causal/unilateral) Z-transform for a finite sequence and display the formatted X(z) expression.",
        )
        self._sequence_text: str = ""
        self.parameters = {
            "sequence": {
                "type": "text",
                "default": "",
                "value": "",
                "label": "x(n) sequence (space-separated integers)",
            }
        }
        self.results: Dict[str, Any] = {}

    def setup(self) -> Dict[str, Any]:
        self._sequence_text = str(self.parameters["sequence"]["value"])
        return self.parameters

    def update_parameter(self, name: str, value: Any):
        super().update_parameter(name, value)
        if name == "sequence":
            self._sequence_text = str(value)

    def _parse_for_ui(self) -> Optional[List[int]]:
        try:
            return parse_sequence_from_input(self._sequence_text)
        except ValueError:
            return None

    def process(self, **kwargs) -> Tuple[np.ndarray, np.ndarray]:
        # Apply parameter overrides
        for k, v in kwargs.items():
            if k in self.parameters:
                self.update_parameter(k, v)

        seq = self._parse_for_ui()
        roc_text = "ROC: Entire z-plane except possibly z=0 or z=∞"

        # Always provide valid time-domain data for UI
        if seq is None:
            seq = [0]

        xn_set, xz_expr = compute_z_transform(seq)
        xz_text = f"X(z) = {xz_expr}"

        # Build alternative positive-power form
        alt_form = _format_positive_powers(seq)
        alt_text = f"Alternative form (positive powers): X(z) = {alt_form}"

        # Step-by-step breakdown
        steps: List[Dict[str, Any]] = []
        for n, x_n in enumerate(seq):
            included = (x_n != 0)
            if included:
                # Pretty term representation with superscripts
                # Omit z when n==0 (z⁰ = 1)
                z_part = "" if n == 0 else f"z{_to_superscript(-n)}"
                if x_n == 1:
                    term_pretty = "1" if n == 0 else f"z{_to_superscript(-n)}"
                elif x_n == -1:
                    term_pretty = "-1" if n == 0 else f"-z{_to_superscript(-n)}"
                elif x_n > 1:
                    term_pretty = f"{x_n}{z_part}"
                else:  # x_n < -1
                    term_pretty = f"-{abs(x_n)}{z_part}"

                term_full = f"{x_n}·z{_to_superscript(-n)} = {term_pretty}"
                reason = "Non-zero coefficient"
            else:
                term_full = f"{x_n}·z{_to_superscript(-n)} = 0"
                reason = "Zero coefficient omitted"

            steps.append(
                {
                    "n": n,
                    "x_n": x_n,
                    "term": term_full,
                    "included": included,
                    "reason": reason,
                }
            )

        # Build detailed explanation
        N = len(seq)
        explanation_lines = [
            f"Given the finite causal sequence x(n) = {xn_set} with length N = {N}.",
            "",
            "The Z-transform of a discrete-time signal x[n] is defined as:",
            "    X(z) = Σₙ₌₀^∞ x[n] · z⁻ⁿ",
            "",
            "For a finite sequence of length N, this becomes:",
            "    X(z) = x[0]·z⁰ + x[1]·z⁻¹ + x[2]·z⁻² + ... + x[N-1]·z⁻⁽ᴺ⁻¹⁾",
            "",
            "Substituting the sequence values:",
        ]

        # Build substitution line
        sub_terms = []
        for n, x_n in enumerate(seq):
            if x_n != 0:
                sub_terms.append(f"{x_n}·z{_to_superscript(-n)}")
        if sub_terms:
            explanation_lines.append("    X(z) = " + " + ".join(sub_terms))
        explanation_lines.append("")

        # Add simplification notes
        explanation_lines.append("Simplifying (note: z⁰ = 1, so the first term becomes just the coefficient):")
        explanation_lines.append(f"    X(z) = {xz_expr}")
        explanation_lines.append("")
        explanation_lines.append("Alternative Form (positive powers of z):")
        explanation_lines.append(f"    Multiply numerator and denominator by z^{N-1}:")
        explanation_lines.append(f"    X(z) = {alt_form}")
        explanation_lines.append("")
        explanation_lines.append("Region of Convergence (ROC):")
        explanation_lines.append(f"    {roc_text}")
        explanation_lines.append("")
        explanation_lines.append("For a finite causal sequence, the ROC is the entire z-plane")
        explanation_lines.append("except possibly z = 0 (if there are negative powers) or z = ∞.")

        explanation = "\n".join(explanation_lines)

        self.results = {
            "steps": steps,
            "roc": roc_text,
            "formula": "X(z) = Σₙ₌₀^∞ x[n] z⁻ⁿ",
            "alternative_form": alt_form,
            "explanation": explanation,
            "display": {
                "title": f"Z-transform of x(n) = {xn_set}",
                "xz": xz_text,
                "roc": roc_text,
                "formula": "X(z) = Σₙ₌₀^∞ x[n] z⁻ⁿ",
                "alternative": alt_text,
                "explanation": explanation,
                "steps": steps,
            },
            "final_answer": f"X(z) = {xz_expr}\n{alt_text}\n{roc_text}",
        }

        time_array = np.arange(len(seq))
        signal_array = np.array(seq, dtype=float)
        return time_array, signal_array

    def get_frequency_domain(self, signal: np.ndarray, sampling_rate: float) -> Tuple[np.ndarray, np.ndarray]:
        # Use the most recently computed expression/sequence.
        # Re-parse from UI parameter to keep this method self-contained.
        seq = self._parse_for_ui()
        if not seq:
            return np.array([]), np.array([])

        # Plot in the frequency domain using ω (rad/sample): X(e^{jω}) = Σ x[n] e^{-jω n}
        omega = np.linspace(-np.pi, np.pi, 1024)
        X = np.zeros_like(omega, dtype=complex)
        for n, x_n in enumerate(seq):
            if x_n == 0:
                continue
            X += x_n * np.exp(-1j * omega * n)

        magnitude = np.abs(X)
        return omega, magnitude

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


if __name__ == "__main__":
    main()