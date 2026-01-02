"""
Java Language Support.

Components:
- JavaBackend: Java type mapping and code generation helpers
- JavaProtocolMixin: Protocol rendering mixin for Java
- file_generators: Individual file generators
"""

from protocol_codegen.generators.languages.java.backend import JavaBackend
from protocol_codegen.generators.languages.java.protocol_mixin import JavaProtocolMixin

__all__ = [
    "JavaBackend",
    "JavaProtocolMixin",
]
