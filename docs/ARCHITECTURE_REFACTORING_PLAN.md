# Plan de Refactorisation Architecturale - Protocol Codegen

> **Version** : 2.4
> **Date** : 2026-01-01
> **Branche** : `feature/extensible-architecture`
> **Tag de référence** : `v2.0-pre-extensibility`
> **Objectif** : Architecture extensible multi-langages / multi-protocoles
> **Progression** : Phase 3.10/3.10 COMPLETE ✅

---

## Table des Matières

1. [État Actuel de la Codebase](#1-état-actuel-de-la-codebase)
2. [Architecture Cible](#2-architecture-cible)
3. [Plan d'Exécution Détaillé](#3-plan-dexécution-détaillé)
4. [Inventaire Complet des Fichiers](#4-inventaire-complet-des-fichiers)
5. [Conventions de Nommage](#5-conventions-de-nommage)
6. [Risques et Mitigations](#6-risques-et-mitigations)
7. [Validation Continue](#7-validation-continue)

---

## 1. État Actuel de la Codebase

### 1.1 Commits Réalisés (Phase 3.0-3.5)

| Commit | Description | Fichiers |
|--------|-------------|----------|
| `eef4cb4` | feat(backends): LanguageBackend abstraction | +4 fichiers, ~850 lignes |
| `2fbb1d6` | feat(encoding): encoding specs | +320 lignes |
| `7574e01` | feat(templates): EncoderTemplate | +600 lignes |
| `b094997` | docs: architecture plan v1.1 | - |
| `6121992` | fix(types): Pylance compliance | refactor |
| `cf50d56` | docs: architecture plan v2.0 | - |
| `97ae652` | feat(architecture): TypeEncoder pattern (3.3-3.5) | +16 fichiers, ~1042 lignes |
| `723b685` | docs: update architecture plan v2.1 | - |
| `717bf23` | refactor(encoder): use TypeEncoder pattern (3.6-3.7) | -1,893 lignes, +100 lignes |
| `19e285a` | docs: update architecture plan v2.2 | - |
| `40f4742` | feat(decoder): implement TypeDecoder pattern (3.8) | +905 lignes, -1,369 lignes |
| `0eb85cb` | docs: update architecture plan v2.3 | - |
| `c5c4ea9` | fix(backends): add assertions for string codecs | +4 lignes |
| `TBD` | refactor(common): update __init__.py exports (3.10) | cleanup |

### 1.2 Fichiers Existants - Backends (COMPLET ✅)

| Fichier | Lignes | État |
|---------|--------|------|
| `generators/backends/__init__.py` | 62 | ✅ Complet |
| `generators/backends/base.py` | 303 | ✅ Complet (+render_encoder/decoder_method) |
| `generators/backends/cpp.py` | 468 | ✅ Complet (+render_encoder/decoder_method) |
| `generators/backends/java.py` | 494 | ✅ Complet (+render_encoder/decoder_method) |
| **Total backends** | **1,327** | |

### 1.3 Fichiers Existants - Encoding (COMPLET ✅)

| Fichier | Lignes | État |
|---------|--------|------|
| `generators/common/encoding/__init__.py` | 61 | ✅ Complet |
| `generators/common/encoding/strategy.py` | 164 | ✅ Complet |
| `generators/common/encoding/serial8_strategy.py` | 142 | ✅ Complet |
| `generators/common/encoding/sysex_strategy.py` | 145 | ✅ Complet |
| `generators/common/encoding/operations.py` | 52 | ✅ Complet (Phase 3.3) |
| **Total encoding** | **564** | |

**Classes disponibles** :
- `IntegerEncodingSpec` (dataclass) - shifts, masks, byte_count
- `NormEncodingSpec` (dataclass) - max_value, integer_spec
- `StringEncodingSpec` (dataclass) - length_mask, char_mask
- `EncodingStrategy` (ABC) - get_integer_spec(), get_norm_spec(), get_string_spec(), bool_true_value, bool_false_value
- `ByteWriteOp` (dataclass) - index, expression (Phase 3.3)
- `MethodSpec` (dataclass) - type_name, method_name, byte_writes, preamble, etc. (Phase 3.3)

### 1.3b Fichiers Existants - TypeEncoders (COMPLET ✅)

| Fichier | Lignes | État |
|---------|--------|------|
| `generators/common/type_encoders/__init__.py` | 26 | ✅ Complet |
| `generators/common/type_encoders/base.py` | 56 | ✅ Complet |
| `generators/common/type_encoders/bool_encoder.py` | 44 | ✅ Complet |
| `generators/common/type_encoders/integer_encoder.py` | 58 | ✅ Complet |
| `generators/common/type_encoders/float_encoder.py` | 49 | ✅ Complet |
| `generators/common/type_encoders/norm_encoder.py` | 76 | ✅ Complet |
| `generators/common/type_encoders/string_encoder.py` | 40 | ✅ Complet |
| **Total type_encoders** | **349** | |

**Note** : Renommé de `types/` à `type_encoders/` pour éviter conflit avec module Python builtin `types`.

### 1.3c Fichiers Existants - TypeDecoders (COMPLET ✅)

| Fichier | Lignes | État |
|---------|--------|------|
| `generators/common/type_decoders/__init__.py` | 26 | ✅ Complet |
| `generators/common/type_decoders/base.py` | 56 | ✅ Complet |
| `generators/common/type_decoders/bool_decoder.py` | 36 | ✅ Complet |
| `generators/common/type_decoders/integer_decoder.py` | 58 | ✅ Complet |
| `generators/common/type_decoders/float_decoder.py` | 50 | ✅ Complet |
| `generators/common/type_decoders/norm_decoder.py` | 65 | ✅ Complet |
| `generators/common/type_decoders/string_decoder.py` | 44 | ✅ Complet |
| **Total type_decoders** | **335** | |

### 1.4 Fichiers Existants - Templates (COMPLET ✅)

| Fichier | Lignes | État |
|---------|--------|------|
| `generators/templates/__init__.py` | 26 | ✅ Complet |
| `generators/templates/encoder.py` | 173 | ✅ Complet (refactoré de 601L) |
| `generators/templates/decoder.py` | 170 | ✅ Complet (Phase 3.8) |
| **Total templates** | **369** | |

**Refactoring effectué** :
- Phase 3.6: EncoderTemplate (602 → 173 lignes, -71%)
- Phase 3.8: DecoderTemplate (nouveau, utilise TypeDecoders)

### 1.5 Fichiers À Supprimer (encoder_generator.py)

| Fichier | Lignes | Raison |
|---------|--------|--------|
| `serial8/cpp/encoder_generator.py` | 273 | Remplacé par EncoderTemplate |
| `serial8/java/encoder_generator.py` | 339 | Remplacé par EncoderTemplate |
| `sysex/cpp/encoder_generator.py` | 298 | Remplacé par EncoderTemplate |
| `sysex/java/encoder_generator.py` | 593 | Remplacé par EncoderTemplate |
| **Total à supprimer** | **1,503** | |

### 1.6 Fichiers Common Inchangés

| Fichier | Lignes | Rôle |
|---------|--------|------|
| `common/cpp/struct_utils.py` | 741 | Génération structs C++ |
| `common/java/struct_utils.py` | 1,104 | Génération structs Java |
| `common/cpp/codec_utils.py` | 122 | Utilitaires codecs C++ |
| `common/java/codec_utils.py` | 49 | Utilitaires codecs Java |
| `common/naming.py` | 107 | Conventions nommage |
| `common/payload_calculator.py` | 175 | Calcul tailles payload |
| **Total inchangé** | **2,298** | |

### 1.7 Tests Existants

```
405 tests passent ✅ (+37 nouveaux tests Phase 3.3-3.5)
```

**Nouveaux tests ajoutés** :
- `tests/generators/common/encoding/test_operations.py` (10 tests)
- `tests/generators/common/type_encoders/test_bool_encoder.py` (4 tests)
- `tests/generators/common/type_encoders/test_integer_encoder.py` (9 tests)
- `tests/generators/common/type_encoders/test_float_encoder.py` (4 tests)
- `tests/generators/common/type_encoders/test_norm_encoder.py` (6 tests)
- `tests/generators/common/type_encoders/test_string_encoder.py` (4 tests)

---

## 2. Architecture Cible

### 2.1 Problème Actuel

```
EncoderTemplate (601 lignes)
├── Logique bool (C++ + Java mélangés)
├── Logique integer (C++ + Java mélangés)
├── Logique float (C++ + Java mélangés)
├── Logique norm (C++ + Java mélangés)
└── Logique string (C++ + Java mélangés)
```

**Violation** : Single Responsibility Principle - une classe fait tout.

### 2.2 Architecture Cible

```
┌─────────────────────────────────────────────────────────────┐
│                    TYPE ENCODERS                            │
│  Pattern d'encodage par type (injection de EncodingStrategy)│
├─────────────┬───────────┬───────────┬───────────┬──────────┤
│ BoolEncoder │IntEncoder │FloatEnc   │ NormEnc   │StringEnc │
│   (40 L)    │  (60 L)   │  (50 L)   │  (60 L)   │  (50 L)  │
└──────┬──────┴─────┬─────┴─────┬─────┴─────┬─────┴────┬─────┘
       └────────────┴───────────┴───────────┴──────────┘
                              │
                              │ MethodSpec (dataclass)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  LANGUAGE BACKENDS                          │
│  render_encoder_method(spec: MethodSpec) -> str             │
├────────────────────────────┬────────────────────────────────┤
│   CppBackend (+80 L)       │   JavaBackend (+80 L)          │
│   *buf++ = expr;           │   buffer[i] = (byte)expr;      │
└────────────────────────────┴────────────────────────────────┘
```

### 2.3 Flux de Données

```
TypeRegistry ─────► TypeEncoder ─────► MethodSpec ─────► Backend ─────► Code
                         │                                   │
                         │ injection                         │ type mapping
                         ▼                                   ▼
                  EncodingStrategy                    TypeRegistry
                  (Serial8/SysEx)                   (cpp_type/java_type)
```

### 2.4 Responsabilités Clarifiées

| Composant | Responsabilité | Ne fait PAS |
|-----------|---------------|-------------|
| **TypeEncoder** | Logique d'encodage pour un pattern de type | Syntaxe langage |
| **EncodingStrategy** | Paramètres du protocol (masks, shifts) | Logique d'encodage |
| **MethodSpec** | Représentation intermédiaire (expressions) | Rendu syntaxique |
| **LanguageBackend** | Syntaxe du langage cible | Logique d'encodage |

### 2.5 Bénéfices Quantifiés

| Action | Avant | Après |
|--------|-------|-------|
| Ajouter Rust | 12+ fichiers | 1 fichier `RustBackend` (~300L) |
| Ajouter WebSocket | 12+ fichiers | 1 fichier `WebSocketStrategy` (~150L) |
| Ajouter int64 | 4+ fichiers | Modifier `IntegerEncoder` (+20L) |
| Duplication | ~26% | <5% |

---

## 3. Plan d'Exécution Détaillé

### Phase 3.3 : MethodSpec (Représentation Intermédiaire) ✅ COMPLÈTE

**Objectif** : Créer la structure de données qui découple TypeEncoder du Backend.

**Fichier créé** : `generators/common/encoding/operations.py` (52 lignes)

```python
"""
Encoding Operations - Intermediate representation for code generation.

These dataclasses represent abstract encoding operations that are
language-agnostic. They are produced by TypeEncoders and consumed
by LanguageBackends to generate final code.
"""

from __future__ import annotations

from dataclasses import dataclass


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
        byte_count: Number of bytes in encoded form
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
```

**Fichier à créer** : `tests/generators/common/encoding/test_operations.py`

```python
"""Tests for encoding operations."""

import pytest

from protocol_codegen.generators.common.encoding.operations import (
    ByteWriteOp,
    MethodSpec,
)


class TestByteWriteOp:
    def test_create(self) -> None:
        op = ByteWriteOp(index=0, expression="val & 0xFF")
        assert op.index == 0
        assert op.expression == "val & 0xFF"

    def test_immutable(self) -> None:
        op = ByteWriteOp(index=0, expression="val & 0xFF")
        with pytest.raises(AttributeError):
            op.index = 1  # type: ignore


class TestMethodSpec:
    def test_create_simple(self) -> None:
        spec = MethodSpec(
            type_name="uint8",
            method_name="Uint8",
            param_type="uint8",
            byte_count=1,
            byte_writes=(ByteWriteOp(0, "val & 0xFF"),),
            doc_comment="8-bit unsigned integer",
        )
        assert spec.type_name == "uint8"
        assert spec.byte_count == 1
        assert len(spec.byte_writes) == 1

    def test_with_preamble(self) -> None:
        spec = MethodSpec(
            type_name="float32",
            method_name="Float32",
            param_type="float32",
            byte_count=4,
            byte_writes=(
                ByteWriteOp(0, "bits & 0xFF"),
                ByteWriteOp(1, "(bits >> 8) & 0xFF"),
                ByteWriteOp(2, "(bits >> 16) & 0xFF"),
                ByteWriteOp(3, "(bits >> 24) & 0xFF"),
            ),
            doc_comment="IEEE 754 float",
            preamble="uint32_t bits; memcpy(&bits, &val, sizeof(float));",
        )
        assert spec.preamble is not None
        assert "memcpy" in spec.preamble
```

**Modification** : `generators/common/encoding/__init__.py`

Ajouter export :
```python
from .operations import ByteWriteOp, MethodSpec
```

**Validation Phase 3.3** :
```bash
pytest tests/generators/common/encoding/test_operations.py -v
ruff check src/protocol_codegen/generators/common/encoding/operations.py
```

---

### Phase 3.4 : TypeEncoders ✅ COMPLÈTE

**Objectif** : Extraire la logique d'encodage de `EncoderTemplate` en classes dédiées.

**Structure créée** (renommé `types/` → `type_encoders/` pour éviter conflit Python builtin):
```
generators/common/type_encoders/
├── __init__.py              (26 lignes)
├── base.py                  (56 lignes)
├── bool_encoder.py          (44 lignes)
├── integer_encoder.py       (58 lignes)
├── float_encoder.py         (49 lignes)
├── norm_encoder.py          (76 lignes)
└── string_encoder.py        (40 lignes)
Total: 349 lignes
```

**Fichier** : `generators/common/type_encoders/base.py`

```python
"""
Type Encoder Base Class.

Defines the interface for type-specific encoding logic.
Each TypeEncoder knows how to produce a MethodSpec for its supported types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from protocol_codegen.generators.common.encoding import EncodingStrategy
    from protocol_codegen.generators.common.encoding.operations import MethodSpec


class TypeEncoder(ABC):
    """Base class for type-specific encoding logic.

    TypeEncoders are responsible for producing MethodSpecs that describe
    HOW to encode a type. They use an injected EncodingStrategy to get
    protocol-specific parameters (masks, shifts, byte counts).

    The MethodSpec is then rendered to actual code by a LanguageBackend.
    """

    def __init__(self, strategy: EncodingStrategy) -> None:
        """Initialize with encoding strategy.

        Args:
            strategy: Protocol-specific encoding parameters
        """
        self.strategy = strategy

    @abstractmethod
    def supported_types(self) -> tuple[str, ...]:
        """Return type names this encoder handles.

        Returns:
            Tuple of protocol-codegen type names (e.g., ("uint8", "uint16"))
        """
        ...

    @abstractmethod
    def get_method_spec(self, type_name: str, description: str) -> MethodSpec:
        """Generate method specification for the given type.

        Args:
            type_name: Protocol-codegen type name
            description: Human-readable description from TypeRegistry

        Returns:
            MethodSpec describing how to encode this type

        Raises:
            ValueError: If type_name is not in supported_types()
        """
        ...
```

**Fichier** : `generators/common/types/integer_encoder.py`

```python
"""
Integer Type Encoder.

Handles encoding of integer types: uint8, int8, uint16, int16, uint32, int32.
Uses EncodingStrategy to get protocol-specific byte layout.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from protocol_codegen.generators.common.encoding.operations import (
    ByteWriteOp,
    MethodSpec,
)
from protocol_codegen.generators.common.types.base import TypeEncoder

if TYPE_CHECKING:
    pass


class IntegerEncoder(TypeEncoder):
    """Encoder for integer types."""

    def supported_types(self) -> tuple[str, ...]:
        return ("uint8", "int8", "uint16", "int16", "uint32", "int32")

    def get_method_spec(self, type_name: str, description: str) -> MethodSpec:
        if type_name not in self.supported_types():
            raise ValueError(f"Unsupported type: {type_name}")

        spec = self.strategy.get_integer_spec(type_name)
        if not spec:
            raise ValueError(f"No integer spec for {type_name}")

        # Build byte write operations
        byte_writes = tuple(
            ByteWriteOp(
                index=i,
                expression=(
                    f"val & 0x{mask:02X}"
                    if shift == 0
                    else f"(val >> {shift}) & 0x{mask:02X}"
                ),
            )
            for i, (shift, mask) in enumerate(zip(spec.shifts, spec.masks, strict=True))
        )

        # Signed types need cast to unsigned
        needs_signed_cast = type_name.startswith("int") and spec.byte_count > 1

        return MethodSpec(
            type_name=type_name,
            method_name=type_name.capitalize(),
            param_type=type_name,
            byte_count=spec.byte_count,
            byte_writes=byte_writes,
            doc_comment=f"{description} ({spec.comment})",
            needs_signed_cast=needs_signed_cast,
        )
```

**Fichier** : `generators/common/types/bool_encoder.py`

```python
"""
Bool Type Encoder.

Handles encoding of boolean values using strategy-specific true/false values.
"""

from __future__ import annotations

from protocol_codegen.generators.common.encoding.operations import (
    ByteWriteOp,
    MethodSpec,
)
from protocol_codegen.generators.common.types.base import TypeEncoder


class BoolEncoder(TypeEncoder):
    """Encoder for boolean type."""

    def supported_types(self) -> tuple[str, ...]:
        return ("bool",)

    def get_method_spec(self, type_name: str, description: str) -> MethodSpec:
        if type_name != "bool":
            raise ValueError(f"Unsupported type: {type_name}")

        true_val = self.strategy.bool_true_value
        false_val = self.strategy.bool_false_value

        return MethodSpec(
            type_name="bool",
            method_name="Bool",
            param_type="bool",
            byte_count=1,
            byte_writes=(
                ByteWriteOp(
                    index=0,
                    expression=f"val ? 0x{true_val:02X} : 0x{false_val:02X}",
                ),
            ),
            doc_comment=f"{description} (0x{false_val:02X} or 0x{true_val:02X})",
        )
```

**Fichier** : `generators/common/types/float_encoder.py`

```python
"""
Float Type Encoder.

Handles encoding of float32 using bitcast to uint32 then integer encoding.
"""

from __future__ import annotations

from protocol_codegen.generators.common.encoding.operations import (
    ByteWriteOp,
    MethodSpec,
)
from protocol_codegen.generators.common.types.base import TypeEncoder


class FloatEncoder(TypeEncoder):
    """Encoder for float32 type."""

    def supported_types(self) -> tuple[str, ...]:
        return ("float32",)

    def get_method_spec(self, type_name: str, description: str) -> MethodSpec:
        if type_name != "float32":
            raise ValueError(f"Unsupported type: {type_name}")

        # Float uses same encoding as uint32 after bitcast
        spec = self.strategy.get_integer_spec("float32")
        if not spec:
            raise ValueError("No float32 spec in strategy")

        byte_writes = tuple(
            ByteWriteOp(
                index=i,
                expression=(
                    f"bits & 0x{mask:02X}"
                    if shift == 0
                    else f"(bits >> {shift}) & 0x{mask:02X}"
                ),
            )
            for i, (shift, mask) in enumerate(zip(spec.shifts, spec.masks, strict=True))
        )

        return MethodSpec(
            type_name="float32",
            method_name="Float32",
            param_type="float32",
            byte_count=spec.byte_count,
            byte_writes=byte_writes,
            doc_comment=f"{description} ({spec.comment})",
            preamble="uint32_t bits; memcpy(&bits, &val, sizeof(float));",
        )
```

**Fichier** : `generators/common/types/norm_encoder.py`

```python
"""
Norm Type Encoder.

Handles encoding of norm8 and norm16 (normalized floats).
"""

from __future__ import annotations

from protocol_codegen.generators.common.encoding.operations import (
    ByteWriteOp,
    MethodSpec,
)
from protocol_codegen.generators.common.types.base import TypeEncoder


class NormEncoder(TypeEncoder):
    """Encoder for normalized float types."""

    def supported_types(self) -> tuple[str, ...]:
        return ("norm8", "norm16")

    def get_method_spec(self, type_name: str, description: str) -> MethodSpec:
        if type_name not in self.supported_types():
            raise ValueError(f"Unsupported type: {type_name}")

        spec = self.strategy.get_norm_spec(type_name)
        if not spec:
            raise ValueError(f"No norm spec for {type_name}")

        max_val = spec.max_value

        if spec.byte_count == 1:
            # Single byte norm
            byte_mask = 0x7F if max_val == 127 else 0xFF
            return MethodSpec(
                type_name=type_name,
                method_name=type_name.capitalize(),
                param_type=type_name,
                byte_count=1,
                byte_writes=(
                    ByteWriteOp(
                        index=0,
                        expression=f"static_cast<uint8_t>(val * {max_val}.0f + 0.5f) & 0x{byte_mask:02X}",
                    ),
                ),
                doc_comment=f"{description} ({spec.comment})",
                preamble="if (val < 0.0f) val = 0.0f; if (val > 1.0f) val = 1.0f;",
            )
        else:
            # Multi-byte norm uses integer spec
            int_spec = spec.integer_spec
            if not int_spec:
                raise ValueError(f"No integer spec for {type_name}")

            byte_writes = tuple(
                ByteWriteOp(
                    index=i,
                    expression=(
                        f"norm & 0x{mask:02X}"
                        if shift == 0
                        else f"(norm >> {shift}) & 0x{mask:02X}"
                    ),
                )
                for i, (shift, mask) in enumerate(
                    zip(int_spec.shifts, int_spec.masks, strict=True)
                )
            )

            return MethodSpec(
                type_name=type_name,
                method_name=type_name.capitalize(),
                param_type=type_name,
                byte_count=spec.byte_count,
                byte_writes=byte_writes,
                doc_comment=f"{description} ({spec.comment})",
                preamble=f"if (val < 0.0f) val = 0.0f; if (val > 1.0f) val = 1.0f; uint16_t norm = static_cast<uint16_t>(val * {max_val}.0f + 0.5f);",
            )
```

**Fichier** : `generators/common/types/string_encoder.py`

```python
"""
String Type Encoder.

Handles encoding of variable-length strings with length prefix.
"""

from __future__ import annotations

from protocol_codegen.generators.common.encoding.operations import MethodSpec
from protocol_codegen.generators.common.types.base import TypeEncoder


class StringEncoder(TypeEncoder):
    """Encoder for string type."""

    def supported_types(self) -> tuple[str, ...]:
        return ("string",)

    def get_method_spec(self, type_name: str, description: str) -> MethodSpec:
        if type_name != "string":
            raise ValueError(f"Unsupported type: {type_name}")

        spec = self.strategy.get_string_spec()

        # String is special - uses loop, not fixed byte writes
        # We encode this in the preamble and leave byte_writes empty
        # The backend will handle the special case

        return MethodSpec(
            type_name="string",
            method_name="String",
            param_type="string",
            byte_count=-1,  # Variable length
            byte_writes=(),  # Special handling by backend
            doc_comment=f"{description} ({spec.comment})",
            preamble=f"LENGTH_MASK=0x{spec.length_mask:02X};CHAR_MASK=0x{spec.char_mask:02X};MAX_LENGTH={spec.max_length}",
        )
```

**Fichier** : `generators/common/types/__init__.py`

```python
"""
Type Encoders.

This package provides type-specific encoding logic that produces
MethodSpecs for the LanguageBackend to render.
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
```

**Tests** : `tests/generators/common/types/test_integer_encoder.py` (exemple)

```python
"""Tests for IntegerEncoder."""

import pytest

from protocol_codegen.generators.common.encoding import Serial8EncodingStrategy
from protocol_codegen.generators.common.types import IntegerEncoder


class TestIntegerEncoderSerial8:
    @pytest.fixture
    def encoder(self) -> IntegerEncoder:
        return IntegerEncoder(Serial8EncodingStrategy())

    def test_supported_types(self, encoder: IntegerEncoder) -> None:
        assert "uint8" in encoder.supported_types()
        assert "uint16" in encoder.supported_types()
        assert "uint32" in encoder.supported_types()

    def test_uint8_spec(self, encoder: IntegerEncoder) -> None:
        spec = encoder.get_method_spec("uint8", "8-bit unsigned")
        assert spec.byte_count == 1
        assert len(spec.byte_writes) == 1
        assert spec.byte_writes[0].expression == "val & 0xFF"

    def test_uint16_spec(self, encoder: IntegerEncoder) -> None:
        spec = encoder.get_method_spec("uint16", "16-bit unsigned")
        assert spec.byte_count == 2
        assert len(spec.byte_writes) == 2
        assert "val & 0xFF" in spec.byte_writes[0].expression
        assert "(val >> 8)" in spec.byte_writes[1].expression

    def test_unsupported_type_raises(self, encoder: IntegerEncoder) -> None:
        with pytest.raises(ValueError, match="Unsupported type"):
            encoder.get_method_spec("float32", "not an integer")
```

**Validation Phase 3.4** :
```bash
pytest tests/generators/common/types/ -v
ruff check src/protocol_codegen/generators/common/types/
```

---

### Phase 3.5 : Backend Render Methods ✅ COMPLÈTE

**Objectif** : Ajouter `render_encoder_method()` aux backends.

**Modifications effectuées** :
- `generators/backends/base.py` : +20 lignes (méthode abstraite)
- `generators/backends/cpp.py` : +86 lignes (implémentation C++)
- `generators/backends/java.py` : +88 lignes (implémentation Java)

**Modification** : `generators/backends/base.py`

Ajouter après `decode_call()` :

```python
    # ─────────────────────────────────────────────────────────────
    # Method Rendering
    # ─────────────────────────────────────────────────────────────

    @abstractmethod
    def render_encoder_method(
        self,
        spec: "MethodSpec",
        registry: "TypeRegistry",
    ) -> str:
        """Render a MethodSpec to language-specific encoder code.

        Args:
            spec: Language-agnostic method specification
            registry: Type registry for type mapping

        Returns:
            Complete encoder method as string
        """
        ...
```

**Modification** : `generators/backends/cpp.py` (+80 lignes)

Ajouter méthode :

```python
    def render_encoder_method(
        self,
        spec: MethodSpec,
        registry: TypeRegistry,
    ) -> str:
        """Render encoder method for C++."""
        cpp_type = self.get_type(spec.param_type, registry)
        method_name = f"encode{spec.method_name}"

        # Handle string specially
        if spec.type_name == "string":
            return self._render_cpp_string_encoder(spec)

        # Build body from byte writes
        if spec.needs_signed_cast:
            unsigned_type = cpp_type.replace("int", "uint")
            preamble = f"    {unsigned_type} val = static_cast<{unsigned_type}>(value);\n"
            param_name = "value"
        else:
            preamble = f"    {spec.preamble}\n" if spec.preamble else ""
            param_name = "val"

        lines = [f"    *buf++ = {op.expression};" for op in spec.byte_writes]
        body = "\n".join(lines)

        return f"""
/**
 * Encode {spec.type_name} ({spec.byte_count} bytes)
 * {spec.doc_comment}
 */
static inline void {method_name}(uint8_t*& buf, {cpp_type} {param_name}) {{
{preamble}{body}
}}
"""

    def _render_cpp_string_encoder(self, spec: MethodSpec) -> str:
        """Render C++ string encoder (special case)."""
        # Parse preamble for masks
        parts = dict(p.split("=") for p in spec.preamble.split(";") if "=" in p)
        length_mask = parts.get("LENGTH_MASK", "0xFF")
        char_mask = parts.get("CHAR_MASK", "0xFF")
        max_length = parts.get("MAX_LENGTH", "255")

        return f"""
/**
 * Encode string (variable length)
 * {spec.doc_comment}
 *
 * Format: [length] [char0] [char1] ... [charN-1]
 * Max length: {max_length} chars
 */
static inline void encodeString(uint8_t*& buf, const std::string& str) {{
    uint8_t len = static_cast<uint8_t>(str.length()) & {length_mask};
    *buf++ = len;

    for (size_t i = 0; i < len; ++i) {{
        *buf++ = static_cast<uint8_t>(str[i]) & {char_mask};
    }}
}}
"""
```

**Modification** : `generators/backends/java.py` (+80 lignes)

Similaire avec syntaxe Java :
- `buffer[offset + i] = (byte)(expr);`
- `return byteCount;`

**Validation Phase 3.5** :
```bash
pytest tests/generators/backends/ -v
ruff check src/protocol_codegen/generators/backends/
```

---

### Phase 3.6 : Refactor EncoderTemplate ✅ COMPLÈTE

**Objectif** : Simplifier `EncoderTemplate` de 601 → ~120 lignes.

**Résultat** : 602 → 173 lignes (-71%)

**Avant** (encoder.py) :
- 23 méthodes
- Logique + rendu mélangés
- Duplication C++/Java dans chaque méthode

**Après** (encoder.py) :
```python
"""
Encoder Template.

Orchestrates TypeEncoders and LanguageBackend to generate encoder files.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from protocol_codegen.generators.common.types import (
    BoolEncoder,
    FloatEncoder,
    IntegerEncoder,
    NormEncoder,
    StringEncoder,
)

if TYPE_CHECKING:
    from protocol_codegen.core.loader import TypeRegistry
    from protocol_codegen.generators.backends.base import LanguageBackend
    from protocol_codegen.generators.common.encoding import EncodingStrategy


class EncoderTemplate:
    """Template for generating Encoder files.

    Combines:
    - TypeEncoders: produce MethodSpecs (what to encode)
    - LanguageBackend: renders MethodSpecs (how to write it)
    """

    def __init__(
        self,
        backend: LanguageBackend,
        strategy: EncodingStrategy,
    ) -> None:
        self.backend = backend
        self.strategy = strategy
        self.encoders = [
            BoolEncoder(strategy),
            IntegerEncoder(strategy),
            FloatEncoder(strategy),
            NormEncoder(strategy),
            StringEncoder(strategy),
        ]

    def generate(self, type_registry: TypeRegistry, output_path: Path) -> str:
        """Generate complete encoder file."""
        parts = [
            self._generate_header(output_path),
            self._generate_class_open(),
            self._generate_encoder_methods(type_registry),
            self._generate_class_close(),
            self._generate_footer(),
        ]
        return "\n".join(filter(None, parts))

    def _generate_header(self, output_path: Path) -> str:
        """Generate file header."""
        # Keep existing logic from current encoder.py
        ...

    def _generate_class_open(self) -> str:
        """Generate class/struct opening."""
        if self.backend.name == "cpp":
            return "struct Encoder {"
        elif self.backend.name == "java":
            return "public final class Encoder {"
        return ""

    def _generate_class_close(self) -> str:
        """Generate class/struct closing."""
        return "};" if self.backend.name == "cpp" else "}"

    def _generate_footer(self) -> str:
        """Generate file footer."""
        if self.backend.name == "cpp":
            return "\n}  // namespace Protocol\n"
        return ""

    def _generate_encoder_methods(self, type_registry: TypeRegistry) -> str:
        """Generate all encoder methods using TypeEncoders + Backend."""
        methods: list[str] = []

        for type_name, atomic_type in sorted(type_registry.types.items()):
            if not atomic_type.is_builtin:
                continue

            # Find encoder that supports this type
            for encoder in self.encoders:
                if type_name in encoder.supported_types():
                    spec = encoder.get_method_spec(type_name, atomic_type.description)
                    code = self.backend.render_encoder_method(spec, type_registry)
                    methods.append(code)
                    break

        return "\n".join(methods)
```

**Delta** : -480 lignes (601 → ~120)

**Validation Phase 3.6** :
```bash
# Tests unitaires
pytest tests/generators/templates/test_encoder_template.py -v

# Génération de référence AVANT
python -m protocol_codegen generate sysex \
    --messages-dir examples/messages \
    --config examples/sysex/protocol_config.py \
    --output output_reference/

# Génération avec nouveau code
python -m protocol_codegen generate sysex \
    --messages-dir examples/messages \
    --config examples/sysex/protocol_config.py \
    --output output_test/

# Diff
diff output_reference/cpp/Encoder.hpp output_test/cpp/Encoder.hpp
diff output_reference/java/Encoder.java output_test/java/Encoder.java
```

---

### Phase 3.7 : Refactorer encoder_generator.py ✅ COMPLÈTE

**Objectif** : Convertir les fichiers `encoder_generator.py` en wrappers minces.

**Approche choisie** : Plutôt que supprimer, les fichiers ont été refactorés en wrappers
pour maintenir la compatibilité avec les imports existants dans `methods/*/generator.py`.

**Résultat** :
| Fichier | Avant | Après | Réduction |
|---------|-------|-------|-----------|
| `serial8/cpp/encoder_generator.py` | 274L | 33L | -88% |
| `serial8/java/encoder_generator.py` | ~300L | 36L | -88% |
| `sysex/cpp/encoder_generator.py` | ~350L | 33L | -91% |
| `sysex/java/encoder_generator.py` | ~587L | 36L | -94% |

**Exemple de wrapper** :
```python
def generate_encoder_hpp(type_registry: TypeRegistry, output_path: Path) -> str:
    template = EncoderTemplate(CppBackend(), Serial8EncodingStrategy())
    return template.generate(type_registry, output_path)
```

**Validation Phase 3.7** :
```bash
pytest
ruff check src/
```

---

### Phase 3.8 : DecoderTemplate (même pattern) ✅ COMPLÈTE

**Objectif** : Appliquer le même pattern aux décodeurs.

**Fichiers créés** :
- `generators/common/encoding/operations.py` : +ByteReadOp, +DecoderMethodSpec
- `generators/common/type_decoders/` : 7 fichiers (~300 lignes)
  - base.py, bool_decoder.py, integer_decoder.py, float_decoder.py
  - norm_decoder.py, string_decoder.py, __init__.py
- `generators/backends/*.py` : +render_decoder_method() dans base, cpp, java
- `generators/templates/decoder.py` : 170 lignes

**Fichiers refactorés en wrappers** (~35 lignes chacun):
| Fichier | Avant | Après | Réduction |
|---------|-------|-------|-----------|
| `serial8/cpp/decoder_generator.py` | 335L | 33L | -90% |
| `serial8/java/decoder_generator.py` | 365L | 36L | -90% |
| `sysex/cpp/decoder_generator.py` | 357L | 33L | -91% |
| `sysex/java/decoder_generator.py` | 386L | 36L | -91% |
| **Total** | 1,443L | 138L | **-90%** |

---

### Phase 3.9 : Autres Templates

**Objectif** : Factoriser ConstantsTemplate, etc. si bénéfice significatif.

**Analyse** :
- `constants_generator.py` : ~165-207 L × 4 = ~730 L, ~67% similarité
- Bénéfice potentiel : ~400 L

**Décision** : Optionnel, priorité moindre.

---

### Phase 3.10 : Cleanup et Documentation ✅ COMPLÈTE

**Actions réalisées** :
1. ✅ Supprimer code mort - déjà fait via thin wrappers
2. ✅ Mettre à jour `common/__init__.py` avec exports des nouveaux modules
3. ✅ Fix Pylance warnings (assertions pour preamble/postamble)
4. ℹ️ Documentation dans ce fichier (ARCHITECTURE_REFACTORING_PLAN.md)
5. ✅ 405 tests passent

---

## 4. Inventaire Complet des Fichiers

### 4.1 Fichiers à CRÉER

| Chemin | Lignes | Phase |
|--------|--------|-------|
| `common/encoding/operations.py` | ~80 | 3.3 |
| `common/types/__init__.py` | ~30 | 3.4 |
| `common/types/base.py` | ~50 | 3.4 |
| `common/types/bool_encoder.py` | ~45 | 3.4 |
| `common/types/integer_encoder.py` | ~70 | 3.4 |
| `common/types/float_encoder.py` | ~55 | 3.4 |
| `common/types/norm_encoder.py` | ~65 | 3.4 |
| `common/types/string_encoder.py` | ~55 | 3.4 |
| `tests/generators/common/encoding/test_operations.py` | ~50 | 3.3 |
| `tests/generators/common/types/test_*.py` | ~200 | 3.4 |
| **Total créé** | **~700** | |

### 4.2 Fichiers à MODIFIER

| Chemin | Avant | Après | Delta | Phase |
|--------|-------|-------|-------|-------|
| `backends/base.py` | 257 | 275 | +18 | 3.5 |
| `backends/cpp.py` | 238 | 320 | +82 | 3.5 |
| `backends/java.py` | 292 | 375 | +83 | 3.5 |
| `templates/encoder.py` | 601 | 120 | **-481** | 3.6 |
| `common/encoding/__init__.py` | 56 | 60 | +4 | 3.3 |
| **Total modifications** | **1,444** | **1,150** | **-294** | |

### 4.3 Fichiers à SUPPRIMER

| Chemin | Lignes | Phase |
|--------|--------|-------|
| `serial8/cpp/encoder_generator.py` | 273 | 3.7 |
| `serial8/java/encoder_generator.py` | 339 | 3.7 |
| `sysex/cpp/encoder_generator.py` | 298 | 3.7 |
| `sysex/java/encoder_generator.py` | 593 | 3.7 |
| `serial8/cpp/decoder_generator.py` | 335 | 3.8 |
| `serial8/java/decoder_generator.py` | 365 | 3.8 |
| `sysex/cpp/decoder_generator.py` | 357 | 3.8 |
| `sysex/java/decoder_generator.py` | 386 | 3.8 |
| **Total supprimé** | **2,946** | |

### 4.4 Bilan Net

| Métrique | Valeur |
|----------|--------|
| Lignes créées | +700 |
| Lignes modifiées | -294 |
| Lignes supprimées | -2,946 |
| **Delta net** | **-2,540** |

---

## 5. Conventions de Nommage

### 5.1 Modules

| Pattern | Exemple | Usage |
|---------|---------|-------|
| `backends/{lang}.py` | `backends/cpp.py` | Un backend par langage |
| `templates/{artifact}.py` | `templates/encoder.py` | Un template par artifact |
| `common/types/{type}_encoder.py` | `common/types/integer_encoder.py` | Un encoder par pattern |

### 5.2 Classes

| Pattern | Exemple | Usage |
|---------|---------|-------|
| `{Lang}Backend` | `CppBackend`, `JavaBackend` | Backend de langage |
| `{Type}Encoder` | `IntegerEncoder`, `BoolEncoder` | Encoder de type |
| `{Artifact}Template` | `EncoderTemplate`, `DecoderTemplate` | Template orchestrateur |
| `{Spec}` | `MethodSpec`, `ByteWriteOp` | Dataclass intermédiaire |

### 5.3 Méthodes

| Pattern | Exemple | Usage |
|---------|---------|-------|
| `get_{thing}` | `get_method_spec()`, `get_integer_spec()` | Accesseur |
| `render_{thing}` | `render_encoder_method()` | Rendu syntaxique |
| `supported_types()` | `supported_types()` | Types gérés |
| `_generate_{part}` | `_generate_header()` | Génération interne |

---

## 6. Risques et Mitigations

### 6.1 Risques Techniques

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Régression output | Moyenne | Élevé | Diff systématique avant/après |
| Expressions non portables | Faible | Moyen | Tests sur les deux backends |
| String encoder spécial | Moyenne | Moyen | Gérer cas spécial dans backend |

### 6.2 Risques Projet

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Scope creep | Moyenne | Moyen | Phases bien définies |
| Tests insuffisants | Faible | Élevé | 368 tests existants + nouveaux |

---

## 7. Validation Continue

### 7.1 Après Chaque Phase

```bash
# 1. Tests unitaires
pytest -v

# 2. Lint
ruff check src/

# 3. Type check (si configuré)
# mypy src/

# 4. Génération de référence
python -m protocol_codegen generate sysex \
    --messages-dir examples/messages \
    --config examples/sysex/protocol_config.py \
    --output output_test/

# 5. Diff
diff -r output_reference/ output_test/
```

### 7.2 Avant Merge Final

```bash
# Tests complets
pytest

# Génération Serial8 + SysEx
python -m protocol_codegen generate serial8 --output output_serial8/
python -m protocol_codegen generate sysex --output output_sysex/

# Diff avec références
diff -r output_reference_serial8/ output_serial8/
diff -r output_reference_sysex/ output_sysex/
```

---

## 8. Résumé Exécutif

### Effort par Phase

| Phase | Description | Lignes | Estimé |
|-------|-------------|--------|--------|
| 3.3 | MethodSpec | +80 | 0.5j |
| 3.4 | TypeEncoders | +370 | 1j |
| 3.5 | Backend render | +180 | 0.5j |
| 3.6 | EncoderTemplate refactor | -481 | 0.5j |
| 3.7 | Supprimer encoder_generator | -1,503 | 0.25j |
| 3.8 | DecoderTemplate | +370/-1,443 | 1j |
| 3.9 | Autres templates | optionnel | 0.5j |
| 3.10 | Cleanup | - | 0.25j |
| **Total** | | **-2,540** | **4.5j** |

### Bénéfices

- **Duplication** : 26% → <5%
- **Nouveau langage** : 12+ fichiers → 1 fichier
- **Nouveau protocol** : 12+ fichiers → 1 fichier
- **Maintenabilité** : Responsabilités séparées
