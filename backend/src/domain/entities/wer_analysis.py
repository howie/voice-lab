"""WER/CER Analysis domain entity for STT evaluation.

Feature: 003-stt-testing-module
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class ErrorType(StrEnum):
    """Type of error rate calculation."""

    WER = "WER"  # Word Error Rate (for English)
    CER = "CER"  # Character Error Rate (for CJK languages)


class AlignmentOperation(StrEnum):
    """Alignment operation types."""

    MATCH = "match"
    SUBSTITUTE = "substitute"
    INSERT = "insert"
    DELETE = "delete"


@dataclass
class AlignmentItem:
    """Single alignment item between reference and hypothesis."""

    ref: str | None  # Reference token (None for insertions)
    hyp: str | None  # Hypothesis token (None for deletions)
    op: AlignmentOperation


@dataclass
class WERAnalysis:
    """WER/CER analysis result entity.

    Stores the error rate calculation result for a transcription.
    """

    result_id: UUID
    ground_truth_id: UUID
    error_rate: float
    error_type: ErrorType
    insertions: int
    deletions: int
    substitutions: int
    total_reference: int
    id: UUID = field(default_factory=uuid4)
    alignment: list[AlignmentItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate analysis parameters."""
        if self.error_rate < 0:
            raise ValueError("error_rate cannot be negative")
        if self.insertions < 0 or self.deletions < 0 or self.substitutions < 0:
            raise ValueError("Error counts cannot be negative")
        if self.total_reference < 0:
            raise ValueError("total_reference cannot be negative")

    @property
    def total_errors(self) -> int:
        """Get total number of errors."""
        return self.insertions + self.deletions + self.substitutions

    @property
    def accuracy(self) -> float:
        """Get accuracy (1 - error_rate), capped at 0."""
        return max(0.0, 1.0 - self.error_rate)

    @property
    def error_rate_percentage(self) -> float:
        """Get error rate as percentage."""
        return self.error_rate * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "result_id": str(self.result_id),
            "ground_truth_id": str(self.ground_truth_id),
            "error_rate": self.error_rate,
            "error_type": self.error_type.value,
            "insertions": self.insertions,
            "deletions": self.deletions,
            "substitutions": self.substitutions,
            "total_reference": self.total_reference,
            "alignment": [
                {"ref": item.ref, "hyp": item.hyp, "op": item.op.value} for item in self.alignment
            ],
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_calculation(
        cls,
        result_id: UUID,
        ground_truth_id: UUID,
        reference: str,
        hypothesis: str,
        language: str,
    ) -> "WERAnalysis":
        """Create WERAnalysis from reference and hypothesis texts.

        Auto-selects WER or CER based on language.
        """
        from src.domain.services.wer_calculator import (
            calculate_alignment,
            calculate_cer,
            calculate_wer,
        )

        # CJK languages use CER, others use WER
        cjk_languages = {"zh-TW", "zh-CN", "ja-JP", "ko-KR"}
        is_cjk = language in cjk_languages

        if is_cjk:
            error_rate = calculate_cer(reference, hypothesis)
            error_type = ErrorType.CER
            # Character-level comparison
            ref_tokens = list(reference.replace(" ", ""))
            hyp_tokens = list(hypothesis.replace(" ", ""))
        else:
            error_rate = calculate_wer(reference, hypothesis)
            error_type = ErrorType.WER
            # Word-level comparison
            ref_tokens = reference.strip().split()
            hyp_tokens = hypothesis.strip().split()

        # Calculate alignment and error counts
        alignment_result, ins, dels, subs = calculate_alignment(ref_tokens, hyp_tokens)

        alignment_items = [
            AlignmentItem(ref=item[0], hyp=item[1], op=AlignmentOperation(item[2]))
            for item in alignment_result
        ]

        return cls(
            result_id=result_id,
            ground_truth_id=ground_truth_id,
            error_rate=error_rate,
            error_type=error_type,
            insertions=ins,
            deletions=dels,
            substitutions=subs,
            total_reference=len(ref_tokens),
            alignment=alignment_items,
        )
