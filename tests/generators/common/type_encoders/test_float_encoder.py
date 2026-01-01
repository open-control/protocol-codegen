"""Tests for FloatEncoder."""

import pytest

from protocol_codegen.generators.common.encoding import (
    Serial8EncodingStrategy,
    SysExEncodingStrategy,
)
from protocol_codegen.generators.common.type_encoders import FloatEncoder


class TestFloatEncoderSerial8:
    """Test FloatEncoder with Serial8 strategy."""

    @pytest.fixture
    def encoder(self) -> FloatEncoder:
        return FloatEncoder(Serial8EncodingStrategy())

    def test_supported_types(self, encoder: FloatEncoder) -> None:
        assert encoder.supported_types() == ("float32",)

    def test_float32_spec(self, encoder: FloatEncoder) -> None:
        spec = encoder.get_method_spec("float32", "IEEE 754 float")
        assert spec.type_name == "float32"
        assert spec.method_name == "Float32"
        assert spec.byte_count == 4
        assert len(spec.byte_writes) == 4
        # Uses 'bits' variable (from bitcast)
        assert "bits" in spec.byte_writes[0].expression
        assert spec.preamble == "FLOAT_BITCAST"

    def test_unsupported_type_raises(self, encoder: FloatEncoder) -> None:
        with pytest.raises(ValueError, match="Unsupported type"):
            encoder.get_method_spec("uint32", "not a float")


class TestFloatEncoderSysEx:
    """Test FloatEncoder with SysEx strategy."""

    @pytest.fixture
    def encoder(self) -> FloatEncoder:
        return FloatEncoder(SysExEncodingStrategy())

    def test_float32_uses_7bit(self, encoder: FloatEncoder) -> None:
        spec = encoder.get_method_spec("float32", "IEEE 754 float")
        # SysEx: 5 bytes for 32-bit value
        assert spec.byte_count == 5
        assert len(spec.byte_writes) == 5
        assert "0x7F" in spec.byte_writes[0].expression
