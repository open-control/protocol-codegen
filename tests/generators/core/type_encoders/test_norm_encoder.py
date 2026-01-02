"""Tests for NormEncoder."""

import pytest

from protocol_codegen.generators.core.type_encoders import NormEncoder
from protocol_codegen.generators.protocols import (
    Serial8EncodingStrategy,
    SysExEncodingStrategy,
)


class TestNormEncoderSerial8:
    """Test NormEncoder with Serial8 strategy."""

    @pytest.fixture
    def encoder(self) -> NormEncoder:
        return NormEncoder(Serial8EncodingStrategy())

    def test_supported_types(self, encoder: NormEncoder) -> None:
        types = encoder.supported_types()
        assert "norm8" in types
        assert "norm16" in types

    def test_norm8_spec(self, encoder: NormEncoder) -> None:
        spec = encoder.get_method_spec("norm8", "Normalized 8-bit")
        assert spec.type_name == "norm8"
        assert spec.method_name == "Norm8"
        assert spec.byte_count == 1
        assert len(spec.byte_writes) == 1
        # Serial8: max 255
        assert "NORM_SCALE=255" in spec.preamble
        assert "0xFF" in spec.byte_writes[0].expression

    def test_norm16_spec(self, encoder: NormEncoder) -> None:
        spec = encoder.get_method_spec("norm16", "Normalized 16-bit")
        assert spec.byte_count == 2
        assert len(spec.byte_writes) == 2
        assert "NORM_SCALE=65535" in spec.preamble

    def test_unsupported_type_raises(self, encoder: NormEncoder) -> None:
        with pytest.raises(ValueError, match="Unsupported type"):
            encoder.get_method_spec("float32", "not a norm")


class TestNormEncoderSysEx:
    """Test NormEncoder with SysEx strategy."""

    @pytest.fixture
    def encoder(self) -> NormEncoder:
        return NormEncoder(SysExEncodingStrategy())

    def test_norm8_uses_127_max(self, encoder: NormEncoder) -> None:
        spec = encoder.get_method_spec("norm8", "Normalized 8-bit")
        # SysEx: max 127, mask 0x7F
        assert "NORM_SCALE=127" in spec.preamble
        assert "0x7F" in spec.byte_writes[0].expression

    def test_norm16_uses_7bit(self, encoder: NormEncoder) -> None:
        spec = encoder.get_method_spec("norm16", "Normalized 16-bit")
        # SysEx: 3 bytes for 16-bit value, full 16-bit range
        assert spec.byte_count == 3
        assert "NORM_SCALE=65535" in spec.preamble
        # Uses 7-bit encoding
        assert "0x7F" in spec.byte_writes[0].expression
