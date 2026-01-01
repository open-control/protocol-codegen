"""Tests for encoding strategies."""

import pytest

from protocol_codegen.generators.common.encoding import (
    Serial8EncodingStrategy,
    SysExEncodingStrategy,
    get_encoding_strategy,
)


class TestSerial8Strategy:
    """Test Serial8 8-bit encoding strategy."""

    @pytest.fixture
    def strategy(self) -> Serial8EncodingStrategy:
        return Serial8EncodingStrategy()

    def test_name(self, strategy: Serial8EncodingStrategy) -> None:
        assert strategy.name == "Serial8"

    def test_description(self, strategy: Serial8EncodingStrategy) -> None:
        assert strategy.description == "8-bit binary"

    def test_bool_size(self, strategy: Serial8EncodingStrategy) -> None:
        assert strategy.get_encoded_size("bool", 1) == 1

    def test_uint8_size(self, strategy: Serial8EncodingStrategy) -> None:
        assert strategy.get_encoded_size("uint8", 1) == 1

    def test_int8_size(self, strategy: Serial8EncodingStrategy) -> None:
        assert strategy.get_encoded_size("int8", 1) == 1

    def test_norm8_size(self, strategy: Serial8EncodingStrategy) -> None:
        assert strategy.get_encoded_size("norm8", 1) == 1

    def test_uint16_size(self, strategy: Serial8EncodingStrategy) -> None:
        assert strategy.get_encoded_size("uint16", 2) == 2

    def test_int16_size(self, strategy: Serial8EncodingStrategy) -> None:
        assert strategy.get_encoded_size("int16", 2) == 2

    def test_norm16_size(self, strategy: Serial8EncodingStrategy) -> None:
        assert strategy.get_encoded_size("norm16", 2) == 2

    def test_uint32_size(self, strategy: Serial8EncodingStrategy) -> None:
        assert strategy.get_encoded_size("uint32", 4) == 4

    def test_int32_size(self, strategy: Serial8EncodingStrategy) -> None:
        assert strategy.get_encoded_size("int32", 4) == 4

    def test_float32_size(self, strategy: Serial8EncodingStrategy) -> None:
        assert strategy.get_encoded_size("float32", 4) == 4

    def test_string_max_size(self, strategy: Serial8EncodingStrategy) -> None:
        # 1 byte length prefix + max_length chars
        assert strategy.get_string_max_encoded_size(32) == 33
        assert strategy.get_string_max_encoded_size(255) == 256

    def test_string_min_size(self, strategy: Serial8EncodingStrategy) -> None:
        # Empty string = just length prefix
        assert strategy.get_string_min_encoded_size() == 1


class TestSysExStrategy:
    """Test SysEx 7-bit MIDI-safe encoding strategy."""

    @pytest.fixture
    def strategy(self) -> SysExEncodingStrategy:
        return SysExEncodingStrategy()

    def test_name(self, strategy: SysExEncodingStrategy) -> None:
        assert strategy.name == "SysEx"

    def test_description(self, strategy: SysExEncodingStrategy) -> None:
        assert strategy.description == "7-bit MIDI-safe"

    def test_bool_size(self, strategy: SysExEncodingStrategy) -> None:
        assert strategy.get_encoded_size("bool", 1) == 1

    def test_uint8_size_no_expansion(self, strategy: SysExEncodingStrategy) -> None:
        # uint8 values are < 128, so no expansion needed
        assert strategy.get_encoded_size("uint8", 1) == 1

    def test_int8_size_no_expansion(self, strategy: SysExEncodingStrategy) -> None:
        assert strategy.get_encoded_size("int8", 1) == 1

    def test_norm8_size_no_expansion(self, strategy: SysExEncodingStrategy) -> None:
        assert strategy.get_encoded_size("norm8", 1) == 1

    def test_uint16_size_expansion(self, strategy: SysExEncodingStrategy) -> None:
        # 16-bit -> 3 bytes for 7-bit encoding
        assert strategy.get_encoded_size("uint16", 2) == 3

    def test_int16_size_expansion(self, strategy: SysExEncodingStrategy) -> None:
        assert strategy.get_encoded_size("int16", 2) == 3

    def test_norm16_size_expansion(self, strategy: SysExEncodingStrategy) -> None:
        assert strategy.get_encoded_size("norm16", 2) == 3

    def test_uint32_size_expansion(self, strategy: SysExEncodingStrategy) -> None:
        # 32-bit -> 5 bytes for 7-bit encoding
        assert strategy.get_encoded_size("uint32", 4) == 5

    def test_int32_size_expansion(self, strategy: SysExEncodingStrategy) -> None:
        assert strategy.get_encoded_size("int32", 4) == 5

    def test_float32_size_expansion(self, strategy: SysExEncodingStrategy) -> None:
        assert strategy.get_encoded_size("float32", 4) == 5

    def test_string_max_size(self, strategy: SysExEncodingStrategy) -> None:
        # String chars are already 7-bit safe (ASCII)
        assert strategy.get_string_max_encoded_size(32) == 33
        assert strategy.get_string_max_encoded_size(255) == 256

    def test_string_min_size(self, strategy: SysExEncodingStrategy) -> None:
        assert strategy.get_string_min_encoded_size() == 1


class TestEncodingStrategyFactory:
    """Test get_encoding_strategy factory function."""

    def test_get_serial8_strategy(self) -> None:
        strategy = get_encoding_strategy("serial8")
        assert isinstance(strategy, Serial8EncodingStrategy)

    def test_get_sysex_strategy(self) -> None:
        strategy = get_encoding_strategy("sysex")
        assert isinstance(strategy, SysExEncodingStrategy)

    def test_unknown_protocol_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown protocol"):
            get_encoding_strategy("unknown")


class TestEncodingStrategyDifferences:
    """Test key differences between Serial8 and SysEx encoding."""

    def test_16bit_differs(self) -> None:
        """16-bit types expand in SysEx but not in Serial8."""
        serial8 = Serial8EncodingStrategy()
        sysex = SysExEncodingStrategy()

        for type_name in ("uint16", "int16", "norm16"):
            assert serial8.get_encoded_size(type_name, 2) == 2
            assert sysex.get_encoded_size(type_name, 2) == 3

    def test_32bit_differs(self) -> None:
        """32-bit types expand in SysEx but not in Serial8."""
        serial8 = Serial8EncodingStrategy()
        sysex = SysExEncodingStrategy()

        for type_name in ("uint32", "int32", "float32"):
            assert serial8.get_encoded_size(type_name, 4) == 4
            assert sysex.get_encoded_size(type_name, 4) == 5

    def test_8bit_same(self) -> None:
        """8-bit types are the same in both protocols."""
        serial8 = Serial8EncodingStrategy()
        sysex = SysExEncodingStrategy()

        for type_name in ("bool", "uint8", "int8", "norm8"):
            assert serial8.get_encoded_size(type_name, 1) == 1
            assert sysex.get_encoded_size(type_name, 1) == 1
