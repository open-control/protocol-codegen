# Plan de Refactorisation Architecturale - Protocol Codegen

> **Version** : 1.1
> **Date** : 2026-01-01
> **Dernière mise à jour** : 2026-01-01
> **Objectif** : Architecture extensible multi-langages / multi-protocoles

---

## 📊 Suivi d'Avancement

### État Global

| Métrique | Valeur |
|----------|--------|
| **Phase actuelle** | 3.2c (Refactor encoder generators) |
| **Tests** | 368 passent ✅ |
| **Nouveaux fichiers** | 6 |
| **Nouvelles lignes** | ~1,540 |
| **Branche** | `feature/extensible-architecture` |

### Progression des Phases

| Phase | Description | Status | Commit | Lignes |
|-------|-------------|--------|--------|--------|
| 3.0 | Préparation (tag, branche) | ✅ Done | `v2.0-pre-extensibility` | - |
| 3.1 | LanguageBackend (CppBackend, JavaBackend) | ✅ Done | `eef4cb4` | +700 |
| 3.2a | Encoding specs dans EncodingStrategy | ✅ Done | `2fbb1d6` | +343 |
| 3.2b | EncoderTemplate | ✅ Done | `7574e01` | +500 |
| 3.2c | Refactor 4 encoder_generator.py | ⏳ Pending | - | -1,300 est. |
| 3.3 | DecoderTemplate | ⏳ Pending | - | +350 est. |
| 3.4 | ConstantsTemplate | ⏳ Pending | - | +150 est. |
| 3.5 | FileManifest + Pipeline | ⏳ Pending | - | +250 est. |
| 3.6 | Consolidation generators | ⏳ Pending | - | -400 est. |
| 3.7 | Cleanup + docs | ⏳ Pending | - | - |

### Fichiers Créés (Phase 3.1-3.2)

```
src/protocol_codegen/generators/
├── backends/
│   ├── __init__.py          ✅ (55 lignes)
│   ├── base.py               ✅ (210 lignes) - LanguageBackend ABC
│   ├── cpp.py                ✅ (217 lignes) - CppBackend
│   └── java.py               ✅ (223 lignes) - JavaBackend
└── templates/
    ├── __init__.py           ✅ (20 lignes)
    └── encoder.py            ✅ (500 lignes) - EncoderTemplate

tests/generators/
├── backends/
│   ├── test_cpp_backend.py   ✅ (188 lignes)
│   ├── test_java_backend.py  ✅ (195 lignes)
│   └── test_backend_factory.py ✅ (41 lignes)
└── templates/
    └── test_encoder_template.py ✅ (150 lignes)
```

### Fichiers Modifiés (Phase 3.2a)

```
src/protocol_codegen/generators/common/encoding/
├── strategy.py               ✅ +114 lignes (IntegerEncodingSpec, NormEncodingSpec, StringEncodingSpec)
├── serial8_strategy.py       ✅ +103 lignes (encoding specs)
└── sysex_strategy.py         ✅ +103 lignes (encoding specs)
```

---

## Table des Matières

1. [Analyse de l'Existant](#1-analyse-de-lexistant)
2. [Architecture Cible](#2-architecture-cible)
3. [Décision: Refactoring vs Réécriture](#3-décision-refactoring-vs-réécriture)
4. [Plan d'Exécution Détaillé](#4-plan-dexécution-détaillé)
5. [Inventaire Complet des Fichiers](#5-inventaire-complet-des-fichiers)
6. [Conventions de Nommage](#6-conventions-de-nommage)
7. [Risques et Mitigations](#7-risques-et-mitigations)

---

## 1. Analyse de l'Existant

### 1.1 Métriques Actuelles

| Catégorie | Fichiers | Lignes | % du Total |
|-----------|----------|--------|------------|
| **Core** (stable) | 13 | 1,574 | 12% |
| **Common** (factorisé) | 22 | 3,609 | 27% |
| **Serial8** (protocol-specific) | 12 | 2,595 | 19% |
| **SysEx** (protocol-specific) | 13 | 3,304 | 25% |
| **Methods** (orchestration) | 8 | 1,408 | 10% |
| **CLI/Entry** | 4 | 322 | 2% |
| **Autres** (__init__, etc.) | 7 | 604 | 5% |
| **TOTAL** | **79** | **13,416** | 100% |

### 1.2 Duplication Identifiée

| Générateur | Serial8 | SysEx | Diff | Similaire |
|------------|---------|-------|------|-----------|
| cpp/encoder | 273 | 298 | 137 | 76% |
| cpp/decoder | 335 | 357 | 160 | 77% |
| cpp/constants | 164 | 207 | 121 | 67% |
| cpp/protocol | 214 | 272 | 296 | 39% |
| cpp/decoder_registry | 142 | 142 | 284 | 0% |
| java/encoder | 339 | 593 | 430 | 54% |
| java/decoder | 365 | 386 | 139 | 81% |
| java/constants | 158 | 204 | 120 | 67% |
| java/protocol | 279 | 253 | 334 | 37% |
| **methods/generator** | 375 | 397 | ~40 | 95% |

**Duplication totale estimée : ~3,500 lignes (26%)**

### 1.3 Points Forts Existants

- ✅ `EncodingStrategy` - Pattern Strategy pour encodage (7-bit vs 8-bit)
- ✅ `BaseProtocolGenerator` - Template Method pour pipeline
- ✅ `common/cpp/struct_utils.py` - Factorisation réussie
- ✅ `common/java/struct_utils.py` - Factorisation réussie
- ✅ `PayloadCalculator` - Calcul de taille paramétré

### 1.4 Points Faibles

- ❌ Pas d'abstraction `LanguageBackend` pour syntaxe/idiomes
- ❌ Encoders/Decoders dupliqués (templates inline)
- ❌ `_generate_cpp()` / `_generate_java()` identiques à 95%
- ❌ Pas de registre de générateurs (discovery)
- ❌ Constants/Protocol generators partiellement dupliqués

---

## 2. Architecture Cible

### 2.1 Vision

```
                    ┌─────────────────────────────────────────┐
                    │           Protocol Codegen              │
                    └─────────────────────────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         │                             │                             │
         ▼                             ▼                             ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  LanguageBackend │         │ EncodingStrategy│         │  FileManifest   │
│  (syntaxe)       │         │ (protocole)     │         │  (orchestration)│
└─────────────────┘         └─────────────────┘         └─────────────────┘
         │                             │                             │
    ┌────┴────┐                   ┌────┴────┐                        │
    ▼         ▼                   ▼         ▼                        ▼
┌──────┐  ┌──────┐          ┌────────┐ ┌────────┐           ┌────────────────┐
│ Cpp  │  │ Java │          │ Serial8│ │ SysEx  │           │ BaseGenerator  │
│Backend│ │Backend│         │Strategy│ │Strategy│           │ (générique)    │
└──────┘  └──────┘          └────────┘ └────────┘           └────────────────┘
    │         │                   │         │                        │
    └────┬────┘                   └────┬────┘                        │
         │                             │                             │
         ▼                             ▼                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CodeGenerator                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │ EncoderTemplate │  │ DecoderTemplate │  │  StructTemplate │  ...         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Principes

1. **Séparation des préoccupations**
   - `LanguageBackend` : syntaxe, types, imports, idiomes
   - `EncodingStrategy` : tailles, transformations d'encodage
   - `Template` : logique de génération commune

2. **Composition plutôt qu'héritage**
   - `CodeGenerator = Backend + Strategy + Template`
   - Pas de hiérarchie de classes profonde

3. **Convention over Configuration**
   - Naming cohérent permet discovery automatique
   - Manifests déclaratifs pour fichiers à générer

---

## 3. Décision: Refactoring vs Réécriture

### 3.1 Critères d'Évaluation

| Critère | Refactoring Incrémental | Réécriture From Scratch |
|---------|------------------------|-------------------------|
| **Risque** | Faible (tests existants) | Élevé (nouveaux bugs) |
| **Temps** | ~5-7 jours | ~10-15 jours |
| **Continuité** | Toujours fonctionnel | Période non-fonctionnelle |
| **Tests** | Réutilisables | À adapter |
| **Complexité** | Migration graduelle | Architecture propre |
| **Dette technique** | Résiduelle possible | Minimale |

### 3.2 Recommandation : REFACTORING INCRÉMENTAL

**Justification :**

1. **250 tests existants** → filet de sécurité
2. **Core stable** (1,574 lignes) → pas besoin de toucher
3. **struct_utils déjà factorisés** → preuve que l'approche marche
4. **70%+ de similarité** → extraction mécaniquede patterns
5. **Production active** → pas de période d'indisponibilité

### 3.3 Snapshot de Référence

Avant de commencer, créer un tag Git :

```bash
git tag -a v2.0-pre-refactoring -m "Snapshot before architecture refactoring"
```

---

## 4. Plan d'Exécution Détaillé

### Phase 3.0 : Préparation (0.5 jour)

| Étape | Action | Fichiers |
|-------|--------|----------|
| 3.0.1 | Créer tag Git `v2.0-pre-refactoring` | - |
| 3.0.2 | Créer branche `feature/extensible-architecture` | - |
| 3.0.3 | Valider baseline : `pytest && ruff check` | - |

---

### Phase 3.1 : LanguageBackend Abstraction (1.5 jour)

**Objectif** : Abstraire la syntaxe des langages C++ et Java

#### Nouveaux Fichiers

| Fichier | Lignes | Description |
|---------|--------|-------------|
| `generators/backends/__init__.py` | ~20 | Exports |
| `generators/backends/base.py` | ~150 | `LanguageBackend` ABC |
| `generators/backends/cpp.py` | ~200 | `CppBackend` implementation |
| `generators/backends/java.py` | ~250 | `JavaBackend` implementation |

#### Détail : `generators/backends/base.py`

```python
"""
Language Backend Abstract Base Class.

Defines the interface for language-specific code generation.
Each backend encapsulates syntax, types, and idioms for one target language.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from protocol_codegen.core.field import FieldBase
    from protocol_codegen.core.types import AtomicType

class LanguageBackend(ABC):
    """Abstract base for language-specific code generation."""

    # ─────────────────────────────────────────────────────────────
    # Identity
    # ─────────────────────────────────────────────────────────────

    @property
    @abstractmethod
    def name(self) -> str:
        """Language identifier: 'cpp', 'java', 'rust', etc."""
        ...

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """File extension: '.hpp', '.java', '.rs', etc."""
        ...

    # ─────────────────────────────────────────────────────────────
    # Type Mapping
    # ─────────────────────────────────────────────────────────────

    @abstractmethod
    def map_atomic_type(self, type_name: str) -> str:
        """Map protocol type to language type.

        Example: 'uint8' → 'uint8_t' (C++) or 'int' (Java)
        """
        ...

    @abstractmethod
    def array_type(self, element_type: str, size: int | None) -> str:
        """Generate array type declaration.

        Example: ('uint8_t', 16) → 'std::array<uint8_t, 16>' (C++)
                 ('int', 16) → 'int[]' (Java)
        """
        ...

    @abstractmethod
    def optional_type(self, inner_type: str) -> str:
        """Generate optional type wrapper.

        Example: 'Foo' → 'std::optional<Foo>' (C++) or 'Foo' (Java, nullable)
        """
        ...

    # ─────────────────────────────────────────────────────────────
    # Syntax Elements
    # ─────────────────────────────────────────────────────────────

    @abstractmethod
    def include_statement(self, path: str) -> str:
        """Generate include/import statement.

        Example: 'Encoder' → '#include "Encoder.hpp"' (C++)
                 'Encoder' → 'import protocol.Encoder;' (Java)
        """
        ...

    @abstractmethod
    def namespace_open(self, name: str) -> str:
        """Open namespace/package scope."""
        ...

    @abstractmethod
    def namespace_close(self, name: str) -> str:
        """Close namespace/package scope."""
        ...

    @abstractmethod
    def struct_declaration(
        self,
        name: str,
        fields: list[tuple[str, str]],  # [(type, name), ...]
        constants: list[tuple[str, str, str]] = [],  # [(type, name, value), ...]
    ) -> str:
        """Generate struct/class declaration with fields."""
        ...

    @abstractmethod
    def function_signature(
        self,
        name: str,
        params: list[tuple[str, str]],  # [(type, name), ...]
        return_type: str,
        modifiers: list[str] = [],  # ['static', 'inline', 'const', ...]
    ) -> str:
        """Generate function/method signature."""
        ...

    # ─────────────────────────────────────────────────────────────
    # Encoder/Decoder Idioms
    # ─────────────────────────────────────────────────────────────

    @abstractmethod
    def encode_call(self, encoder_var: str, method: str, value: str) -> str:
        """Generate encoder method call.

        Example: ('Encoder', 'encodeUint8', 'val')
                 → 'Encoder::encodeUint8(buf, val);' (C++)
                 → 'Encoder.encodeUint8(buffer, val);' (Java)
        """
        ...

    @abstractmethod
    def decode_call(self, decoder_var: str, method: str) -> str:
        """Generate decoder method call.

        Example: ('Decoder', 'decodeUint8')
                 → 'Decoder::decodeUint8(buf)' (C++)
                 → 'Decoder.decodeUint8(buffer)' (Java)
        """
        ...

    # ─────────────────────────────────────────────────────────────
    # File Assembly
    # ─────────────────────────────────────────────────────────────

    @abstractmethod
    def file_header(self, description: str, includes: list[str]) -> str:
        """Generate file header with includes/imports."""
        ...

    @abstractmethod
    def file_footer(self) -> str:
        """Generate file footer (closing braces, etc.)."""
        ...
```

#### Détail : `generators/backends/cpp.py`

```python
"""
C++ Language Backend.

Implements LanguageBackend for C++ code generation.
Handles C++ syntax, STL types, and embedded-friendly patterns.
"""

from protocol_codegen.generators.backends.base import LanguageBackend


class CppBackend(LanguageBackend):
    """C++ code generation backend."""

    # Type mapping: protocol type → C++ type
    TYPE_MAP = {
        "bool": "bool",
        "uint8": "uint8_t",
        "int8": "int8_t",
        "uint16": "uint16_t",
        "int16": "int16_t",
        "uint32": "uint32_t",
        "int32": "int32_t",
        "float32": "float",
        "norm8": "float",
        "norm16": "float",
        "string": "std::string",
    }

    @property
    def name(self) -> str:
        return "cpp"

    @property
    def file_extension(self) -> str:
        return ".hpp"

    def map_atomic_type(self, type_name: str) -> str:
        return self.TYPE_MAP.get(type_name, type_name)

    def array_type(self, element_type: str, size: int | None) -> str:
        if size is not None:
            return f"std::array<{element_type}, {size}>"
        return f"std::vector<{element_type}>"

    def optional_type(self, inner_type: str) -> str:
        return f"std::optional<{inner_type}>"

    def include_statement(self, path: str) -> str:
        if path.startswith("<"):
            return f"#include {path}"
        return f'#include "{path}"'

    def namespace_open(self, name: str) -> str:
        return f"namespace {name} {{"

    def namespace_close(self, name: str) -> str:
        return f"}}  // namespace {name}"

    def struct_declaration(
        self,
        name: str,
        fields: list[tuple[str, str]],
        constants: list[tuple[str, str, str]] = [],
    ) -> str:
        lines = [f"struct {name} {{"]

        # Constants
        for const_type, const_name, const_value in constants:
            lines.append(f"    static constexpr {const_type} {const_name} = {const_value};")

        if constants and fields:
            lines.append("")

        # Fields
        for field_type, field_name in fields:
            lines.append(f"    {field_type} {field_name};")

        lines.append("};")
        return "\n".join(lines)

    def function_signature(
        self,
        name: str,
        params: list[tuple[str, str]],
        return_type: str,
        modifiers: list[str] = [],
    ) -> str:
        mod_str = " ".join(modifiers) + " " if modifiers else ""
        param_str = ", ".join(f"{t} {n}" for t, n in params)
        return f"{mod_str}{return_type} {name}({param_str})"

    def encode_call(self, encoder_var: str, method: str, value: str) -> str:
        return f"{encoder_var}::{method}(buf, {value});"

    def decode_call(self, decoder_var: str, method: str) -> str:
        return f"{decoder_var}::{method}(buf)"

    def file_header(self, description: str, includes: list[str]) -> str:
        lines = [
            "#pragma once",
            "",
            "/**",
            f" * {description}",
            " *",
            " * AUTO-GENERATED - DO NOT EDIT",
            " */",
            "",
        ]
        for inc in includes:
            lines.append(self.include_statement(inc))
        lines.append("")
        return "\n".join(lines)

    def file_footer(self) -> str:
        return ""
```

#### Détail : `generators/backends/java.py`

```python
"""
Java Language Backend.

Implements LanguageBackend for Java code generation.
Handles Java syntax, package structure, and Android compatibility.
"""

from protocol_codegen.generators.backends.base import LanguageBackend


class JavaBackend(LanguageBackend):
    """Java code generation backend."""

    TYPE_MAP = {
        "bool": "boolean",
        "uint8": "int",      # Java n'a pas de unsigned, on utilise int
        "int8": "byte",
        "uint16": "int",
        "int16": "short",
        "uint32": "long",
        "int32": "int",
        "float32": "float",
        "norm8": "float",
        "norm16": "float",
        "string": "String",
    }

    def __init__(self, package: str = "protocol"):
        self._package = package

    @property
    def name(self) -> str:
        return "java"

    @property
    def file_extension(self) -> str:
        return ".java"

    @property
    def package(self) -> str:
        return self._package

    def map_atomic_type(self, type_name: str) -> str:
        return self.TYPE_MAP.get(type_name, type_name)

    def array_type(self, element_type: str, size: int | None) -> str:
        return f"{element_type}[]"

    def optional_type(self, inner_type: str) -> str:
        # Java uses nullable references
        return inner_type

    def include_statement(self, path: str) -> str:
        return f"import {path};"

    def namespace_open(self, name: str) -> str:
        return f"package {name};"

    def namespace_close(self, name: str) -> str:
        return ""  # Java doesn't close packages

    def struct_declaration(
        self,
        name: str,
        fields: list[tuple[str, str]],
        constants: list[tuple[str, str, str]] = [],
    ) -> str:
        lines = [f"public final class {name} {{"]

        # Constants
        for const_type, const_name, const_value in constants:
            lines.append(f"    public static final {const_type} {const_name} = {const_value};")

        if constants and fields:
            lines.append("")

        # Fields (private final)
        for field_type, field_name in fields:
            lines.append(f"    private final {field_type} {field_name};")

        lines.append("}")
        return "\n".join(lines)

    def function_signature(
        self,
        name: str,
        params: list[tuple[str, str]],
        return_type: str,
        modifiers: list[str] = [],
    ) -> str:
        mod_str = " ".join(modifiers) + " " if modifiers else ""
        param_str = ", ".join(f"{t} {n}" for t, n in params)
        return f"{mod_str}{return_type} {name}({param_str})"

    def encode_call(self, encoder_var: str, method: str, value: str) -> str:
        return f"{encoder_var}.{method}(buffer, {value});"

    def decode_call(self, decoder_var: str, method: str) -> str:
        return f"{decoder_var}.{method}(buffer)"

    def file_header(self, description: str, includes: list[str]) -> str:
        lines = [
            f"package {self._package};",
            "",
            "/**",
            f" * {description}",
            " *",
            " * AUTO-GENERATED - DO NOT EDIT",
            " */",
            "",
        ]
        for inc in includes:
            lines.append(self.include_statement(inc))
        if includes:
            lines.append("")
        return "\n".join(lines)

    def file_footer(self) -> str:
        return ""
```

#### Tests à Créer

| Fichier | Description |
|---------|-------------|
| `tests/generators/backends/test_cpp_backend.py` | Tests unitaires CppBackend |
| `tests/generators/backends/test_java_backend.py` | Tests unitaires JavaBackend |

#### Validation Phase 3.1

```bash
pytest tests/generators/backends/
ruff check src/protocol_codegen/generators/backends/
```

---

### Phase 3.2 : CodecTemplate - Encoders (1 jour)

**Objectif** : Factoriser `encoder_generator.py` (Serial8 + SysEx) × (C++ + Java)

#### Nouveaux Fichiers

| Fichier | Lignes | Description |
|---------|--------|-------------|
| `generators/templates/__init__.py` | ~10 | Exports |
| `generators/templates/encoder.py` | ~300 | `EncoderTemplate` générique |

#### Fichiers Modifiés

| Fichier | Action |
|---------|--------|
| `serial8/cpp/encoder_generator.py` | Réduire à orchestrateur (~50 lignes) |
| `serial8/java/encoder_generator.py` | Réduire à orchestrateur (~50 lignes) |
| `sysex/cpp/encoder_generator.py` | Réduire à orchestrateur (~50 lignes) |
| `sysex/java/encoder_generator.py` | Réduire à orchestrateur (~50 lignes) |

#### Détail : `generators/templates/encoder.py`

```python
"""
Encoder Template.

Generates Encoder.hpp/java files for any combination of:
- LanguageBackend (C++, Java, Rust, ...)
- EncodingStrategy (Serial8, SysEx, WebSocket, ...)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from protocol_codegen.core.loader import TypeRegistry
    from protocol_codegen.generators.backends.base import LanguageBackend
    from protocol_codegen.generators.common.encoding import EncodingStrategy


class EncoderTemplate:
    """Template for encoder code generation."""

    def __init__(
        self,
        backend: LanguageBackend,
        strategy: EncodingStrategy,
    ):
        self.backend = backend
        self.strategy = strategy

    def generate(self, type_registry: TypeRegistry) -> str:
        """Generate complete encoder file."""
        header = self._generate_header()
        encoders = self._generate_encode_methods(type_registry)
        footer = self.backend.file_footer()

        return f"{header}\n{encoders}\n{footer}"

    def _generate_header(self) -> str:
        """Generate file header with includes."""
        includes = self._get_required_includes()
        return self.backend.file_header(
            description=f"Encoder for {self.strategy.name} protocol",
            includes=includes,
        )

    def _get_required_includes(self) -> list[str]:
        """Get required includes for this backend."""
        if self.backend.name == "cpp":
            return ["<cstdint>", "<cstring>", "<string>"]
        elif self.backend.name == "java":
            return []
        return []

    def _generate_encode_methods(self, type_registry: TypeRegistry) -> str:
        """Generate all encode methods."""
        methods = []

        for type_name, atomic_type in sorted(type_registry.types.items()):
            if atomic_type.cpp_type is None:
                continue

            method = self._generate_single_encoder(type_name, atomic_type)
            if method:
                methods.append(method)

        return "\n".join(methods)

    def _generate_single_encoder(self, type_name: str, atomic_type) -> str:
        """Generate encoder for a single type."""
        # Delegate to strategy for encoding logic
        encode_logic = self.strategy.get_encode_logic(type_name)

        # Use backend for syntax
        method_name = f"encode{type_name.capitalize()}"
        lang_type = self.backend.map_atomic_type(type_name)

        if self.backend.name == "cpp":
            return self._generate_cpp_encoder(method_name, lang_type, encode_logic, atomic_type.description)
        elif self.backend.name == "java":
            return self._generate_java_encoder(method_name, lang_type, encode_logic, atomic_type.description)

        return ""

    def _generate_cpp_encoder(self, method_name: str, param_type: str, logic: str, desc: str) -> str:
        """Generate C++ encoder method."""
        return f'''
/**
 * {desc}
 */
static inline void {method_name}(uint8_t*& buf, {param_type} val) {{
{logic}
}}
'''

    def _generate_java_encoder(self, method_name: str, param_type: str, logic: str, desc: str) -> str:
        """Generate Java encoder method."""
        return f'''
    /**
     * {desc}
     */
    public static void {method_name}(ByteBuffer buffer, {param_type} val) {{
{logic}
    }}
'''
```

#### Extension de EncodingStrategy

Ajouter à `generators/common/encoding/strategy.py` :

```python
@abstractmethod
def get_encode_logic(self, type_name: str) -> str:
    """Return the encoding logic for a given type.

    Returns language-agnostic pseudo-code that templates transform.
    """
    ...
```

#### Validation Phase 3.2

```bash
# Générer avec nouveau code
python -m protocol_codegen generate sysex ...

# Comparer output
diff -r output_before/ output_after/

# Tests
pytest
```

---

### Phase 3.3 : CodecTemplate - Decoders (1 jour)

**Objectif** : Factoriser `decoder_generator.py`

#### Nouveaux Fichiers

| Fichier | Lignes | Description |
|---------|--------|-------------|
| `generators/templates/decoder.py` | ~350 | `DecoderTemplate` générique |

#### Fichiers Modifiés

| Fichier | Action |
|---------|--------|
| `serial8/cpp/decoder_generator.py` | Réduire à orchestrateur (~50 lignes) |
| `serial8/java/decoder_generator.py` | Réduire à orchestrateur (~50 lignes) |
| `sysex/cpp/decoder_generator.py` | Réduire à orchestrateur (~50 lignes) |
| `sysex/java/decoder_generator.py` | Réduire à orchestrateur (~50 lignes) |

#### Structure identique à Phase 3.2

---

### Phase 3.4 : ConstantsTemplate (0.5 jour)

**Objectif** : Factoriser `constants_generator.py`

#### Nouveaux Fichiers

| Fichier | Lignes | Description |
|---------|--------|-------------|
| `generators/templates/constants.py` | ~150 | `ConstantsTemplate` |

#### Fichiers Modifiés

| Fichier | Action |
|---------|--------|
| `serial8/cpp/constants_generator.py` | Réduire (~40 lignes) |
| `serial8/java/constants_generator.py` | Réduire (~40 lignes) |
| `sysex/cpp/constants_generator.py` | Réduire (~40 lignes) |
| `sysex/java/constants_generator.py` | Réduire (~40 lignes) |

---

### Phase 3.5 : FileManifest + Orchestration Générique (1 jour)

**Objectif** : Éliminer duplication dans `_generate_cpp()` / `_generate_java()`

#### Nouveaux Fichiers

| Fichier | Lignes | Description |
|---------|--------|-------------|
| `generators/manifest.py` | ~100 | `FileManifest` déclaratif |
| `generators/pipeline.py` | ~150 | `GenerationPipeline` |

#### Fichiers Modifiés

| Fichier | Action |
|---------|--------|
| `methods/base_generator.py` | Utiliser pipeline générique |
| `methods/serial8/generator.py` | Réduire à ~150 lignes |
| `methods/sysex/generator.py` | Réduire à ~150 lignes |

#### Détail : `generators/manifest.py`

```python
"""
File Manifest.

Declarative specification of files to generate per language.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable


class FileScope(Enum):
    """Scope of file generation."""
    ONCE = auto()        # Generate once (e.g., Encoder.hpp)
    PER_MESSAGE = auto() # Generate per message (e.g., FooMessage.hpp)
    PER_ENUM = auto()    # Generate per enum (e.g., FooEnum.hpp)


@dataclass
class FileSpec:
    """Specification for a generated file."""

    filename_pattern: str  # e.g., "Encoder.hpp", "{name}Message.hpp"
    generator: Callable    # Function that generates content
    scope: FileScope = FileScope.ONCE
    subdirectory: str = ""  # e.g., "structs/"


# C++ Manifest
CPP_MANIFEST = [
    FileSpec("Encoder.hpp", generate_encoder_hpp),
    FileSpec("Decoder.hpp", generate_decoder_hpp),
    FileSpec("ProtocolConstants.hpp", generate_constants_hpp),
    FileSpec("MessageID.hpp", generate_messageid_hpp),
    FileSpec("MessageStructure.hpp", generate_message_structure_hpp),
    FileSpec("ProtocolCallbacks.hpp", generate_callbacks_hpp),
    FileSpec("DecoderRegistry.hpp", generate_decoder_registry_hpp),
    FileSpec("Protocol.hpp.template", generate_protocol_template_hpp),
    FileSpec("ProtocolMethods.inl", generate_methods_hpp),
    FileSpec("{name}Message.hpp", generate_struct_hpp, FileScope.PER_MESSAGE, "structs/"),
    FileSpec("{name}.hpp", generate_enum_hpp, FileScope.PER_ENUM),
]

# Java Manifest
JAVA_MANIFEST = [
    FileSpec("Encoder.java", generate_encoder_java),
    FileSpec("Decoder.java", generate_decoder_java),
    FileSpec("ProtocolConstants.java", generate_constants_java),
    FileSpec("MessageID.java", generate_messageid_java),
    FileSpec("ProtocolCallbacks.java", generate_callbacks_java),
    FileSpec("DecoderRegistry.java", generate_decoder_registry_java),
    FileSpec("Protocol.java.template", generate_protocol_template_java),
    FileSpec("ProtocolMethods.java", generate_methods_java),
    FileSpec("{name}Message.java", generate_struct_java, FileScope.PER_MESSAGE, "struct/"),
    FileSpec("{name}.java", generate_enum_java, FileScope.PER_ENUM),
]
```

#### Détail : `generators/pipeline.py`

```python
"""
Generation Pipeline.

Generic file generation orchestration.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from protocol_codegen.core.file_utils import GenerationStats, write_if_changed
from protocol_codegen.generators.manifest import FileScope, FileSpec

if TYPE_CHECKING:
    from protocol_codegen.core.message import Message
    from protocol_codegen.core.enum_def import EnumDef


class GenerationPipeline:
    """Executes file generation from a manifest."""

    def __init__(self, base_path: Path, verbose: bool = False):
        self.base_path = base_path
        self.verbose = verbose
        self.stats = GenerationStats()

    def execute(
        self,
        manifest: list[FileSpec],
        context: "GenerationContext",
    ) -> None:
        """Execute all file specifications in manifest."""
        for spec in manifest:
            self._execute_spec(spec, context)

    def _execute_spec(self, spec: FileSpec, context: "GenerationContext") -> None:
        """Execute a single file specification."""
        output_dir = self.base_path / spec.subdirectory
        output_dir.mkdir(parents=True, exist_ok=True)

        if spec.scope == FileScope.ONCE:
            self._generate_single(spec, output_dir, context)
        elif spec.scope == FileScope.PER_MESSAGE:
            self._generate_per_message(spec, output_dir, context)
        elif spec.scope == FileScope.PER_ENUM:
            self._generate_per_enum(spec, output_dir, context)

    def _generate_single(self, spec: FileSpec, output_dir: Path, context) -> None:
        path = output_dir / spec.filename_pattern
        content = spec.generator(context)
        was_written = write_if_changed(path, content)
        self.stats.record_write(path, was_written)

    def _generate_per_message(self, spec: FileSpec, output_dir: Path, context) -> None:
        for message in context.messages:
            pascal_name = self._to_pascal_case(message.name)
            filename = spec.filename_pattern.format(name=pascal_name)
            path = output_dir / filename
            content = spec.generator(message, context)
            was_written = write_if_changed(path, content)
            self.stats.record_write(path, was_written)

    def _generate_per_enum(self, spec: FileSpec, output_dir: Path, context) -> None:
        for enum_def in context.enum_defs:
            filename = spec.filename_pattern.format(name=enum_def.name)
            path = output_dir / filename
            content = spec.generator(enum_def, context)
            was_written = write_if_changed(path, content)
            self.stats.record_write(path, was_written)

    def _to_pascal_case(self, name: str) -> str:
        return "".join(word.capitalize() for word in name.split("_"))

    def summary(self) -> str:
        return self.stats.summary()
```

---

### Phase 3.6 : Consolidation Protocol Generators (0.5 jour)

**Objectif** : Factoriser `protocol_generator.py` et `decoder_registry_generator.py`

#### Fichiers Modifiés

| Fichier | Action |
|---------|--------|
| `serial8/cpp/protocol_generator.py` | Analyser différences |
| `sysex/cpp/protocol_generator.py` | Merger si possible |
| `serial8/cpp/decoder_registry_generator.py` | Analyser différences |
| `sysex/cpp/decoder_registry_generator.py` | Merger si possible |

Note: Ces fichiers ont ~40% de similarité, la factorisation peut être partielle.

---

### Phase 3.7 : Nettoyage et Documentation (0.5 jour)

| Étape | Action |
|-------|--------|
| 3.7.1 | Supprimer code mort / fichiers obsolètes |
| 3.7.2 | Mettre à jour `__init__.py` exports |
| 3.7.3 | Documenter l'architecture dans README |
| 3.7.4 | Valider tous les tests |
| 3.7.5 | Merger dans main |

---

## 5. Inventaire Complet des Fichiers

### 5.1 Fichiers à CRÉER

| Chemin | Lignes | Phase |
|--------|--------|-------|
| `generators/backends/__init__.py` | ~20 | 3.1 |
| `generators/backends/base.py` | ~150 | 3.1 |
| `generators/backends/cpp.py` | ~200 | 3.1 |
| `generators/backends/java.py` | ~250 | 3.1 |
| `generators/templates/__init__.py` | ~10 | 3.2 |
| `generators/templates/encoder.py` | ~300 | 3.2 |
| `generators/templates/decoder.py` | ~350 | 3.3 |
| `generators/templates/constants.py` | ~150 | 3.4 |
| `generators/manifest.py` | ~100 | 3.5 |
| `generators/pipeline.py` | ~150 | 3.5 |
| `tests/generators/backends/test_cpp_backend.py` | ~100 | 3.1 |
| `tests/generators/backends/test_java_backend.py` | ~100 | 3.1 |
| `tests/generators/templates/test_encoder.py` | ~100 | 3.2 |
| `tests/generators/templates/test_decoder.py` | ~100 | 3.3 |
| **TOTAL CRÉÉ** | **~2,080** | |

### 5.2 Fichiers à MODIFIER

| Chemin | Avant | Après | Delta | Phase |
|--------|-------|-------|-------|-------|
| `common/encoding/strategy.py` | 50 | 80 | +30 | 3.2 |
| `common/encoding/serial8_strategy.py` | 39 | 100 | +61 | 3.2 |
| `common/encoding/sysex_strategy.py` | 42 | 110 | +68 | 3.2 |
| `serial8/cpp/encoder_generator.py` | 273 | 50 | -223 | 3.2 |
| `serial8/java/encoder_generator.py` | 339 | 50 | -289 | 3.2 |
| `sysex/cpp/encoder_generator.py` | 298 | 50 | -248 | 3.2 |
| `sysex/java/encoder_generator.py` | 593 | 50 | -543 | 3.2 |
| `serial8/cpp/decoder_generator.py` | 335 | 50 | -285 | 3.3 |
| `serial8/java/decoder_generator.py` | 365 | 50 | -315 | 3.3 |
| `sysex/cpp/decoder_generator.py` | 357 | 50 | -307 | 3.3 |
| `sysex/java/decoder_generator.py` | 386 | 50 | -336 | 3.3 |
| `serial8/cpp/constants_generator.py` | 164 | 40 | -124 | 3.4 |
| `serial8/java/constants_generator.py` | 158 | 40 | -118 | 3.4 |
| `sysex/cpp/constants_generator.py` | 207 | 40 | -167 | 3.4 |
| `sysex/java/constants_generator.py` | 204 | 40 | -164 | 3.4 |
| `methods/base_generator.py` | 233 | 180 | -53 | 3.5 |
| `methods/serial8/generator.py` | 375 | 150 | -225 | 3.5 |
| `methods/sysex/generator.py` | 397 | 150 | -247 | 3.5 |
| **TOTAL MODIFICATIONS** | **4,815** | **1,380** | **-3,435** | |

### 5.3 Fichiers INCHANGÉS

| Catégorie | Fichiers | Lignes |
|-----------|----------|--------|
| `core/*` | 13 | 1,574 |
| `generators/common/cpp/struct_utils.py` | 1 | 741 |
| `generators/common/java/struct_utils.py` | 1 | 1,104 |
| `generators/common/cpp/*` (autres) | 6 | 604 |
| `generators/common/java/*` (autres) | 5 | 513 |
| `generators/common/naming.py` | 1 | 107 |
| `generators/common/payload_calculator.py` | 1 | 175 |
| `serial8/cpp/struct_generator.py` | 1 | 127 |
| `serial8/java/struct_generator.py` | 1 | 135 |
| `sysex/cpp/struct_generator.py` | 1 | 127 |
| `sysex/java/struct_generator.py` | 1 | 135 |
| `serial8/cpp/protocol_generator.py` | 1 | 214 |
| `sysex/cpp/protocol_generator.py` | 1 | 272 |
| `serial8/java/protocol_generator.py` | 1 | 279 |
| `sysex/java/protocol_generator.py` | 1 | 253 |
| `serial8/cpp/decoder_registry_generator.py` | 1 | 142 |
| `sysex/cpp/decoder_registry_generator.py` | 1 | 142 |
| `cli.py`, `__main__.py`, etc. | 4 | 322 |
| `__init__.py` files | ~15 | ~400 |
| **TOTAL INCHANGÉ** | ~53 | ~6,366 |

### 5.4 Fichiers à SUPPRIMER

Aucun fichier n'est supprimé - les fichiers existants sont réduits à des orchestrateurs légers.

---

## 6. Conventions de Nommage

### 6.1 Modules

| Pattern | Exemple | Usage |
|---------|---------|-------|
| `backends/{lang}.py` | `backends/cpp.py` | Un backend par langage |
| `templates/{artifact}.py` | `templates/encoder.py` | Un template par artifact |
| `{protocol}/{lang}/{artifact}_generator.py` | `sysex/cpp/encoder_generator.py` | Orchestrateur protocol×lang |

### 6.2 Classes

| Pattern | Exemple | Usage |
|---------|---------|-------|
| `{Lang}Backend` | `CppBackend`, `JavaBackend` | Implementation LanguageBackend |
| `{Artifact}Template` | `EncoderTemplate`, `DecoderTemplate` | Template générique |
| `{Protocol}EncodingStrategy` | `SysExEncodingStrategy` | Strategy d'encodage |
| `{Protocol}Generator` | `SysExGenerator` | Générateur principal |

### 6.3 Fonctions

| Pattern | Exemple | Usage |
|---------|---------|-------|
| `generate_{artifact}_{ext}` | `generate_encoder_hpp` | Point d'entrée génération |
| `_generate_{part}` | `_generate_header` | Fonction interne |
| `map_{thing}` | `map_atomic_type` | Mapping/transformation |
| `get_{thing}` | `get_encode_logic` | Accesseur |

### 6.4 Fichiers Générés

| Pattern C++ | Pattern Java | Exemple |
|-------------|--------------|---------|
| `{Name}.hpp` | `{Name}.java` | `Encoder.hpp`, `Encoder.java` |
| `{Name}Message.hpp` | `{Name}Message.java` | `TransportPlayMessage.hpp` |
| `Protocol*.hpp` | `Protocol*.java` | `ProtocolConstants.hpp` |

---

## 7. Risques et Mitigations

### 7.1 Risques Techniques

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Régression encode/decode | Moyenne | Élevé | Tests comparatifs output |
| Imports circulaires | Faible | Moyen | Structure claire backends/templates |
| Performance génération | Faible | Faible | Benchmark avant/après |

### 7.2 Risques Projet

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Scope creep | Moyenne | Moyen | Phases bien définies |
| Temps sous-estimé | Moyenne | Moyen | Buffer 20% par phase |
| Perte de compatibilité | Faible | Élevé | Tag Git pré-refactoring |

### 7.3 Validation Continue

Après chaque phase :

```bash
# 1. Tests unitaires
pytest

# 2. Lint
ruff check src/

# 3. Génération de référence
python -m protocol_codegen generate sysex \
    --messages-dir examples/messages \
    --config examples/sysex/protocol_config.py \
    --plugin-paths examples/sysex/plugin_paths.py \
    --output output_test/

# 4. Diff avec référence
diff -r output_reference/ output_test/
```

---

## 8. Résumé Exécutif

### Métriques Finales Projetées

| Métrique | Avant | Après | Gain |
|----------|-------|-------|------|
| **Fichiers Python** | 79 | ~68 | -11 |
| **Lignes de code** | 13,416 | ~10,000 | -3,400 (25%) |
| **Duplication estimée** | 26% | <5% | -21pp |
| **Fichiers à modifier pour nouveau langage** | ~12 | **1** | -92% |
| **Fichiers à modifier pour nouveau protocole** | ~12 | **1** | -92% |

### Effort Total Estimé

| Phase | Effort | Cumulatif |
|-------|--------|-----------|
| 3.0 Préparation | 0.5j | 0.5j |
| 3.1 LanguageBackend | 1.5j | 2j |
| 3.2 EncoderTemplate | 1j | 3j |
| 3.3 DecoderTemplate | 1j | 4j |
| 3.4 ConstantsTemplate | 0.5j | 4.5j |
| 3.5 FileManifest | 1j | 5.5j |
| 3.6 Consolidation | 0.5j | 6j |
| 3.7 Nettoyage | 0.5j | 6.5j |
| **TOTAL** | | **6.5 jours** |

### Décision

✅ **REFACTORING INCRÉMENTAL RECOMMANDÉ**

- Tests existants = filet de sécurité
- Architecture cible claire
- Gains quantifiables
- Aucune période d'indisponibilité
