"""
Language-specific code generation.

This module contains the language axis of the code generation:
- base: LanguageBackend abstract base class
- cpp: C++ backend and file generators
- java: Java backend and file generators
"""

from typing import Any

from protocol_codegen.generators.languages.base import LanguageBackend
from protocol_codegen.generators.languages.cpp.backend import CppBackend
from protocol_codegen.generators.languages.java.backend import JavaBackend

__all__ = [
    "LanguageBackend",
    "CppBackend",
    "JavaBackend",
    "get_backend",
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
