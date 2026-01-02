"""Tests for BoolEncoder."""

import pytest

from protocol_codegen.generators.core.type_encoders import BoolEncoder
from protocol_codegen.generators.protocols import (
    Serial8EncodingStrategy,
    SysExEncodingStrategy,
)


class TestBoolEncoderSerial8:
    """Test BoolEncoder with Serial8 strategy."""

    @pytest.fixture
    def encoder(self) -> BoolEncoder:
        return BoolEncoder(Serial8EncodingStrategy())

    def test_supported_types(self, encoder: BoolEncoder) -> None:
        assert encoder.supported_types() == ("bool",)

    def test_bool_spec(self, encoder: BoolEncoder) -> None:
        spec = encoder.get_method_spec("bool", "Boolean value")
        assert spec.type_name == "bool"
        assert spec.method_name == "Bool"
        assert spec.byte_count == 1
        assert len(spec.byte_writes) == 1
        # Serial8: true=0x01, false=0x00
        assert "0x01" in spec.byte_writes[0].expression
        assert "0x00" in spec.byte_writes[0].expression

    def test_unsupported_type_raises(self, encoder: BoolEncoder) -> None:
        with pytest.raises(ValueError, match="Unsupported type"):
            encoder.get_method_spec("uint8", "not a bool")


class TestBoolEncoderSysEx:
    """Test BoolEncoder with SysEx strategy."""

    @pytest.fixture
    def encoder(self) -> BoolEncoder:
        return BoolEncoder(SysExEncodingStrategy())

    def test_bool_spec(self, encoder: BoolEncoder) -> None:
        spec = encoder.get_method_spec("bool", "Boolean value")
        # SysEx: same as Serial8 (true=0x01, false=0x00)
        assert "0x01" in spec.byte_writes[0].expression
        assert "0x00" in spec.byte_writes[0].expression
