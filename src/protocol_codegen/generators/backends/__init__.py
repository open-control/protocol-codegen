"""
Language Backends for Code Generation.

This package provides language-specific backends that encapsulate
syntax, idioms, and conventions for target languages.

Available Backends:
- CppBackend: C++17 with STL containers
- JavaBackend: Java 8+ with ByteBuffer

Usage:
    from protocol_codegen.generators.languages.cpp import CppBackend, JavaBackend

    cpp = CppBackend(namespace="Protocol")
    java = JavaBackend(package="com.example.protocol")

    # Get type from registry
    cpp_type = cpp.get_type("uint8", registry)  # -> "uint8_t"
    java_type = java.get_type("uint8", registry)  # -> "int"

    # Generate array type
    cpp.array_type("uint8_t", 16)  # -> "std::array<uint8_t, 16>"
    java.array_type("int", 16)    # -> "int[]"
"""

from typing import Any

from protocol_codegen.generators.languages.base import LanguageBackend
from protocol_codegen.generators.languages.cpp.backend import CppBackend
from protocol_codegen.generators.languages.java.backend import JavaBackend

__all__ = [
    "LanguageBackend",
    "CppBackend",
    "JavaBackend",
]


def get_backend(language: str, **kwargs: Any) -> LanguageBackend:
    """Factory function to get a backend by language name.

    Args:
        language: Language identifier ('cpp', 'java')
        **kwargs: Backend-specific options (namespace, package, etc.)

    Returns:
        Configured LanguageBackend instance

    Raises:
        ValueError: If language is not supported
    """
    backends = {
        "cpp": CppBackend,
        "java": JavaBackend,
    }

    backend_class = backends.get(language.lower())
    if backend_class is None:
        supported = ", ".join(sorted(backends.keys()))
        raise ValueError(f"Unknown language '{language}'. Supported: {supported}")

    return backend_class(**kwargs)
