"""Tests for PayloadCalculator."""

import pytest

from protocol_codegen.core.enum_def import EnumDef
from protocol_codegen.core.field import CompositeField, EnumField, PrimitiveField, Type
from protocol_codegen.core.loader import TypeRegistry
from protocol_codegen.generators.core.payload import PayloadCalculator
from protocol_codegen.generators.protocols import (
    BinaryEncodingStrategy,
    SysExEncodingStrategy,
)


@pytest.fixture
def type_registry() -> TypeRegistry:
    """Create a TypeRegistry with builtin types."""
    registry = TypeRegistry()
    registry.load_builtins()
    return registry


@pytest.fixture
def binary_calculator(type_registry: TypeRegistry) -> PayloadCalculator:
    """Create PayloadCalculator with Binary strategy."""
    return PayloadCalculator(BinaryEncodingStrategy(), type_registry)


@pytest.fixture
def sysex_calculator(type_registry: TypeRegistry) -> PayloadCalculator:
    """Create PayloadCalculator with SysEx strategy."""
    return PayloadCalculator(SysExEncodingStrategy(), type_registry)


class TestPayloadCalculatorBinary:
    """Test PayloadCalculator with Binary encoding."""

    def test_empty_fields(self, binary_calculator: PayloadCalculator) -> None:
        """Empty message has zero payload."""
        assert binary_calculator.calculate_max_payload_size([], 32) == 0
        assert binary_calculator.calculate_min_payload_size([], 32) == 0

    def test_single_bool(self, binary_calculator: PayloadCalculator) -> None:
        """Bool field is 1 byte."""
        fields = [PrimitiveField(name="flag", type_name=Type.BOOL)]
        assert binary_calculator.calculate_max_payload_size(fields, 32) == 1
        assert binary_calculator.calculate_min_payload_size(fields, 32) == 1

    def test_single_uint8(self, binary_calculator: PayloadCalculator) -> None:
        """uint8 field is 1 byte."""
        fields = [PrimitiveField(name="value", type_name=Type.UINT8)]
        assert binary_calculator.calculate_max_payload_size(fields, 32) == 1
        assert binary_calculator.calculate_min_payload_size(fields, 32) == 1

    def test_single_uint16(self, binary_calculator: PayloadCalculator) -> None:
        """uint16 field is 2 bytes in Binary."""
        fields = [PrimitiveField(name="value", type_name=Type.UINT16)]
        assert binary_calculator.calculate_max_payload_size(fields, 32) == 2
        assert binary_calculator.calculate_min_payload_size(fields, 32) == 2

    def test_single_uint32(self, binary_calculator: PayloadCalculator) -> None:
        """uint32 field is 4 bytes in Binary."""
        fields = [PrimitiveField(name="value", type_name=Type.UINT32)]
        assert binary_calculator.calculate_max_payload_size(fields, 32) == 4
        assert binary_calculator.calculate_min_payload_size(fields, 32) == 4

    def test_single_float32(self, binary_calculator: PayloadCalculator) -> None:
        """float32 field is 4 bytes in Binary."""
        fields = [PrimitiveField(name="value", type_name=Type.FLOAT32)]
        assert binary_calculator.calculate_max_payload_size(fields, 32) == 4
        assert binary_calculator.calculate_min_payload_size(fields, 32) == 4

    def test_string_field(self, binary_calculator: PayloadCalculator) -> None:
        """String field: 1 byte prefix + max_length for max, 1 byte for min."""
        fields = [PrimitiveField(name="text", type_name=Type.STRING)]
        assert binary_calculator.calculate_max_payload_size(fields, 32) == 33  # 1 + 32
        assert binary_calculator.calculate_min_payload_size(fields, 32) == 1  # Empty string

    def test_fixed_array(self, binary_calculator: PayloadCalculator) -> None:
        """Fixed array: count byte + (size * count)."""
        fields = [PrimitiveField(name="values", type_name=Type.UINT8, array=4)]
        # Max: 1 (count) + 4 * 1 (elements) = 5
        assert binary_calculator.calculate_max_payload_size(fields, 32) == 5
        # Min: 1 (count byte only, 0 elements)
        assert binary_calculator.calculate_min_payload_size(fields, 32) == 1

    def test_dynamic_array(self, binary_calculator: PayloadCalculator) -> None:
        """Dynamic array: same as fixed array (count byte + elements)."""
        fields = [PrimitiveField(name="values", type_name=Type.UINT8, array=4, dynamic=True)]
        assert binary_calculator.calculate_max_payload_size(fields, 32) == 5
        assert binary_calculator.calculate_min_payload_size(fields, 32) == 1

    def test_multiple_fields(self, binary_calculator: PayloadCalculator) -> None:
        """Multiple fields sum up correctly."""
        fields = [
            PrimitiveField(name="id", type_name=Type.UINT8),
            PrimitiveField(name="value", type_name=Type.UINT16),
            PrimitiveField(name="flag", type_name=Type.BOOL),
        ]
        # 1 + 2 + 1 = 4
        assert binary_calculator.calculate_max_payload_size(fields, 32) == 4
        assert binary_calculator.calculate_min_payload_size(fields, 32) == 4

    def test_name_prefix_size(self, binary_calculator: PayloadCalculator) -> None:
        """Name prefix adds to payload size."""
        fields = [PrimitiveField(name="value", type_name=Type.UINT8)]
        # With name prefix of 10 bytes
        assert binary_calculator.calculate_max_payload_size(fields, 32, name_prefix_size=10) == 11
        assert binary_calculator.calculate_min_payload_size(fields, 32, name_prefix_size=10) == 11


class TestPayloadCalculatorSysEx:
    """Test PayloadCalculator with SysEx encoding (7-bit expansion)."""

    def test_uint8_no_expansion(self, sysex_calculator: PayloadCalculator) -> None:
        """uint8 is 1 byte (no expansion needed, values < 128)."""
        fields = [PrimitiveField(name="value", type_name=Type.UINT8)]
        assert sysex_calculator.calculate_max_payload_size(fields, 32) == 1

    def test_uint16_expansion(self, sysex_calculator: PayloadCalculator) -> None:
        """uint16 expands from 2 to 3 bytes in SysEx."""
        fields = [PrimitiveField(name="value", type_name=Type.UINT16)]
        assert sysex_calculator.calculate_max_payload_size(fields, 32) == 3

    def test_uint32_expansion(self, sysex_calculator: PayloadCalculator) -> None:
        """uint32 expands from 4 to 5 bytes in SysEx."""
        fields = [PrimitiveField(name="value", type_name=Type.UINT32)]
        assert sysex_calculator.calculate_max_payload_size(fields, 32) == 5

    def test_float32_expansion(self, sysex_calculator: PayloadCalculator) -> None:
        """float32 expands from 4 to 5 bytes in SysEx."""
        fields = [PrimitiveField(name="value", type_name=Type.FLOAT32)]
        assert sysex_calculator.calculate_max_payload_size(fields, 32) == 5


class TestPayloadCalculatorEnum:
    """Test PayloadCalculator with enum fields."""

    @pytest.fixture
    def enum_def(self) -> EnumDef:
        """Create a test enum definition."""
        return EnumDef(
            name="TestEnum",
            values={"VALUE_A": 0, "VALUE_B": 1, "VALUE_C": 2},
        )

    def test_single_enum(self, binary_calculator: PayloadCalculator, enum_def: EnumDef) -> None:
        """Single enum is 1 byte."""
        fields = [EnumField(name="status", enum_def=enum_def)]
        assert binary_calculator.calculate_max_payload_size(fields, 32) == 1
        assert binary_calculator.calculate_min_payload_size(fields, 32) == 1

    def test_enum_array(self, binary_calculator: PayloadCalculator, enum_def: EnumDef) -> None:
        """Enum array: count byte + elements."""
        fields = [EnumField(name="statuses", enum_def=enum_def, array=3)]
        # Max: 1 (count) + 3 * 1 (elements) = 4
        assert binary_calculator.calculate_max_payload_size(fields, 32) == 4
        # Min: 1 (count byte only)
        assert binary_calculator.calculate_min_payload_size(fields, 32) == 1


class TestPayloadCalculatorComposite:
    """Test PayloadCalculator with composite fields."""

    def test_simple_composite(self, binary_calculator: PayloadCalculator) -> None:
        """Composite field sums nested fields."""
        nested_fields = [
            PrimitiveField(name="x", type_name=Type.UINT8),
            PrimitiveField(name="y", type_name=Type.UINT8),
        ]
        fields = [CompositeField(name="point", fields=nested_fields)]
        # 1 + 1 = 2
        assert binary_calculator.calculate_max_payload_size(fields, 32) == 2
        assert binary_calculator.calculate_min_payload_size(fields, 32) == 2

    def test_composite_array(self, binary_calculator: PayloadCalculator) -> None:
        """Composite array: count byte + (nested_size * count)."""
        nested_fields = [
            PrimitiveField(name="x", type_name=Type.UINT8),
            PrimitiveField(name="y", type_name=Type.UINT8),
        ]
        fields = [CompositeField(name="points", fields=nested_fields, array=3)]
        # Max: 1 (count) + 3 * 2 (nested) = 7
        assert binary_calculator.calculate_max_payload_size(fields, 32) == 7
        # Min: 1 (count byte only)
        assert binary_calculator.calculate_min_payload_size(fields, 32) == 1

    def test_nested_composite(self, binary_calculator: PayloadCalculator) -> None:
        """Nested composites sum recursively."""
        inner = [PrimitiveField(name="value", type_name=Type.UINT16)]
        outer = [
            PrimitiveField(name="id", type_name=Type.UINT8),
            CompositeField(name="data", fields=inner),
        ]
        fields = [CompositeField(name="container", fields=outer)]
        # 1 (id) + 2 (value) = 3
        assert binary_calculator.calculate_max_payload_size(fields, 32) == 3


class TestPayloadCalculatorProtocolDifference:
    """Test key differences between Binary and SysEx."""

    def test_complex_message_differs(
        self, binary_calculator: PayloadCalculator, sysex_calculator: PayloadCalculator
    ) -> None:
        """Complex message shows protocol size difference."""
        fields = [
            PrimitiveField(name="id", type_name=Type.UINT8),
            PrimitiveField(name="position", type_name=Type.UINT32),
            PrimitiveField(name="values", type_name=Type.UINT16, array=4),
        ]

        # Binary: 1 + 4 + (1 + 4*2) = 1 + 4 + 9 = 14
        assert binary_calculator.calculate_max_payload_size(fields, 32) == 14

        # SysEx: 1 + 5 + (1 + 4*3) = 1 + 5 + 13 = 19 (7-bit expansion)
        assert sysex_calculator.calculate_max_payload_size(fields, 32) == 19
