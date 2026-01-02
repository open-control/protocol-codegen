"""
Language-specific code generation.

This module contains the language axis of the code generation:
- base: LanguageBackend abstract base class
- cpp: C++ backend and file generators
- java: Java backend and file generators
"""

from protocol_codegen.generators.languages.base import LanguageBackend

__all__ = [
    "LanguageBackend",
]
