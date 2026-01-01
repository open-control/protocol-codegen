"""Tests for IntegerEncoder."""

import pytest

from protocol_codegen.generators.common.encoding import (
    Serial8EncodingStrategy,
    SysExEncodingStrategy,
)
from protocol_codegen.generators.common.type_encoders import IntegerEncoder


class TestIntegerEncoderSerial8:
    """Test IntegerEncoder with Serial8 strategy."""

    @pytest.fixture
    def encoder(self) -> IntegerEncoder:
        return IntegerEncoder(Serial8EncodingStrategy())

    def test_supported_types(self, encoder: IntegerEncoder) -> None:
        types = encoder.supported_types()
        assert "uint8" in types
        assert "int8" in types
        assert "uint16" in types
        assert "int16" in types
        assert "uint32" in types
        assert "int32" in types

    def test_uint8_spec(self, encoder: IntegerEncoder) -> None:
        spec = encoder.get_method_spec("uint8", "8-bit unsigned")
        assert spec.byte_count == 1
        assert len(spec.byte_writes) == 1
        assert spec.byte_writes[0].expression == "val & 0xFF"
        assert spec.needs_signed_cast is False

    def test_uint16_spec(self, encoder: IntegerEncoder) -> None:
        spec = encoder.get_method_spec("uint16", "16-bit unsigned")
        assert spec.byte_count == 2
        assert len(spec.byte_writes) == 2
        # Little-endian: low byte first
        assert "val & 0xFF" in spec.byte_writes[0].expression
        assert "(val >> 8)" in spec.byte_writes[1].expression

    def test_uint32_spec(self, encoder: IntegerEncoder) -> None:
        spec = encoder.get_method_spec("uint32", "32-bit unsigned")
        assert spec.byte_count == 4
        assert len(spec.byte_writes) == 4
        assert "(val >> 24)" in spec.byte_writes[3].expression

    def test_int16_needs_signed_cast(self, encoder: IntegerEncoder) -> None:
        spec = encoder.get_method_spec("int16", "16-bit signed")
        assert spec.needs_signed_cast is True

    def test_int8_no_signed_cast(self, encoder: IntegerEncoder) -> None:
        # Single byte doesn't need cast
        spec = encoder.get_method_spec("int8", "8-bit signed")
        assert spec.needs_signed_cast is False

    def test_unsupported_type_raises(self, encoder: IntegerEncoder) -> None:
        with pytest.raises(ValueError, match="Unsupported type"):
            encoder.get_method_spec("float32", "not an integer")


class TestIntegerEncoderSysEx:
    """Test IntegerEncoder with SysEx strategy."""

    @pytest.fixture
    def encoder(self) -> IntegerEncoder:
        return IntegerEncoder(SysExEncodingStrategy())

    def test_uint16_uses_7bit(self, encoder: IntegerEncoder) -> None:
        spec = encoder.get_method_spec("uint16", "16-bit unsigned")
        # SysEx: 3 bytes, 7-bit encoding
        assert spec.byte_count == 3
        assert len(spec.byte_writes) == 3
        assert "0x7F" in spec.byte_writes[0].expression

    def test_uint32_uses_7bit(self, encoder: IntegerEncoder) -> None:
        spec = encoder.get_method_spec("uint32", "32-bit unsigned")
        # SysEx: 5 bytes
        assert spec.byte_count == 5
        assert len(spec.byte_writes) == 5
