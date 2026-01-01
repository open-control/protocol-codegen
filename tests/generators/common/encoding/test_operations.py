"""Tests for encoding operations."""

import pytest

from protocol_codegen.generators.common.encoding.operations import (
    ByteWriteOp,
    MethodSpec,
)


class TestByteWriteOp:
    """Tests for ByteWriteOp dataclass."""

    def test_create(self) -> None:
        op = ByteWriteOp(index=0, expression="val & 0xFF")
        assert op.index == 0
        assert op.expression == "val & 0xFF"

    def test_immutable(self) -> None:
        op = ByteWriteOp(index=0, expression="val & 0xFF")
        with pytest.raises(AttributeError):
            op.index = 1  # type: ignore[misc]

    def test_equality(self) -> None:
        op1 = ByteWriteOp(index=0, expression="val & 0xFF")
        op2 = ByteWriteOp(index=0, expression="val & 0xFF")
        assert op1 == op2

    def test_hash(self) -> None:
        op = ByteWriteOp(index=0, expression="val & 0xFF")
        # Should be hashable (frozen dataclass)
        assert hash(op) is not None


class TestMethodSpec:
    """Tests for MethodSpec dataclass."""

    def test_create_simple(self) -> None:
        spec = MethodSpec(
            type_name="uint8",
            method_name="Uint8",
            param_type="uint8",
            byte_count=1,
            byte_writes=(ByteWriteOp(0, "val & 0xFF"),),
            doc_comment="8-bit unsigned integer",
        )
        assert spec.type_name == "uint8"
        assert spec.method_name == "Uint8"
        assert spec.byte_count == 1
        assert len(spec.byte_writes) == 1
        assert spec.preamble is None
        assert spec.needs_signed_cast is False

    def test_create_with_preamble(self) -> None:
        spec = MethodSpec(
            type_name="float32",
            method_name="Float32",
            param_type="float32",
            byte_count=4,
            byte_writes=(
                ByteWriteOp(0, "bits & 0xFF"),
                ByteWriteOp(1, "(bits >> 8) & 0xFF"),
                ByteWriteOp(2, "(bits >> 16) & 0xFF"),
                ByteWriteOp(3, "(bits >> 24) & 0xFF"),
            ),
            doc_comment="IEEE 754 float",
            preamble="uint32_t bits; memcpy(&bits, &val, sizeof(float));",
        )
        assert spec.preamble is not None
        assert "memcpy" in spec.preamble
        assert len(spec.byte_writes) == 4

    def test_create_with_signed_cast(self) -> None:
        spec = MethodSpec(
            type_name="int16",
            method_name="Int16",
            param_type="int16",
            byte_count=2,
            byte_writes=(
                ByteWriteOp(0, "val & 0xFF"),
                ByteWriteOp(1, "(val >> 8) & 0xFF"),
            ),
            doc_comment="16-bit signed integer",
            needs_signed_cast=True,
        )
        assert spec.needs_signed_cast is True

    def test_variable_length(self) -> None:
        spec = MethodSpec(
            type_name="string",
            method_name="String",
            param_type="string",
            byte_count=-1,  # Variable length
            byte_writes=(),  # Special handling
            doc_comment="Variable length string",
        )
        assert spec.byte_count == -1
        assert len(spec.byte_writes) == 0

    def test_immutable(self) -> None:
        spec = MethodSpec(
            type_name="uint8",
            method_name="Uint8",
            param_type="uint8",
            byte_count=1,
            byte_writes=(ByteWriteOp(0, "val & 0xFF"),),
            doc_comment="8-bit unsigned",
        )
        with pytest.raises(AttributeError):
            spec.byte_count = 2  # type: ignore[misc]

    def test_equality(self) -> None:
        spec1 = MethodSpec(
            type_name="uint8",
            method_name="Uint8",
            param_type="uint8",
            byte_count=1,
            byte_writes=(ByteWriteOp(0, "val & 0xFF"),),
            doc_comment="8-bit unsigned",
        )
        spec2 = MethodSpec(
            type_name="uint8",
            method_name="Uint8",
            param_type="uint8",
            byte_count=1,
            byte_writes=(ByteWriteOp(0, "val & 0xFF"),),
            doc_comment="8-bit unsigned",
        )
        assert spec1 == spec2
