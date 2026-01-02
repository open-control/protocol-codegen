"""
Type Encoders.

This package provides type-specific encoding logic that produces
MethodSpecs for the LanguageBackend to render.

Each TypeEncoder:
- Knows which protocol-codegen types it supports
- Uses an injected EncodingStrategy for protocol-specific parameters
- Produces MethodSpecs that are language-agnostic
"""

from .base import TypeEncoder
from .bool_encoder import BoolEncoder
from .float_encoder import FloatEncoder
from .integer_encoder import IntegerEncoder
from .norm_encoder import NormEncoder
from .string_encoder import StringEncoder

__all__ = [
    "TypeEncoder",
    "BoolEncoder",
    "FloatEncoder",
    "IntegerEncoder",
    "NormEncoder",
    "StringEncoder",
]
