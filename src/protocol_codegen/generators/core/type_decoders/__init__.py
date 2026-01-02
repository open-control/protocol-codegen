"""
Type Decoders.

This package provides type-specific decoding logic that produces
DecoderMethodSpecs for the LanguageBackend to render.

Each TypeDecoder:
- Knows which protocol-codegen types it supports
- Uses an injected EncodingStrategy for protocol-specific parameters
- Produces DecoderMethodSpecs that are language-agnostic
"""

from .base import TypeDecoder
from .bool_decoder import BoolDecoder
from .float_decoder import FloatDecoder
from .integer_decoder import IntegerDecoder
from .norm_decoder import NormDecoder
from .string_decoder import StringDecoder

__all__ = [
    "TypeDecoder",
    "BoolDecoder",
    "FloatDecoder",
    "IntegerDecoder",
    "NormDecoder",
    "StringDecoder",
]
