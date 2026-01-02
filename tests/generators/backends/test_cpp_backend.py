"""Tests for CppBackend."""

from pathlib import Path

import pytest

from protocol_codegen.core.loader import TypeRegistry
from protocol_codegen.generators.languages.cpp.backend import CppBackend


@pytest.fixture
def backend() -> CppBackend:
    """Create a CppBackend with default namespace."""
    return CppBackend()


@pytest.fixture
def custom_backend() -> CppBackend:
    """Create a CppBackend with custom namespace."""
    return CppBackend(namespace="CustomNamespace")


@pytest.fixture
def type_registry() -> TypeRegistry:
    """Create a TypeRegistry with builtins loaded."""
    registry = TypeRegistry()
    registry.load_builtins()
    return registry


class TestCppBackendIdentity:
    """Test backend identity properties."""

    def test_name(self, backend: CppBackend) -> None:
        assert backend.name == "cpp"

    def test_file_extension(self, backend: CppBackend) -> None:
        assert backend.file_extension == ".hpp"

    def test_default_namespace(self, backend: CppBackend) -> None:
        assert backend.namespace == "Protocol"

    def test_custom_namespace(self, custom_backend: CppBackend) -> None:
        assert custom_backend.namespace == "CustomNamespace"


class TestCppBackendTypeMapping:
    """Test type mapping through TypeRegistry."""

    def test_get_type_uint8(self, backend: CppBackend, type_registry: TypeRegistry) -> None:
        assert backend.get_type("uint8", type_registry) == "uint8_t"

    def test_get_type_uint16(self, backend: CppBackend, type_registry: TypeRegistry) -> None:
        assert backend.get_type("uint16", type_registry) == "uint16_t"

    def test_get_type_uint32(self, backend: CppBackend, type_registry: TypeRegistry) -> None:
        assert backend.get_type("uint32", type_registry) == "uint32_t"

    def test_get_type_int8(self, backend: CppBackend, type_registry: TypeRegistry) -> None:
        assert backend.get_type("int8", type_registry) == "int8_t"

    def test_get_type_int16(self, backend: CppBackend, type_registry: TypeRegistry) -> None:
        assert backend.get_type("int16", type_registry) == "int16_t"

    def test_get_type_int32(self, backend: CppBackend, type_registry: TypeRegistry) -> None:
        assert backend.get_type("int32", type_registry) == "int32_t"

    def test_get_type_float32(self, backend: CppBackend, type_registry: TypeRegistry) -> None:
        assert backend.get_type("float32", type_registry) == "float"

    def test_get_type_bool(self, backend: CppBackend, type_registry: TypeRegistry) -> None:
        assert backend.get_type("bool", type_registry) == "bool"

    def test_get_type_string(self, backend: CppBackend, type_registry: TypeRegistry) -> None:
        assert backend.get_type("string", type_registry) == "std::string"

    def test_get_type_norm8(self, backend: CppBackend, type_registry: TypeRegistry) -> None:
        assert backend.get_type("norm8", type_registry) == "float"

    def test_get_type_norm16(self, backend: CppBackend, type_registry: TypeRegistry) -> None:
        assert backend.get_type("norm16", type_registry) == "float"

    def test_get_type_unknown_returns_name(
        self, backend: CppBackend, type_registry: TypeRegistry
    ) -> None:
        """Unknown types (custom types) return the type name as-is."""
        assert backend.get_type("CustomType", type_registry) == "CustomType"


class TestCppBackendArrayTypes:
    """Test array type generation."""

    def test_fixed_array(self, backend: CppBackend) -> None:
        result = backend.array_type("uint8_t", 16)
        assert result == "std::array<uint8_t, 16>"

    def test_fixed_array_with_struct(self, backend: CppBackend) -> None:
        result = backend.array_type("FooMessage", 4)
        assert result == "std::array<FooMessage, 4>"

    def test_dynamic_array_explicit(self, backend: CppBackend) -> None:
        result = backend.array_type("uint8_t", 16, dynamic=True)
        assert result == "std::vector<uint8_t>"

    def test_dynamic_array_no_size(self, backend: CppBackend) -> None:
        result = backend.array_type("uint8_t", None)
        assert result == "std::vector<uint8_t>"


class TestCppBackendOptionalType:
    """Test optional type generation."""

    def test_optional_primitive(self, backend: CppBackend) -> None:
        result = backend.optional_type("uint8_t")
        assert result == "std::optional<uint8_t>"

    def test_optional_struct(self, backend: CppBackend) -> None:
        result = backend.optional_type("FooMessage")
        assert result == "std::optional<FooMessage>"


class TestCppBackendIncludes:
    """Test include statement generation."""

    def test_local_include(self, backend: CppBackend) -> None:
        result = backend.include_statement("Encoder.hpp")
        assert result == '#include "Encoder.hpp"'

    def test_system_include_explicit(self, backend: CppBackend) -> None:
        result = backend.include_statement("cstdint", is_system=True)
        assert result == "#include <cstdint>"

    def test_system_include_with_brackets(self, backend: CppBackend) -> None:
        result = backend.include_statement("<cstdint>")
        assert result == "#include <cstdint>"

    def test_standard_imports(self, backend: CppBackend) -> None:
        imports = backend.standard_imports()
        assert "<cstdint>" in imports
        assert "<string>" in imports
        assert "<array>" in imports
        assert "<vector>" in imports


class TestCppBackendNamespace:
    """Test namespace handling."""

    def test_namespace_open(self, backend: CppBackend) -> None:
        result = backend.namespace_open("Protocol")
        assert result == "namespace Protocol {"

    def test_namespace_close(self, backend: CppBackend) -> None:
        result = backend.namespace_close("Protocol")
        assert result == "}  // namespace Protocol"


class TestCppBackendFileStructure:
    """Test file header/footer generation."""

    def test_file_header_basic(self, backend: CppBackend) -> None:
        result = backend.file_header(Path("Test.hpp"), "Test file")
        assert "#pragma once" in result
        assert "AUTO-GENERATED" in result
        assert "Test.hpp" in result
        assert "namespace Protocol {" in result

    def test_file_header_with_includes(self, backend: CppBackend) -> None:
        result = backend.file_header(
            Path("Test.hpp"),
            "Test file",
            includes=["<cstdint>", "Encoder.hpp"],
        )
        assert "#include <cstdint>" in result
        assert '#include "Encoder.hpp"' in result

    def test_file_header_custom_namespace(self, backend: CppBackend) -> None:
        result = backend.file_header(
            Path("Test.hpp"),
            "Test file",
            namespace="CustomNS",
        )
        assert "namespace CustomNS {" in result

    def test_file_footer(self, backend: CppBackend) -> None:
        result = backend.file_footer()
        assert "}  // namespace Protocol" in result

    def test_file_footer_custom_namespace(self, backend: CppBackend) -> None:
        result = backend.file_footer(namespace="CustomNS")
        assert "}  // namespace CustomNS" in result


class TestCppBackendEncoderDecoder:
    """Test encoder/decoder call generation."""

    def test_encode_call(self, backend: CppBackend) -> None:
        result = backend.encode_call("encodeUint8", "value")
        assert result == "Encoder::encodeUint8(buf, value);"

    def test_encode_call_custom_buffer(self, backend: CppBackend) -> None:
        result = backend.encode_call("encodeUint8", "value", buffer_var="buffer")
        assert result == "Encoder::encodeUint8(buffer, value);"

    def test_decode_call(self, backend: CppBackend) -> None:
        result = backend.decode_call("decodeUint8")
        assert result == "Decoder::decodeUint8(buf)"

    def test_decode_call_custom_buffer(self, backend: CppBackend) -> None:
        result = backend.decode_call("decodeUint8", buffer_var="buffer")
        assert result == "Decoder::decodeUint8(buffer)"


class TestCppBackendHelpers:
    """Test C++ specific helpers."""

    def test_constant(self, backend: CppBackend) -> None:
        result = backend.constant("uint8_t", "MAX_SIZE", "255")
        assert result == "static constexpr uint8_t MAX_SIZE = 255;"

    def test_constant_with_visibility(self, backend: CppBackend) -> None:
        # visibility is ignored in C++ (uses section-based visibility)
        result = backend.constant("uint8_t", "MAX_SIZE", "255", visibility="private")
        assert result == "static constexpr uint8_t MAX_SIZE = 255;"

    def test_field(self, backend: CppBackend) -> None:
        result = backend.field("uint8_t", "value")
        assert result == "    uint8_t value;"

    def test_field_with_final(self, backend: CppBackend) -> None:
        result = backend.field("uint8_t", "value", is_final=True)
        assert result == "    const uint8_t value;"

    def test_static_function(self, backend: CppBackend) -> None:
        result = backend.static_function(
            "void",
            "encode",
            [("uint8_t*&", "buf"), ("uint8_t", "val")],
            ["*buf++ = val;"],
        )
        assert "static inline void encode(uint8_t*& buf, uint8_t val)" in result
        assert "*buf++ = val;" in result
        assert result.endswith("}")

    def test_generate_filename(self, backend: CppBackend) -> None:
        result = backend.generate_filename("Encoder")
        assert result == "Encoder.hpp"
