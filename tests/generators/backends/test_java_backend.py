"""Tests for JavaBackend."""

from pathlib import Path

import pytest

from protocol_codegen.core.loader import TypeRegistry
from protocol_codegen.generators.backends.java import JavaBackend


@pytest.fixture
def backend() -> JavaBackend:
    """Create a JavaBackend with default package."""
    return JavaBackend()


@pytest.fixture
def custom_backend() -> JavaBackend:
    """Create a JavaBackend with custom package."""
    return JavaBackend(package="com.example.protocol")


@pytest.fixture
def type_registry() -> TypeRegistry:
    """Create a TypeRegistry with builtins loaded."""
    registry = TypeRegistry()
    registry.load_builtins()
    return registry


class TestJavaBackendIdentity:
    """Test backend identity properties."""

    def test_name(self, backend: JavaBackend) -> None:
        assert backend.name == "java"

    def test_file_extension(self, backend: JavaBackend) -> None:
        assert backend.file_extension == ".java"

    def test_default_package(self, backend: JavaBackend) -> None:
        assert backend.package == "protocol"

    def test_custom_package(self, custom_backend: JavaBackend) -> None:
        assert custom_backend.package == "com.example.protocol"


class TestJavaBackendTypeMapping:
    """Test type mapping through TypeRegistry."""

    def test_get_type_uint8(self, backend: JavaBackend, type_registry: TypeRegistry) -> None:
        # Java has no unsigned, uint8 maps to int
        assert backend.get_type("uint8", type_registry) == "int"

    def test_get_type_uint16(self, backend: JavaBackend, type_registry: TypeRegistry) -> None:
        assert backend.get_type("uint16", type_registry) == "int"

    def test_get_type_uint32(self, backend: JavaBackend, type_registry: TypeRegistry) -> None:
        # uint32 needs long to hold full range
        assert backend.get_type("uint32", type_registry) == "long"

    def test_get_type_int8(self, backend: JavaBackend, type_registry: TypeRegistry) -> None:
        assert backend.get_type("int8", type_registry) == "byte"

    def test_get_type_int16(self, backend: JavaBackend, type_registry: TypeRegistry) -> None:
        assert backend.get_type("int16", type_registry) == "short"

    def test_get_type_int32(self, backend: JavaBackend, type_registry: TypeRegistry) -> None:
        assert backend.get_type("int32", type_registry) == "int"

    def test_get_type_float32(self, backend: JavaBackend, type_registry: TypeRegistry) -> None:
        assert backend.get_type("float32", type_registry) == "float"

    def test_get_type_bool(self, backend: JavaBackend, type_registry: TypeRegistry) -> None:
        assert backend.get_type("bool", type_registry) == "boolean"

    def test_get_type_string(self, backend: JavaBackend, type_registry: TypeRegistry) -> None:
        assert backend.get_type("string", type_registry) == "String"

    def test_get_type_norm8(self, backend: JavaBackend, type_registry: TypeRegistry) -> None:
        assert backend.get_type("norm8", type_registry) == "float"

    def test_get_type_norm16(self, backend: JavaBackend, type_registry: TypeRegistry) -> None:
        assert backend.get_type("norm16", type_registry) == "float"

    def test_get_type_unknown_returns_name(
        self, backend: JavaBackend, type_registry: TypeRegistry
    ) -> None:
        """Unknown types (custom types) return the type name as-is."""
        assert backend.get_type("CustomType", type_registry) == "CustomType"


class TestJavaBackendArrayTypes:
    """Test array type generation."""

    def test_fixed_array(self, backend: JavaBackend) -> None:
        result = backend.array_type("int", 16)
        assert result == "int[]"

    def test_fixed_array_with_struct(self, backend: JavaBackend) -> None:
        result = backend.array_type("FooMessage", 4)
        assert result == "FooMessage[]"

    def test_dynamic_array(self, backend: JavaBackend) -> None:
        # Java uses same syntax for dynamic and fixed arrays
        result = backend.array_type("int", 16, dynamic=True)
        assert result == "int[]"

    def test_dynamic_array_no_size(self, backend: JavaBackend) -> None:
        result = backend.array_type("int", None)
        assert result == "int[]"


class TestJavaBackendOptionalType:
    """Test optional type generation."""

    def test_optional_primitive(self, backend: JavaBackend) -> None:
        # Java uses nullable references, returns type as-is
        result = backend.optional_type("int")
        assert result == "int"

    def test_optional_struct(self, backend: JavaBackend) -> None:
        result = backend.optional_type("FooMessage")
        assert result == "FooMessage"


class TestJavaBackendImports:
    """Test import statement generation."""

    def test_import_statement(self, backend: JavaBackend) -> None:
        result = backend.include_statement("java.nio.ByteBuffer")
        assert result == "import java.nio.ByteBuffer;"

    def test_import_with_semicolon(self, backend: JavaBackend) -> None:
        # Should handle if already has semicolon
        result = backend.include_statement("java.nio.ByteBuffer;")
        assert result == "import java.nio.ByteBuffer;"

    def test_standard_imports(self, backend: JavaBackend) -> None:
        imports = backend.standard_imports()
        assert "java.nio.ByteBuffer" in imports
        assert "java.nio.ByteOrder" in imports


class TestJavaBackendPackage:
    """Test package/namespace handling."""

    def test_namespace_open(self, backend: JavaBackend) -> None:
        result = backend.namespace_open("protocol")
        assert result == "package protocol;"

    def test_namespace_close(self, backend: JavaBackend) -> None:
        # Java doesn't close packages
        result = backend.namespace_close("protocol")
        assert result == ""


class TestJavaBackendFileStructure:
    """Test file header/footer generation."""

    def test_file_header_basic(self, backend: JavaBackend) -> None:
        result = backend.file_header(Path("Test.java"), "Test file")
        assert "package protocol;" in result
        assert "AUTO-GENERATED" in result
        assert "Test.java" in result

    def test_file_header_with_imports(self, backend: JavaBackend) -> None:
        result = backend.file_header(
            Path("Test.java"),
            "Test file",
            includes=["java.nio.ByteBuffer", "java.util.List"],
        )
        assert "import java.nio.ByteBuffer;" in result
        assert "import java.util.List;" in result

    def test_file_header_custom_package(self, backend: JavaBackend) -> None:
        result = backend.file_header(
            Path("Test.java"),
            "Test file",
            namespace="com.example",
        )
        assert "package com.example;" in result

    def test_file_footer(self, backend: JavaBackend) -> None:
        # Java file footer is empty (classes close themselves)
        result = backend.file_footer()
        assert result == ""


class TestJavaBackendEncoderDecoder:
    """Test encoder/decoder call generation."""

    def test_encode_call(self, backend: JavaBackend) -> None:
        result = backend.encode_call("encodeUint8", "value")
        assert result == "Encoder.encodeUint8(buffer, value);"

    def test_encode_call_custom_buffer(self, backend: JavaBackend) -> None:
        result = backend.encode_call("encodeUint8", "value", buffer_var="buf")
        assert result == "Encoder.encodeUint8(buf, value);"

    def test_decode_call(self, backend: JavaBackend) -> None:
        result = backend.decode_call("decodeUint8")
        assert result == "Decoder.decodeUint8(buffer)"

    def test_decode_call_custom_buffer(self, backend: JavaBackend) -> None:
        result = backend.decode_call("decodeUint8", buffer_var="buf")
        assert result == "Decoder.decodeUint8(buf)"


class TestJavaBackendHelpers:
    """Test Java specific helpers."""

    def test_constant_public(self, backend: JavaBackend) -> None:
        result = backend.constant("int", "MAX_SIZE", "255")
        assert result == "public static final int MAX_SIZE = 255;"

    def test_constant_private(self, backend: JavaBackend) -> None:
        result = backend.constant("int", "MAX_SIZE", "255", visibility="private")
        assert result == "private static final int MAX_SIZE = 255;"

    def test_constant_package(self, backend: JavaBackend) -> None:
        result = backend.constant("int", "MAX_SIZE", "255", visibility="package")
        assert result == "static final int MAX_SIZE = 255;"

    def test_class_field(self, backend: JavaBackend) -> None:
        result = backend.class_field("int", "value")
        assert result == "    private int value;"

    def test_class_field_final(self, backend: JavaBackend) -> None:
        result = backend.class_field("int", "value", is_final=True)
        assert result == "    private final int value;"

    def test_class_field_public(self, backend: JavaBackend) -> None:
        result = backend.class_field("int", "value", visibility="public")
        assert result == "    public int value;"

    def test_static_method(self, backend: JavaBackend) -> None:
        result = backend.static_method(
            "void",
            "encode",
            [("ByteBuffer", "buffer"), ("int", "val")],
            ["buffer.put((byte) val);"],
        )
        assert "public static void encode(ByteBuffer buffer, int val)" in result
        assert "buffer.put((byte) val);" in result
        assert result.strip().endswith("}")

    def test_class_declaration(self, backend: JavaBackend) -> None:
        result = backend.class_declaration("Encoder")
        assert result == "public final class Encoder {"

    def test_class_declaration_not_final(self, backend: JavaBackend) -> None:
        result = backend.class_declaration("Encoder", is_final=False)
        assert result == "public class Encoder {"

    def test_boxed_type_int(self, backend: JavaBackend) -> None:
        assert backend.boxed_type("int") == "Integer"

    def test_boxed_type_boolean(self, backend: JavaBackend) -> None:
        assert backend.boxed_type("boolean") == "Boolean"

    def test_boxed_type_long(self, backend: JavaBackend) -> None:
        assert backend.boxed_type("long") == "Long"

    def test_boxed_type_unknown(self, backend: JavaBackend) -> None:
        # Non-primitive types return as-is
        assert backend.boxed_type("String") == "String"

    def test_generate_filename(self, backend: JavaBackend) -> None:
        result = backend.generate_filename("Encoder")
        assert result == "Encoder.java"
