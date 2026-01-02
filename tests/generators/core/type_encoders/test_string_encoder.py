"""Tests for StringEncoder."""

import pytest

from protocol_codegen.generators.core.type_encoders import StringEncoder
from protocol_codegen.generators.protocols import (
    Serial8EncodingStrategy,
    SysExEncodingStrategy,
)


class TestStringEncoderSerial8:
    """Test StringEncoder with Serial8 strategy."""

    @pytest.fixture
    def encoder(self) -> StringEncoder:
        return StringEncoder(Serial8EncodingStrategy())

    def test_supported_types(self, encoder: StringEncoder) -> None:
        assert encoder.supported_types() == ("string",)

    def test_string_spec(self, encoder: StringEncoder) -> None:
        spec = encoder.get_method_spec("string", "Variable length string")
        assert spec.type_name == "string"
        assert spec.method_name == "String"
        assert spec.byte_count == -1  # Variable
        assert len(spec.byte_writes) == 0  # Special handling
        # Serial8: 8-bit masks
        assert "LENGTH_MASK=0xFF" in spec.preamble
        assert "CHAR_MASK=0xFF" in spec.preamble
        assert "MAX_LENGTH=255" in spec.preamble

    def test_unsupported_type_raises(self, encoder: StringEncoder) -> None:
        with pytest.raises(ValueError, match="Unsupported type"):
            encoder.get_method_spec("uint8", "not a string")


class TestStringEncoderSysEx:
    """Test StringEncoder with SysEx strategy."""

    @pytest.fixture
    def encoder(self) -> StringEncoder:
        return StringEncoder(SysExEncodingStrategy())

    def test_string_uses_7bit_masks(self, encoder: StringEncoder) -> None:
        spec = encoder.get_method_spec("string", "Variable length string")
        # SysEx: 7-bit masks
        assert "LENGTH_MASK=0x7F" in spec.preamble
        assert "CHAR_MASK=0x7F" in spec.preamble
        assert "MAX_LENGTH=127" in spec.preamble
