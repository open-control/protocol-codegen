"""
Tests for method generation (naming utilities and generators).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from protocol_codegen.core.enums import Direction, Intent
from protocol_codegen.core.field import PrimitiveField, Type
from protocol_codegen.core.loader import TypeRegistry
from protocol_codegen.core.message import Message
from protocol_codegen.generators.common.naming import (
    message_name_to_callback_name,
    message_name_to_method_name,
    should_exclude_field,
    to_camel_case,
    to_pascal_case,
)
from protocol_codegen.generators.common.cpp.method_generator import (
    generate_protocol_methods_hpp,
)
from protocol_codegen.generators.common.java.method_generator import (
    generate_protocol_methods_java,
)


class TestNamingConversions:
    """Tests for naming conversion utilities."""

    def test_simple_name_to_method(self) -> None:
        assert message_name_to_method_name("TRANSPORT_PLAY") == "transportPlay"

    def test_name_with_suffix_preserved(self) -> None:
        """Suffixes are no longer removed - names should be correct at source."""
        assert message_name_to_method_name("DEVICE_SELECT") == "deviceSelect"
        assert message_name_to_method_name("TRACK_VOLUME_STATE") == "trackVolumeState"

    def test_request_prefix_preserved(self) -> None:
        assert message_name_to_method_name("REQUEST_DEVICE_LIST") == "requestDeviceList"

    def test_callback_name(self) -> None:
        assert message_name_to_callback_name("TRANSPORT_PLAY") == "onTransportPlay"

    def test_callback_name_complex(self) -> None:
        assert message_name_to_callback_name("DEVICE_LIST_WINDOW") == "onDeviceListWindow"

    def test_to_camel_case(self) -> None:
        assert to_camel_case("TRANSPORT_PLAY") == "transportPlay"
        assert to_camel_case("DEVICE") == "device"
        assert to_camel_case("A_B_C") == "aBC"

    def test_to_pascal_case(self) -> None:
        assert to_pascal_case("TRANSPORT_PLAY") == "TransportPlay"
        assert to_pascal_case("DEVICE") == "Device"


class TestExcludedFields:
    """Tests for field exclusion logic."""

    def test_from_host_excluded(self) -> None:
        assert should_exclude_field("fromHost") is True

    def test_is_echo_excluded(self) -> None:
        assert should_exclude_field("isEcho") is True

    def test_normal_field_not_excluded(self) -> None:
        assert should_exclude_field("value") is False
        assert should_exclude_field("index") is False


class TestCppMethodGenerator:
    """Tests for C++ method generation."""

    def test_to_host_generates_send_method(self) -> None:
        """TO_HOST message generates a send method in C++."""
        msg = Message(
            description="Play transport",
            fields=[PrimitiveField("playing", type_name=Type.BOOL)],
            direction=Direction.TO_HOST,
            intent=Intent.COMMAND,
        )
        msg.name = "TRANSPORT_PLAY"

        code = generate_protocol_methods_hpp([msg], Path("test.hpp"))

        assert "void transportPlay(bool playing)" in code
        assert "send(Protocol::TransportPlayMessage{playing})" in code

    def test_to_controller_not_in_methods_inl(self) -> None:
        """TO_CONTROLLER messages are not included in ProtocolMethods.inl (callbacks are in ProtocolCallbacks)."""
        msg = Message(
            description="Transport state",
            fields=[PrimitiveField("playing", type_name=Type.BOOL)],
            direction=Direction.TO_CONTROLLER,
            intent=Intent.NOTIFY,
        )
        msg.name = "TRANSPORT_STATE"

        code = generate_protocol_methods_hpp([msg], Path("test.hpp"))

        # TO_CONTROLLER messages are handled by ProtocolCallbacks, not ProtocolMethods.inl
        assert "transportState" not in code
        assert "No TO_HOST messages" in code

    def test_empty_message_generates_no_args(self) -> None:
        """Message with no fields generates method with no args."""
        msg = Message(
            description="Request",
            fields=[],
            direction=Direction.TO_HOST,
            intent=Intent.QUERY,
        )
        msg.name = "REQUEST_STATUS"

        code = generate_protocol_methods_hpp([msg], Path("test.hpp"))

        assert "void requestStatus()" in code
        assert "send(Protocol::RequestStatusMessage{})" in code

    def test_legacy_message_ignored(self) -> None:
        """Legacy messages (no direction) are ignored."""
        msg = Message(
            description="Legacy",
            fields=[PrimitiveField("value", type_name=Type.UINT8)],
        )
        msg.name = "LEGACY_MESSAGE"

        code = generate_protocol_methods_hpp([msg], Path("test.hpp"))

        assert "legacyMessage" not in code

    def test_deprecated_message_ignored(self) -> None:
        """Deprecated messages are ignored."""
        msg = Message(
            description="Deprecated",
            fields=[],
            direction=Direction.TO_HOST,
            intent=Intent.COMMAND,
            deprecated=True,
        )
        msg.name = "OLD_MESSAGE"

        code = generate_protocol_methods_hpp([msg], Path("test.hpp"))

        assert "oldMessage" not in code


class TestJavaMethodGenerator:
    """Tests for Java method generation."""

    @pytest.fixture
    def type_registry(self) -> TypeRegistry:
        """Create a TypeRegistry with builtins loaded for tests."""
        registry = TypeRegistry()
        registry.load_builtins()
        return registry

    def test_to_host_generates_callback(self, type_registry: TypeRegistry) -> None:
        """TO_HOST message generates a callback in Java (Host receives)."""
        msg = Message(
            description="Play transport",
            fields=[PrimitiveField("playing", type_name=Type.BOOL)],
            direction=Direction.TO_HOST,
            intent=Intent.COMMAND,
        )
        msg.name = "TRANSPORT_PLAY"

        code = generate_protocol_methods_java([msg], Path("test.java"), "com.test", type_registry)

        assert "Consumer<TransportPlayMessage>" in code
        assert "onTransportPlay" in code

    def test_to_controller_generates_send_method(self, type_registry: TypeRegistry) -> None:
        """TO_CONTROLLER message generates a send method in Java (Host sends)."""
        msg = Message(
            description="Transport state",
            fields=[PrimitiveField("playing", type_name=Type.BOOL)],
            direction=Direction.TO_CONTROLLER,
            intent=Intent.NOTIFY,
        )
        msg.name = "TRANSPORT_STATE"

        code = generate_protocol_methods_java([msg], Path("test.java"), "com.test", type_registry)

        assert "void transportState(boolean playing)" in code
        assert "send(new TransportStateMessage(playing))" in code

    def test_package_declaration(self, type_registry: TypeRegistry) -> None:
        """Generated code includes correct package."""
        msg = Message(
            description="Test",
            fields=[],
            direction=Direction.TO_HOST,
            intent=Intent.COMMAND,
        )
        msg.name = "TEST"

        code = generate_protocol_methods_java([msg], Path("test.java"), "com.bitwig.protocol", type_registry)

        assert "package com.bitwig.protocol;" in code
        assert "import com.bitwig.protocol.struct.*;" in code
