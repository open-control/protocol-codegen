"""
Tests for EnumDef and EnumField classes.
"""

import pytest

from protocol_codegen.core import EnumDef, EnumField


class TestEnumDef:
    """Tests for EnumDef dataclass."""

    def test_create_simple_enum(self) -> None:
        """Test creating a simple enum."""
        enum = EnumDef(
            name="TrackType",
            values={"AUDIO": 0, "INSTRUMENT": 1, "GROUP": 2},
        )
        assert enum.name == "TrackType"
        assert enum.values == {"AUDIO": 0, "INSTRUMENT": 1, "GROUP": 2}
        assert enum.description == ""
        assert enum.is_bitflags is False

    def test_create_enum_with_description(self) -> None:
        """Test creating an enum with description."""
        enum = EnumDef(
            name="DeviceType",
            values={"UNKNOWN": 0, "AUDIO": 1},
            description="Device type from Bitwig",
        )
        assert enum.description == "Device type from Bitwig"

    def test_create_bitflags_enum(self) -> None:
        """Test creating a bitflags enum."""
        enum = EnumDef(
            name="ChildType",
            values={"NONE": 0, "SLOTS": 1, "LAYERS": 2, "DRUMS": 4},
            is_bitflags=True,
        )
        assert enum.is_bitflags is True
        assert enum.cpp_type == "uint8_t"
        assert enum.java_type == "int"

    def test_empty_name_raises(self) -> None:
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Enum name cannot be empty"):
            EnumDef(name="", values={"A": 0})

    def test_lowercase_name_raises(self) -> None:
        """Test that lowercase name raises ValueError."""
        with pytest.raises(ValueError, match="Enum name must be PascalCase"):
            EnumDef(name="trackType", values={"A": 0})

    def test_empty_values_raises(self) -> None:
        """Test that empty values raises ValueError."""
        with pytest.raises(ValueError, match="must have at least one value"):
            EnumDef(name="Empty", values={})

    def test_negative_value_raises(self) -> None:
        """Test that negative values raise ValueError."""
        with pytest.raises(ValueError, match="must be a non-negative integer"):
            EnumDef(name="Bad", values={"NEG": -1})

    def test_create_enum_with_string_mapping(self) -> None:
        """Test creating an enum with string mapping."""
        enum = EnumDef(
            name="TrackType",
            values={"AUDIO": 0, "INSTRUMENT": 1},
            string_mapping={"Audio": "AUDIO", "Instrument": "INSTRUMENT"},
        )
        assert enum.string_mapping == {"Audio": "AUDIO", "Instrument": "INSTRUMENT"}

    def test_invalid_string_mapping_raises(self) -> None:
        """Test that invalid string mapping raises ValueError."""
        with pytest.raises(ValueError, match="references unknown value"):
            EnumDef(
                name="Bad",
                values={"A": 0},
                string_mapping={"foo": "NONEXISTENT"},
            )

    def test_max_value(self) -> None:
        """Test max_value property."""
        enum = EnumDef(
            name="Test",
            values={"A": 0, "B": 5, "C": 3},
        )
        assert enum.max_value == 5

    def test_wire_type(self) -> None:
        """Test wire_type is always uint8."""
        enum = EnumDef(name="Test", values={"A": 0})
        assert enum.wire_type == "uint8"

    def test_cpp_type_enum(self) -> None:
        """Test cpp_type for regular enum (no namespace by default)."""
        enum = EnumDef(name="TrackType", values={"A": 0})
        assert enum.cpp_type == "TrackType"

    def test_cpp_type_enum_with_namespace(self) -> None:
        """Test cpp_type for enum with custom namespace."""
        enum = EnumDef(name="TrackType", values={"A": 0}, cpp_namespace="Protocol")
        assert enum.cpp_type == "Protocol::TrackType"

    def test_cpp_type_bitflags(self) -> None:
        """Test cpp_type for bitflags."""
        enum = EnumDef(name="ChildType", values={"A": 0}, is_bitflags=True)
        assert enum.cpp_type == "uint8_t"

    def test_java_type_enum(self) -> None:
        """Test java_type for regular enum."""
        enum = EnumDef(name="TrackType", values={"A": 0})
        assert enum.java_type == "TrackType"

    def test_java_type_bitflags(self) -> None:
        """Test java_type for bitflags."""
        enum = EnumDef(name="ChildType", values={"A": 0}, is_bitflags=True)
        assert enum.java_type == "int"

    def test_get_default_value(self) -> None:
        """Test get_default_value returns first value name."""
        enum = EnumDef(name="Test", values={"FIRST": 0, "SECOND": 1})
        assert enum.get_default_value() == "FIRST"

    def test_custom_namespace(self) -> None:
        """Test custom C++ namespace."""
        enum = EnumDef(
            name="Custom",
            values={"A": 0},
            cpp_namespace="MyNamespace",
        )
        assert enum.cpp_namespace == "MyNamespace"
        assert enum.cpp_type == "MyNamespace::Custom"

    def test_str_representation(self) -> None:
        """Test string representation."""
        enum = EnumDef(name="Test", values={"A": 0, "B": 1})
        assert "EnumDef(Test" in str(enum)
        assert "A" in str(enum)

    def test_str_representation_bitflags(self) -> None:
        """Test string representation for bitflags."""
        enum = EnumDef(name="Flags", values={"A": 1}, is_bitflags=True)
        assert "(bitflags)" in str(enum)

    def test_frozen(self) -> None:
        """Test that EnumDef is frozen (immutable)."""
        enum = EnumDef(name="Test", values={"A": 0})
        with pytest.raises(AttributeError):
            enum.name = "Changed"  # type: ignore[misc]


class TestEnumField:
    """Tests for EnumField class."""

    @pytest.fixture
    def sample_enum(self) -> EnumDef:
        """Create a sample enum for testing."""
        return EnumDef(
            name="TrackType",
            values={"AUDIO": 0, "INSTRUMENT": 1, "GROUP": 2},
        )

    def test_create_scalar_field(self, sample_enum: EnumDef) -> None:
        """Test creating a scalar enum field."""
        field = EnumField("trackType", enum_def=sample_enum)
        assert field.name == "trackType"
        assert field.enum_def == sample_enum
        assert field.array is None

    def test_create_array_field(self, sample_enum: EnumDef) -> None:
        """Test creating an array enum field."""
        field = EnumField("trackTypes", enum_def=sample_enum, array=8)
        assert field.array == 8
        assert field.is_array() is True

    def test_is_primitive(self, sample_enum: EnumDef) -> None:
        """Test that enum fields are primitive."""
        field = EnumField("trackType", enum_def=sample_enum)
        assert field.is_primitive() is True

    def test_is_not_composite(self, sample_enum: EnumDef) -> None:
        """Test that enum fields are not composite."""
        field = EnumField("trackType", enum_def=sample_enum)
        assert field.is_composite() is False

    def test_is_enum(self, sample_enum: EnumDef) -> None:
        """Test is_enum method."""
        field = EnumField("trackType", enum_def=sample_enum)
        assert field.is_enum() is True

    def test_zero_array_size_raises(self, sample_enum: EnumDef) -> None:
        """Test that zero array size raises ValueError."""
        with pytest.raises(ValueError, match="Array size must be positive"):
            EnumField("bad", enum_def=sample_enum, array=0)

    def test_negative_array_size_raises(self, sample_enum: EnumDef) -> None:
        """Test that negative array size raises ValueError."""
        with pytest.raises(ValueError, match="Array size must be positive"):
            EnumField("bad", enum_def=sample_enum, array=-1)

    def test_validate_depth_scalar(self, sample_enum: EnumDef) -> None:
        """Test validate_depth for scalar field."""
        field = EnumField("trackType", enum_def=sample_enum)
        # Should not raise
        field.validate_depth(max_depth=3, current_depth=0)

    def test_validate_depth_exceeds_max(self, sample_enum: EnumDef) -> None:
        """Test validate_depth raises when exceeding max depth."""
        field = EnumField("trackType", enum_def=sample_enum)
        with pytest.raises(ValueError, match="exceeds maximum nesting depth"):
            field.validate_depth(max_depth=3, current_depth=4)

    def test_str_representation_scalar(self, sample_enum: EnumDef) -> None:
        """Test string representation for scalar field."""
        field = EnumField("trackType", enum_def=sample_enum)
        assert str(field) == "trackType: TrackType"

    def test_str_representation_array(self, sample_enum: EnumDef) -> None:
        """Test string representation for array field."""
        field = EnumField("trackTypes", enum_def=sample_enum, array=4)
        assert str(field) == "trackTypes: TrackType[4]"
