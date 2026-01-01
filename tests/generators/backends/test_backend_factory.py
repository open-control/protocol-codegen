"""Tests for backend factory function."""

import pytest

from protocol_codegen.generators.backends import (
    CppBackend,
    JavaBackend,
    LanguageBackend,
    get_backend,
)


class TestGetBackend:
    """Test get_backend factory function."""

    def test_get_cpp_backend(self) -> None:
        backend = get_backend("cpp")
        assert isinstance(backend, CppBackend)
        assert isinstance(backend, LanguageBackend)

    def test_get_java_backend(self) -> None:
        backend = get_backend("java")
        assert isinstance(backend, JavaBackend)
        assert isinstance(backend, LanguageBackend)

    def test_case_insensitive(self) -> None:
        assert isinstance(get_backend("CPP"), CppBackend)
        assert isinstance(get_backend("Cpp"), CppBackend)
        assert isinstance(get_backend("JAVA"), JavaBackend)
        assert isinstance(get_backend("Java"), JavaBackend)

    def test_with_kwargs_cpp(self) -> None:
        backend = get_backend("cpp", namespace="CustomNS")
        assert isinstance(backend, CppBackend)
        assert backend.namespace == "CustomNS"

    def test_with_kwargs_java(self) -> None:
        backend = get_backend("java", package="com.example")
        assert isinstance(backend, JavaBackend)
        assert backend.package == "com.example"

    def test_unknown_language_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown language 'rust'"):
            get_backend("rust")

    def test_error_message_lists_supported(self) -> None:
        with pytest.raises(ValueError, match="Supported: cpp, java"):
            get_backend("unknown")
