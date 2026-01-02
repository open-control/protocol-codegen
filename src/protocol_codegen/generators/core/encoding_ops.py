"""
Encoding/Decoding Operations - Intermediate representation for code generation.

These dataclasses represent abstract encoding/decoding operations that are
language-agnostic. They are produced by TypeEncoders/TypeDecoders and consumed
by LanguageBackends to generate final code.
"""

from __future__ import annotations

from dataclasses import dataclass

# =============================================================================
# Encoder Operations
# =============================================================================


@dataclass(frozen=True)
class ByteWriteOp:
    """Single byte write operation.

    Attributes:
        index: Byte index (for Java: buffer[offset + index])
        expression: Language-agnostic expression (e.g., "val & 0xFF")
    """

    index: int
    expression: str


@dataclass(frozen=True)
class MethodSpec:
    """Language-agnostic specification for an encoder method.

    This is the contract between TypeEncoder (producer) and
    LanguageBackend (consumer).

    Attributes:
        type_name: Protocol-codegen type (e.g., "uint16")
        method_name: Method name without prefix (e.g., "Uint16")
        param_type: Parameter type name (protocol-codegen type)
        byte_count: Number of bytes in encoded form (-1 for variable length)
        byte_writes: Tuple of byte write operations
        doc_comment: Documentation string
        preamble: Optional code before byte writes (e.g., "uint32_t bits; memcpy(...);")
        needs_signed_cast: True if param is signed and needs cast to unsigned
    """

    type_name: str
    method_name: str
    param_type: str
    byte_count: int
    byte_writes: tuple[ByteWriteOp, ...]
    doc_comment: str
    preamble: str | None = None
    needs_signed_cast: bool = False


# =============================================================================
# Decoder Operations
# =============================================================================


@dataclass(frozen=True)
class ByteReadOp:
    """Single byte read operation.

    Attributes:
        index: Byte index in buffer (e.g., buf[0], buf[1])
        shift: Bit shift to apply (e.g., << 8)
        mask: Optional mask to apply (e.g., 0x7F for SysEx)
    """

    index: int
    shift: int = 0
    mask: int | None = None


@dataclass(frozen=True)
class DecoderMethodSpec:
    """Language-agnostic specification for a decoder method.

    Decoders differ from encoders:
    - They return bool (success/failure)
    - They write to an output parameter
    - They track remaining bytes

    Attributes:
        type_name: Protocol-codegen type (e.g., "uint16")
        method_name: Method name without prefix (e.g., "Uint16")
        result_type: Result type name (protocol-codegen type)
        byte_count: Number of bytes to read (-1 for variable length)
        byte_reads: Tuple of byte read operations to combine into value
        doc_comment: Documentation string
        postamble: Optional code after byte reads (e.g., for float memcpy)
        needs_signed_cast: True if result is signed and needs cast
    """

    type_name: str
    method_name: str
    result_type: str
    byte_count: int
    byte_reads: tuple[ByteReadOp, ...]
    doc_comment: str
    postamble: str | None = None
    needs_signed_cast: bool = False
