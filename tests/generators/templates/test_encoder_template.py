"""Tests for EncoderTemplate."""

from pathlib import Path

import pytest

from protocol_codegen.core.loader import TypeRegistry
from protocol_codegen.generators.backends import CppBackend, JavaBackend
from protocol_codegen.generators.common.encoding import (
    Serial8EncodingStrategy,
    SysExEncodingStrategy,
)
from protocol_codegen.generators.templates import EncoderTemplate


@pytest.fixture
def type_registry() -> TypeRegistry:
    """Create a TypeRegistry with builtins loaded."""
    registry = TypeRegistry()
    registry.load_builtins()
    return registry


class TestEncoderTemplateCppSerial8:
    """Test EncoderTemplate with C++ and Serial8."""

    @pytest.fixture
    def template(self) -> EncoderTemplate:
        return EncoderTemplate(CppBackend(), Serial8EncodingStrategy())

    def test_generates_code(self, template: EncoderTemplate, type_registry: TypeRegistry) -> None:
        code = template.generate(type_registry, Path("Encoder.hpp"))
        assert len(code) > 0

    def test_has_pragma_once(self, template: EncoderTemplate, type_registry: TypeRegistry) -> None:
        code = template.generate(type_registry, Path("Encoder.hpp"))
        assert "#pragma once" in code

    def test_has_namespace(self, template: EncoderTemplate, type_registry: TypeRegistry) -> None:
        code = template.generate(type_registry, Path("Encoder.hpp"))
        assert "namespace Protocol {" in code
        assert "}  // namespace Protocol" in code

    def test_has_encoder_struct(self, template: EncoderTemplate, type_registry: TypeRegistry) -> None:
        code = template.generate(type_registry, Path("Encoder.hpp"))
        assert "struct Encoder {" in code

    def test_has_bool_encoder(self, template: EncoderTemplate, type_registry: TypeRegistry) -> None:
        code = template.generate(type_registry, Path("Encoder.hpp"))
        assert "encodeBool" in code
        assert "bool val" in code

    def test_has_uint8_encoder(self, template: EncoderTemplate, type_registry: TypeRegistry) -> None:
        code = template.generate(type_registry, Path("Encoder.hpp"))
        assert "encodeUint8" in code
        assert "uint8_t val" in code

    def test_has_uint16_encoder(self, template: EncoderTemplate, type_registry: TypeRegistry) -> None:
        code = template.generate(type_registry, Path("Encoder.hpp"))
        assert "encodeUint16" in code
        # Serial8: 2 bytes, little-endian
        assert "val & 0xFF" in code
        assert "(val >> 8) & 0xFF" in code

    def test_has_uint32_encoder(self, template: EncoderTemplate, type_registry: TypeRegistry) -> None:
        code = template.generate(type_registry, Path("Encoder.hpp"))
        assert "encodeUint32" in code
        # Serial8: 4 bytes
        assert "(val >> 24) & 0xFF" in code

    def test_has_float32_encoder(self, template: EncoderTemplate, type_registry: TypeRegistry) -> None:
        code = template.generate(type_registry, Path("Encoder.hpp"))
        assert "encodeFloat32" in code
        assert "memcpy" in code

    def test_has_norm8_encoder(self, template: EncoderTemplate, type_registry: TypeRegistry) -> None:
        code = template.generate(type_registry, Path("Encoder.hpp"))
        assert "encodeNorm8" in code
        # Serial8: max value 255
        assert "255" in code

    def test_has_string_encoder(self, template: EncoderTemplate, type_registry: TypeRegistry) -> None:
        code = template.generate(type_registry, Path("Encoder.hpp"))
        assert "encodeString" in code
        assert "std::string" in code


class TestEncoderTemplateCppSysEx:
    """Test EncoderTemplate with C++ and SysEx."""

    @pytest.fixture
    def template(self) -> EncoderTemplate:
        return EncoderTemplate(CppBackend(), SysExEncodingStrategy())

    def test_uint16_uses_7bit_encoding(
        self, template: EncoderTemplate, type_registry: TypeRegistry
    ) -> None:
        code = template.generate(type_registry, Path("Encoder.hpp"))
        # SysEx: 3 bytes, 7-bit encoding
        assert "0x7F" in code
        assert "(val >> 7) & 0x7F" in code
        assert "(val >> 14) & 0x03" in code

    def test_uint32_uses_7bit_encoding(
        self, template: EncoderTemplate, type_registry: TypeRegistry
    ) -> None:
        code = template.generate(type_registry, Path("Encoder.hpp"))
        # SysEx: 5 bytes, 7-bit encoding
        assert "(val >> 28) & 0x0F" in code

    def test_norm8_uses_127_max(
        self, template: EncoderTemplate, type_registry: TypeRegistry
    ) -> None:
        code = template.generate(type_registry, Path("Encoder.hpp"))
        # SysEx: max value 127
        assert "127" in code


class TestEncoderTemplateJavaSerial8:
    """Test EncoderTemplate with Java and Serial8."""

    @pytest.fixture
    def template(self) -> EncoderTemplate:
        return EncoderTemplate(JavaBackend(), Serial8EncodingStrategy())

    def test_has_package(self, template: EncoderTemplate, type_registry: TypeRegistry) -> None:
        code = template.generate(type_registry, Path("Encoder.java"))
        assert "package protocol;" in code

    def test_has_class(self, template: EncoderTemplate, type_registry: TypeRegistry) -> None:
        code = template.generate(type_registry, Path("Encoder.java"))
        assert "public final class Encoder {" in code

    def test_has_write_methods(self, template: EncoderTemplate, type_registry: TypeRegistry) -> None:
        code = template.generate(type_registry, Path("Encoder.java"))
        assert "writeBool" in code
        assert "writeUint8" in code
        assert "writeUint16" in code
        assert "writeFloat32" in code
        assert "writeString" in code

    def test_returns_byte_count(self, template: EncoderTemplate, type_registry: TypeRegistry) -> None:
        code = template.generate(type_registry, Path("Encoder.java"))
        assert "return 1;" in code  # bool, uint8
        assert "return 2;" in code  # uint16
        assert "return 4;" in code  # uint32, float32


class TestEncoderTemplateJavaSysEx:
    """Test EncoderTemplate with Java and SysEx."""

    @pytest.fixture
    def template(self) -> EncoderTemplate:
        return EncoderTemplate(JavaBackend(), SysExEncodingStrategy())

    def test_uint16_returns_3_bytes(
        self, template: EncoderTemplate, type_registry: TypeRegistry
    ) -> None:
        code = template.generate(type_registry, Path("Encoder.java"))
        # SysEx uint16: 3 bytes
        assert "return 3;" in code

    def test_uint32_returns_5_bytes(
        self, template: EncoderTemplate, type_registry: TypeRegistry
    ) -> None:
        code = template.generate(type_registry, Path("Encoder.java"))
        # SysEx uint32: 5 bytes
        assert "return 5;" in code


class TestEncoderTemplateCustomPackage:
    """Test EncoderTemplate with custom Java package."""

    def test_custom_package(self, type_registry: TypeRegistry) -> None:
        backend = JavaBackend(package="com.example.protocol")
        template = EncoderTemplate(backend, Serial8EncodingStrategy())
        code = template.generate(type_registry, Path("Encoder.java"))
        assert "package com.example.protocol;" in code
