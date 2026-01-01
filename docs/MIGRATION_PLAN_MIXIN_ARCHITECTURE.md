# Plan de Migration: Architecture Mixin pour Protocol-Codegen

> **Version:** 1.0
> **Date:** 2026-01-01
> **Statut:** Approuvé pour implémentation
> **Objectif:** Architecture propre, extensible, zéro duplication, zéro legacy

---

## Table des Matières

1. [Vue d'Ensemble](#1-vue-densemble)
2. [Architecture Cible](#2-architecture-cible)
3. [Phases de Migration](#3-phases-de-migration)
   - [Phase 0: Préparation](#phase-0-préparation)
   - [Phase 1: Extraction Config Commune](#phase-1-extraction-config-commune)
   - [Phase 2: Unification java_package](#phase-2-unification-java_package)
   - [Phase 3: Nettoyage API Surface](#phase-3-nettoyage-api-surface)
   - [Phase 4: Infrastructure Renderers](#phase-4-infrastructure-renderers)
   - [Phase 5: Mixins Langage](#phase-5-mixins-langage)
   - [Phase 6: Mixins Protocol](#phase-6-mixins-protocol)
   - [Phase 7: Implémentation Renderers](#phase-7-implémentation-renderers)
   - [Phase 8: Intégration Orchestrateurs](#phase-8-intégration-orchestrateurs)
   - [Phase 9: Nettoyage Final](#phase-9-nettoyage-final)
4. [Validation Finale](#4-validation-finale)
5. [Rollback Strategy](#5-rollback-strategy)

---

## 1. Vue d'Ensemble

### 1.1 Problèmes Actuels

| Problème | Impact | Solution |
|----------|--------|----------|
| `ProtocolConfig` dupliqué (cpp/java) | Maintenance double | Extraction vers `common/config.py` |
| `java_package` incohérent | API confuse | Paramètre unifié |
| `struct_utils` exposés publiquement | Surface API trop large | Internaliser |
| Protocol generators dupliqués (4 fichiers) | ~1000 LOC redondants | Pattern Mixin |
| Pas de registry pour renderers | Extension difficile | Auto-découverte |

### 1.2 Métriques Cibles

| Métrique | Avant | Après | Réduction |
|----------|-------|-------|-----------|
| Fichiers generators/ | 46 | ~30 | -35% |
| LOC total | ~8750 | ~5500 | -37% |
| Duplication | ~30% | <5% | -83% |
| Fichiers protocol template | 4 | 4 + 4 mixins | Logique partagée |

### 1.3 Commande de Test Globale

```bash
# À exécuter après CHAQUE phase
cd open-control/protocol-codegen
.venv/Scripts/python.exe -m pytest -v --tb=short

# Vérification ruff (linting)
python -m ruff check src/ tests/

# Génération de test (validation end-to-end)
cd ../../midi-studio/plugin-bitwig
./script/protocol/generate_protocol.sh
```

---

## 2. Architecture Cible

### 2.1 Structure Finale

```
generators/
├── __init__.py                    # API publique
│
├── backends/                      # Couche LANGAGE (inchangé)
│   ├── __init__.py
│   ├── base.py                    # LanguageBackend ABC
│   ├── cpp.py                     # CppBackend
│   ├── java.py                    # JavaBackend
│   └── factory.py                 # get_backend()
│
├── strategies/                    # Couche PROTOCOLE (renommé de encoding/)
│   ├── __init__.py
│   ├── base.py                    # EncodingStrategy ABC
│   ├── serial8.py                 # Serial8EncodingStrategy
│   └── sysex.py                   # SysExEncodingStrategy
│
├── common/                        # Logique partagée
│   ├── __init__.py
│   ├── config.py                  # ProtocolConfig TypedDict (NOUVEAU)
│   ├── naming.py                  # to_pascal_case, etc.
│   ├── payload.py                 # PayloadCalculator
│   │
│   ├── type_encoders/             # Encodeurs par type (inchangé)
│   └── type_decoders/             # Décodeurs par type (inchangé)
│
├── templates/                     # Templates universels (inchangé)
│   ├── __init__.py
│   ├── encoder.py                 # EncoderTemplate
│   └── decoder.py                 # DecoderTemplate
│
└── renderers/                     # NOUVEAU - Génération de fichiers
    ├── __init__.py                # API: create_renderer(type, backend, strategy?)
    │
    ├── base.py                    # FileRenderer ABC
    │
    ├── universal/                 # Backend + Strategy → fichier
    │   ├── __init__.py
    │   ├── encoder.py             # EncoderRenderer
    │   └── decoder.py             # DecoderRenderer
    │
    ├── by_backend/                # Backend seul → fichier
    │   ├── __init__.py            # Registry + factory
    │   ├── base.py                # Classe de base partagée
    │   │
    │   ├── enum/
    │   │   ├── __init__.py
    │   │   ├── cpp.py             # CppEnumRenderer
    │   │   └── java.py            # JavaEnumRenderer
    │   │
    │   ├── callbacks/
    │   │   ├── __init__.py
    │   │   ├── cpp.py
    │   │   └── java.py
    │   │
    │   ├── messageid/
    │   │   ├── __init__.py
    │   │   ├── cpp.py
    │   │   └── java.py
    │   │
    │   ├── decoder_registry/
    │   │   ├── __init__.py
    │   │   ├── cpp.py
    │   │   └── java.py
    │   │
    │   ├── methods/
    │   │   ├── __init__.py
    │   │   ├── cpp.py
    │   │   └── java.py
    │   │
    │   └── message_structure/
    │       ├── __init__.py
    │       ├── cpp.py
    │       └── java.py
    │
    ├── by_backend_strategy/       # Backend × Strategy → fichier
    │   ├── __init__.py
    │   ├── base.py
    │   │
    │   ├── struct/
    │   │   ├── __init__.py
    │   │   ├── _logic.py          # Logique commune (StructSpec, etc.)
    │   │   ├── cpp.py             # CppStructRenderer
    │   │   └── java.py            # JavaStructRenderer
    │   │
    │   └── constants/
    │       ├── __init__.py
    │       ├── cpp.py
    │       └── java.py
    │
    └── protocol/                  # MIXINS - Protocol templates
        ├── __init__.py            # Registry + create_protocol_renderer()
        ├── base.py                # ProtocolRendererBase (template method)
        │
        ├── mixins/
        │   ├── __init__.py
        │   │
        │   ├── languages/         # Syntaxe par langage
        │   │   ├── __init__.py
        │   │   ├── cpp.py         # CppProtocolMixin
        │   │   └── java.py        # JavaProtocolMixin
        │   │
        │   └── framings/          # Framing par protocole
        │       ├── __init__.py
        │       ├── serial8.py     # Serial8FramingMixin
        │       └── sysex.py       # SysExFramingMixin
        │
        └── implementations/       # Combinaisons finales
            ├── __init__.py
            ├── serial8_cpp.py     # ~15 LOC
            ├── serial8_java.py    # ~15 LOC
            ├── sysex_cpp.py       # ~15 LOC
            └── sysex_java.py      # ~15 LOC
```

### 2.2 Fichiers Supprimés (Phase 9)

```
À SUPPRIMER:
├── generators/
│   ├── common/
│   │   ├── cpp/
│   │   │   ├── callbacks_generator.py      → renderers/by_backend/callbacks/cpp.py
│   │   │   ├── constants_generator.py      → renderers/by_backend_strategy/constants/cpp.py
│   │   │   ├── decoder_registry_generator.py → renderers/by_backend/decoder_registry/cpp.py
│   │   │   ├── enum_generator.py           → renderers/by_backend/enum/cpp.py
│   │   │   ├── message_structure_generator.py → renderers/by_backend/message_structure/cpp.py
│   │   │   ├── messageid_generator.py      → renderers/by_backend/messageid/cpp.py
│   │   │   ├── method_generator.py         → renderers/by_backend/methods/cpp.py
│   │   │   ├── struct_generator.py         → renderers/by_backend_strategy/struct/cpp.py
│   │   │   └── struct_utils.py             → renderers/by_backend_strategy/struct/_logic.py
│   │   │
│   │   └── java/                           # Idem pour Java
│   │       └── ...
│   │
│   ├── serial8/
│   │   ├── cpp/
│   │   │   ├── __init__.py                 # SUPPRIMER (re-export inutile)
│   │   │   └── protocol_generator.py       → renderers/protocol/implementations/serial8_cpp.py
│   │   └── java/
│   │       ├── __init__.py                 # SUPPRIMER
│   │       └── protocol_generator.py       → renderers/protocol/implementations/serial8_java.py
│   │
│   └── sysex/                              # Idem
│       └── ...
```

---

## 3. Phases de Migration

---

### Phase 0: Préparation

**Objectif:** Créer une branche, s'assurer que les tests passent

**Durée estimée:** 15 min

#### Étapes

```bash
# 0.1 Créer branche de travail
git checkout -b refactor/mixin-architecture

# 0.2 Vérifier état initial
cd open-control/protocol-codegen
.venv/Scripts/python.exe -m pytest -v --tb=short
# ATTENDU: 405 tests passed

# 0.3 Vérifier génération actuelle
cd ../../midi-studio/plugin-bitwig
./script/protocol/generate_protocol.sh
# ATTENDU: Génération réussie

# 0.4 Commit checkpoint
git add -A && git commit -m "chore: checkpoint before mixin architecture migration"
```

#### Critères de Succès
- [x] Branche créée (feature/extensible-architecture)
- [x] 405 tests passent
- [x] Génération protocol fonctionne
- [x] Commit checkpoint créé (0e9915e)

---

### Phase 1: Extraction Config Commune

**Objectif:** Extraire `ProtocolConfig` TypedDict vers un fichier commun

**Durée estimée:** 30 min

#### 1.1 Créer le fichier config.py

**Fichier:** `src/protocol_codegen/generators/common/config.py`

```python
"""
Common Protocol Configuration Types.

Shared TypedDict definitions for protocol configuration across all backends.
"""

from typing import TypedDict


class StructureConfig(TypedDict):
    """Serial8 structure configuration."""
    message_type_offset: int
    payload_offset: int


class SysExFramingConfig(TypedDict):
    """SysEx framing configuration."""
    start: int
    end: int
    manufacturer_id: int
    device_id: int
    min_message_length: int
    message_type_offset: int
    payload_offset: int


class LimitsConfig(TypedDict):
    """Protocol limits configuration."""
    string_max_length: int
    array_max_items: int
    max_payload_size: int
    max_message_size: int


class ProtocolConfig(TypedDict, total=False):
    """
    Unified protocol configuration.

    Used by constants generators for both C++ and Java.
    - Serial8 uses: structure + limits
    - SysEx uses: sysex + limits
    """
    structure: StructureConfig  # Serial8
    sysex: SysExFramingConfig   # SysEx
    limits: LimitsConfig
```

#### 1.2 Mettre à jour common/cpp/constants_generator.py

```python
# SUPPRIMER les lignes 45-69 (les 4 TypedDict classes)

# AJOUTER en haut du fichier
from protocol_codegen.generators.common.config import (
    ProtocolConfig,
    LimitsConfig,
    StructureConfig,
    SysExFramingConfig,
)
```

#### 1.3 Mettre à jour common/java/constants_generator.py

```python
# SUPPRIMER les lignes 42-66 (les 4 TypedDict classes)

# AJOUTER en haut du fichier
from protocol_codegen.generators.common.config import (
    ProtocolConfig,
    LimitsConfig,
    StructureConfig,
    SysExFramingConfig,
)
```

#### 1.4 Mettre à jour common/__init__.py

```python
# AJOUTER l'export
from protocol_codegen.generators.common.config import (
    ProtocolConfig,
    LimitsConfig,
    StructureConfig,
    SysExFramingConfig,
)

# Ajouter au __all__
__all__ = [
    # ... existants ...
    "ProtocolConfig",
    "LimitsConfig",
    "StructureConfig",
    "SysExFramingConfig",
]
```

#### 1.5 Tests

```bash
# Exécuter les tests
.venv/Scripts/python.exe -m pytest -v --tb=short

# Vérifier imports
.venv/Scripts/python.exe -c "from protocol_codegen.generators.common import ProtocolConfig; print('OK')"

# Génération end-to-end
cd ../../midi-studio/plugin-bitwig && ./script/protocol/generate_protocol.sh
```

#### 1.6 Commit

```bash
git add -A && git commit -m "refactor(config): extract ProtocolConfig TypedDict to common/config.py

- Create generators/common/config.py with shared TypedDict definitions
- Remove duplicate definitions from cpp/constants_generator.py
- Remove duplicate definitions from java/constants_generator.py
- Export from common/__init__.py for public API"
```

#### Critères de Succès
- [x] `common/config.py` créé avec les 4 TypedDict
- [x] cpp/constants_generator.py utilise import
- [x] java/constants_generator.py utilise import
- [x] Tous les tests passent (405)
- [x] Génération fonctionne (commit 418e7a3)

---

### Phase 2: Unification java_package

**Objectif:** Retirer `java_package` de EnumDef, passer comme paramètre

**Durée estimée:** 45 min

#### 2.1 Modifier core/enum_def.py

```python
# AVANT (ligne ~61)
@dataclass
class EnumDef:
    """Definition of an enum type extracted from messages."""
    name: str
    values: dict[str, int]
    java_package: str = "protocol"  # SUPPRIMER CETTE LIGNE

# APRÈS
@dataclass
class EnumDef:
    """Definition of an enum type extracted from messages."""
    name: str
    values: dict[str, int]
    # Note: java_package removed - passed as parameter to generators
```

#### 2.2 Modifier common/java/enum_generator.py

```python
# AVANT (signature ligne ~30)
def generate_enum_java(enum_def: EnumDef, output_path: Path) -> str:

# APRÈS
def generate_enum_java(enum_def: EnumDef, output_path: Path, package: str) -> str:
    """
    Generate Java enum file.

    Args:
        enum_def: Enum definition
        output_path: Output file path
        package: Java package name

    Returns:
        Generated Java code
    """

# AVANT (ligne ~38)
    lines.append(f"package {enum_def.java_package};")

# APRÈS
    lines.append(f"package {package};")
```

#### 2.3 Mettre à jour methods/serial8/generator.py

```python
# AVANT (dans _generate_java, ~ligne 350)
for enum_def in self.enum_defs:
    java_enum_path = java_base / f"{enum_def.name}.java"
    java_enum_code = generate_enum_java(enum_def, java_enum_path)

# APRÈS
for enum_def in self.enum_defs:
    java_enum_path = java_base / f"{enum_def.name}.java"
    java_enum_code = generate_enum_java(enum_def, java_enum_path, java_package)
```

#### 2.4 Mettre à jour methods/sysex/generator.py

```python
# AVANT (dans _generate_java, ~ligne 340)
for enum_def in self.enum_defs:
    java_enum_path = java_base / f"{enum_def.name}.java"
    java_enum_code = generate_enum_java(enum_def, java_enum_path)

# APRÈS
for enum_def in self.enum_defs:
    java_enum_path = java_base / f"{enum_def.name}.java"
    java_enum_code = generate_enum_java(enum_def, java_enum_path, java_package)
```

#### 2.5 Mettre à jour les tests

**Fichier:** `tests/test_enum_generator.py`

```python
# Tous les appels à generate_enum_java doivent ajouter le paramètre package

# AVANT
result = generate_enum_java(enum_def, output_path)

# APRÈS
result = generate_enum_java(enum_def, output_path, "com.example.protocol")
```

#### 2.6 Tests

```bash
# Tests unitaires
.venv/Scripts/python.exe -m pytest tests/test_enum_generator.py -v --tb=short
.venv/Scripts/python.exe -m pytest tests/test_enum_def.py -v --tb=short

# Tous les tests
.venv/Scripts/python.exe -m pytest -v --tb=short

# Génération end-to-end
cd ../../midi-studio/plugin-bitwig && ./script/protocol/generate_protocol.sh
```

#### 2.7 Commit

```bash
git add -A && git commit -m "refactor(enum): unify java_package as parameter

BREAKING CHANGE: generate_enum_java() now requires package parameter

- Remove java_package field from EnumDef dataclass
- Add package parameter to generate_enum_java()
- Update Serial8Generator and SysExGenerator
- Update tests

This aligns enum generation with all other Java generators
that receive package as a parameter."
```

#### Critères de Succès
- [x] `java_package` supprimé de EnumDef
- [x] `generate_enum_java` a paramètre `package`
- [x] Serial8Generator mis à jour
- [x] SysExGenerator mis à jour
- [x] Tests mis à jour et passent
- [x] Génération fonctionne (commit b04dfea)

---

### Phase 3: Nettoyage API Surface

**Objectif:** Retirer struct_utils du __all__ public, garder comme implémentation interne

**Durée estimée:** 20 min

#### 3.1 Modifier common/cpp/__init__.py

```python
# SUPPRIMER les imports struct_utils (lignes 31-40)
# from protocol_codegen.generators.common.cpp.struct_utils import (
#     analyze_includes_needed,
#     generate_composite_structs,
#     ...
# )

# SUPPRIMER du __all__ (lignes 60-69)
# "analyze_includes_needed",
# "generate_composite_structs",
# ...

# GARDER SEULEMENT les générateurs de haut niveau
__all__ = [
    "generate_protocol_callbacks_hpp",
    "generate_constants_hpp",
    "generate_decoder_registry_hpp",
    "generate_enum_hpp",
    "generate_message_structure_hpp",
    "generate_messageid_hpp",
    "generate_protocol_methods_hpp",
    "generate_struct_hpp",
]
```

#### 3.2 Modifier common/java/__init__.py

```python
# SUPPRIMER les imports struct_utils (lignes 28-45)

# GARDER SEULEMENT les générateurs de haut niveau
__all__ = [
    "generate_protocol_callbacks_java",
    "generate_constants_java",
    "generate_decoder_registry_java",
    "generate_enum_java",
    "generate_messageid_java",
    "generate_protocol_methods_java",
    "generate_struct_java",
]
```

#### 3.3 Tests

```bash
# Vérifier que struct_utils ne sont plus accessibles publiquement
.venv/Scripts/python.exe -c "
from protocol_codegen.generators.common.cpp import generate_struct_hpp
print('generate_struct_hpp: OK')
try:
    from protocol_codegen.generators.common.cpp import generate_encode_function
    print('ERROR: generate_encode_function should not be public')
except ImportError:
    print('generate_encode_function correctly hidden: OK')
"

# Tous les tests
.venv/Scripts/python.exe -m pytest -v --tb=short

# Génération
cd ../../midi-studio/plugin-bitwig && ./script/protocol/generate_protocol.sh
```

#### 3.4 Commit

```bash
git add -A && git commit -m "refactor(api): hide struct_utils from public API

- Remove struct_utils exports from common/cpp/__init__.py
- Remove struct_utils exports from common/java/__init__.py
- struct_utils remain available internally via direct import
- Public API now only exposes high-level generate_* functions"
```

#### Critères de Succès
- [x] struct_utils non accessibles via `common.cpp`
- [x] struct_utils non accessibles via `common.java`
- [x] Tous les tests passent
- [x] Génération fonctionne (commit 9584528)

---

### Phase 4: Infrastructure Renderers

**Objectif:** Créer la structure de base pour les renderers

**Durée estimée:** 1h

#### 4.1 Créer la structure de dossiers

```bash
mkdir -p src/protocol_codegen/generators/renderers
mkdir -p src/protocol_codegen/generators/renderers/universal
mkdir -p src/protocol_codegen/generators/renderers/by_backend
mkdir -p src/protocol_codegen/generators/renderers/by_backend_strategy
mkdir -p src/protocol_codegen/generators/renderers/protocol
mkdir -p src/protocol_codegen/generators/renderers/protocol/mixins
mkdir -p src/protocol_codegen/generators/renderers/protocol/mixins/languages
mkdir -p src/protocol_codegen/generators/renderers/protocol/mixins/framings
mkdir -p src/protocol_codegen/generators/renderers/protocol/implementations
```

#### 4.2 Créer renderers/__init__.py

```python
"""
Renderers Package.

Provides file renderers organized by dependency type:
- universal/: Depend on both backend and strategy
- by_backend/: Depend only on backend (language)
- by_backend_strategy/: Depend on both, but logic differs
- protocol/: Protocol template renderers (mixin-based)
"""

from protocol_codegen.generators.renderers.registry import (
    RendererRegistry,
    get_renderer,
    register_renderer,
)

__all__ = [
    "RendererRegistry",
    "get_renderer",
    "register_renderer",
]
```

#### 4.3 Créer renderers/base.py

```python
"""
Base Renderer Classes.

Abstract base classes for all file renderers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class FileRenderer(ABC):
    """
    Abstract base class for all file renderers.

    A renderer generates a single output file from input data.
    """

    @property
    @abstractmethod
    def file_type(self) -> str:
        """Return the type of file this renderer produces (e.g., 'enum', 'struct')."""
        ...

    @abstractmethod
    def render(self, data: Any, output_path: Path, **kwargs: Any) -> str:
        """
        Render the file content.

        Args:
            data: Input data (message, enum_def, etc.)
            output_path: Target file path
            **kwargs: Additional renderer-specific arguments

        Returns:
            Generated file content as string
        """
        ...


class BackendRenderer(FileRenderer):
    """
    Base class for renderers that depend only on backend.

    Examples: EnumRenderer, CallbacksRenderer, MessageIdRenderer
    """

    def __init__(self, backend: "LanguageBackend") -> None:
        self.backend = backend

    @property
    def language(self) -> str:
        """Return the target language name."""
        return self.backend.name


class BackendStrategyRenderer(FileRenderer):
    """
    Base class for renderers that depend on both backend and strategy.

    Examples: StructRenderer, ConstantsRenderer
    """

    def __init__(
        self,
        backend: "LanguageBackend",
        strategy: "EncodingStrategy"
    ) -> None:
        self.backend = backend
        self.strategy = strategy

    @property
    def language(self) -> str:
        """Return the target language name."""
        return self.backend.name

    @property
    def protocol(self) -> str:
        """Return the protocol name."""
        return self.strategy.name
```

#### 4.4 Créer renderers/registry.py

```python
"""
Renderer Registry.

Auto-discovery and factory for renderers.
"""

from typing import Type, Callable, Any
from pathlib import Path
import importlib
import pkgutil


class RendererRegistry:
    """
    Registry for file renderers.

    Supports registration by:
    - (file_type, backend_name) for by_backend renderers
    - (file_type, backend_name, strategy_name) for by_backend_strategy renderers
    """

    _by_backend: dict[tuple[str, str], Type] = {}
    _by_backend_strategy: dict[tuple[str, str, str], Type] = {}

    @classmethod
    def register_backend(
        cls,
        file_type: str,
        backend_name: str
    ) -> Callable[[Type], Type]:
        """Decorator to register a by_backend renderer."""
        def decorator(renderer_cls: Type) -> Type:
            key = (file_type, backend_name.lower())
            cls._by_backend[key] = renderer_cls
            return renderer_cls
        return decorator

    @classmethod
    def register_backend_strategy(
        cls,
        file_type: str,
        backend_name: str,
        strategy_name: str
    ) -> Callable[[Type], Type]:
        """Decorator to register a by_backend_strategy renderer."""
        def decorator(renderer_cls: Type) -> Type:
            key = (file_type, backend_name.lower(), strategy_name.lower())
            cls._by_backend_strategy[key] = renderer_cls
            return renderer_cls
        return decorator

    @classmethod
    def get_backend_renderer(
        cls,
        file_type: str,
        backend: "LanguageBackend"
    ) -> Any:
        """Get a by_backend renderer instance."""
        key = (file_type, backend.name.lower())
        if key not in cls._by_backend:
            raise ValueError(
                f"No renderer registered for ({file_type}, {backend.name})"
            )
        return cls._by_backend[key](backend)

    @classmethod
    def get_backend_strategy_renderer(
        cls,
        file_type: str,
        backend: "LanguageBackend",
        strategy: "EncodingStrategy"
    ) -> Any:
        """Get a by_backend_strategy renderer instance."""
        key = (file_type, backend.name.lower(), strategy.name.lower())
        if key not in cls._by_backend_strategy:
            raise ValueError(
                f"No renderer registered for ({file_type}, {backend.name}, {strategy.name})"
            )
        return cls._by_backend_strategy[key](backend, strategy)


# Convenience functions
def register_renderer(
    file_type: str,
    backend_name: str,
    strategy_name: str | None = None
) -> Callable[[Type], Type]:
    """
    Decorator to register a renderer.

    Usage:
        @register_renderer("enum", "cpp")
        class CppEnumRenderer: ...

        @register_renderer("struct", "java", "sysex")
        class JavaSysExStructRenderer: ...
    """
    if strategy_name is None:
        return RendererRegistry.register_backend(file_type, backend_name)
    return RendererRegistry.register_backend_strategy(
        file_type, backend_name, strategy_name
    )


def get_renderer(
    file_type: str,
    backend: "LanguageBackend",
    strategy: "EncodingStrategy | None" = None
) -> Any:
    """
    Get a renderer instance.

    Usage:
        renderer = get_renderer("enum", cpp_backend)
        renderer = get_renderer("struct", java_backend, sysex_strategy)
    """
    if strategy is None:
        return RendererRegistry.get_backend_renderer(file_type, backend)
    return RendererRegistry.get_backend_strategy_renderer(
        file_type, backend, strategy
    )
```

#### 4.5 Créer __init__.py pour chaque sous-dossier

```python
# renderers/universal/__init__.py
"""Universal renderers (backend + strategy)."""

# renderers/by_backend/__init__.py
"""Backend-only renderers."""

# renderers/by_backend_strategy/__init__.py
"""Backend + Strategy renderers with shared logic."""

# renderers/protocol/__init__.py
"""Protocol template renderers (mixin-based)."""

# renderers/protocol/mixins/__init__.py
"""Mixins for protocol renderers."""

# renderers/protocol/mixins/languages/__init__.py
"""Language-specific mixins."""

# renderers/protocol/mixins/framings/__init__.py
"""Protocol framing mixins."""

# renderers/protocol/implementations/__init__.py
"""Concrete protocol renderer implementations."""
```

#### 4.6 Tests

```bash
# Test imports
.venv/Scripts/python.exe -c "
from protocol_codegen.generators.renderers import RendererRegistry, get_renderer, register_renderer
from protocol_codegen.generators.renderers.base import FileRenderer, BackendRenderer, BackendStrategyRenderer
print('All imports OK')
"

# Tous les tests (doivent toujours passer)
.venv/Scripts/python.exe -m pytest -v --tb=short
```

#### 4.7 Commit

```bash
git add -A && git commit -m "feat(renderers): create renderer infrastructure

- Add renderers/ package structure
- Create FileRenderer, BackendRenderer, BackendStrategyRenderer ABCs
- Create RendererRegistry with decorator-based registration
- Prepare directory structure for all renderer types"
```

#### Critères de Succès
- [x] Structure de dossiers créée
- [x] `renderers/__init__.py` créé
- [x] `renderers/base.py` créé avec ABCs
- [x] `renderers/registry.py` créé avec registry
- [x] Tous les __init__.py créés
- [x] Imports fonctionnent
- [x] Tests passent (commit 6045892)

---

### Phase 5: Mixins Langage

**Objectif:** Créer les mixins pour syntaxe C++ et Java

**Durée estimée:** 1h30

#### 5.1 Créer protocol/mixins/languages/cpp.py

```python
"""
C++ Language Mixin for Protocol Renderers.

Provides C++ syntax for protocol template generation.
"""

from pathlib import Path


class CppProtocolMixin:
    """
    Mixin providing C++ syntax for protocol templates.

    Must be combined with a FramingMixin and ProtocolRendererBase.
    """

    @property
    def is_cpp(self) -> bool:
        return True

    @property
    def is_java(self) -> bool:
        return False

    @property
    def file_extension(self) -> str:
        return ".hpp"

    def render_file_header(self, output_path: Path) -> str:
        """Render C++ file header with pragma once and includes."""
        return f"""/**
 * {output_path.name} - Protocol Handler Template
 *
 * AUTO-GENERATED - Customize for your project
 */

#pragma once

#include <cstdint>
#include <cstring>

#include "MessageID.hpp"
#include "ProtocolConstants.hpp"
#include "ProtocolCallbacks.hpp"
#include "DecoderRegistry.hpp"
#include "MessageStructure.hpp"
"""

    def render_namespace_open(self, namespace: str = "Protocol") -> str:
        """Render namespace opening."""
        return f"\nnamespace {namespace} {{\n"

    def render_namespace_close(self, namespace: str = "Protocol") -> str:
        """Render namespace closing."""
        return f"\n}}  // namespace {namespace}\n"

    def render_class_declaration(self, class_name: str) -> str:
        """Render class declaration opening."""
        return f"""
class {class_name} : public ProtocolCallbacks {{
public:
"""

    def render_class_close(self) -> str:
        """Render class closing."""
        return "};\n"

    def render_constructor(self, class_name: str, transport_type: str) -> str:
        """Render constructor."""
        return f"""    explicit {class_name}({transport_type}& transport)
        : transport_(transport) {{
        transport_.setOnReceive([this](const uint8_t* data, size_t len) {{
            dispatch(data, len);
        }});
    }}

    ~{class_name}() = default;

    // Non-copyable, non-movable
    {class_name}(const {class_name}&) = delete;
    {class_name}& operator=(const {class_name}&) = delete;
    {class_name}({class_name}&&) = delete;
    {class_name}& operator=({class_name}&&) = delete;
"""

    def render_send_method_signature(self) -> str:
        """Render send method signature."""
        return "    template <typename T>\n    void send(const T& message)"

    def render_send_method_body_start(self) -> str:
        """Render start of send method body."""
        return """ {
        constexpr MessageID messageId = T::MESSAGE_ID;

        // Encode payload
        uint8_t payload[T::MAX_PAYLOAD_SIZE];
        uint16_t payloadLen = message.encode(payload, sizeof(payload));

        // Build frame
        uint8_t frame[MAX_MESSAGE_SIZE];
        uint16_t offset = 0;
"""

    def render_send_method_body_end(self) -> str:
        """Render end of send method body."""
        return """
        // Send frame
        transport_.send(frame, offset);
    }
"""

    def render_dispatch_method_signature(self) -> str:
        """Render dispatch method signature."""
        return "    void dispatch(const uint8_t* data, size_t len)"

    def render_private_section(self, transport_type: str) -> str:
        """Render private section."""
        return f"""
private:
    {transport_type}& transport_;
"""

    def render_memcpy(self, dest: str, src: str, size: str) -> str:
        """Render memcpy call."""
        return f"std::memcpy({dest}, {src}, {size});"

    def render_cast_message_id(self) -> str:
        """Render message ID cast."""
        return "static_cast<uint8_t>(messageId)"
```

#### 5.2 Créer protocol/mixins/languages/java.py

```python
"""
Java Language Mixin for Protocol Renderers.

Provides Java syntax for protocol template generation.
"""

from pathlib import Path


class JavaProtocolMixin:
    """
    Mixin providing Java syntax for protocol templates.

    Must be combined with a FramingMixin and ProtocolRendererBase.
    """

    def __init__(self, package: str = "protocol") -> None:
        self.package = package

    @property
    def is_cpp(self) -> bool:
        return False

    @property
    def is_java(self) -> bool:
        return True

    @property
    def file_extension(self) -> str:
        return ".java"

    def render_file_header(self, output_path: Path) -> str:
        """Render Java file header with package and imports."""
        return f"""package {self.package};

/**
 * {output_path.stem} - Protocol Handler Template
 *
 * AUTO-GENERATED - Customize for your project
 */

import {self.package}.struct.*;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
"""

    def render_namespace_open(self, namespace: str = "") -> str:
        """Java doesn't have namespaces, return empty."""
        return ""

    def render_namespace_close(self, namespace: str = "") -> str:
        """Java doesn't have namespaces, return empty."""
        return ""

    def render_class_declaration(self, class_name: str) -> str:
        """Render class declaration opening."""
        return f"""
public class {class_name} extends ProtocolCallbacks {{
"""

    def render_class_close(self) -> str:
        """Render class closing."""
        return "}  // class\n"

    def render_constructor(self, class_name: str, transport_type: str) -> str:
        """Render constructor - abstract in template."""
        return f"""    // TODO: Implement constructor with your transport
    // public {class_name}({transport_type} transport) {{ ... }}
"""

    def render_send_method_signature(self) -> str:
        """Render send method signature."""
        return "    public <T> void send(T message)"

    def render_send_method_body_start(self) -> str:
        """Render start of send method body."""
        return """ {
        if (message == null) return;

        try {
            // Get MESSAGE_ID via reflection
            Field idField = message.getClass().getField("MESSAGE_ID");
            MessageID messageId = (MessageID) idField.get(null);

            // Encode payload
            Method encodeMethod = message.getClass().getMethod("encode");
            byte[] payload = (byte[]) encodeMethod.invoke(message);

            // Build frame
            byte[] frame = new byte[ProtocolConstants.MAX_MESSAGE_SIZE];
            int offset = 0;
"""

    def render_send_method_body_end(self) -> str:
        """Render end of send method body."""
        return """
            // TODO: Send via your transport
            // transport.send(frame, 0, offset);

        } catch (Exception e) {
            throw new RuntimeException("Failed to send: " + e.getMessage(), e);
        }
    }
"""

    def render_dispatch_method_signature(self) -> str:
        """Render dispatch method signature."""
        return "    public void dispatch(byte[] data)"

    def render_private_section(self, transport_type: str) -> str:
        """Render private section."""
        return f"""
    // TODO: Add your transport member
    // private {transport_type} transport;
"""

    def render_arraycopy(self, src: str, src_pos: str, dest: str, dest_pos: str, length: str) -> str:
        """Render System.arraycopy call."""
        return f"System.arraycopy({src}, {src_pos}, {dest}, {dest_pos}, {length});"

    def render_cast_message_id(self) -> str:
        """Render message ID cast."""
        return "messageId.getValue()"
```

#### 5.3 Créer protocol/mixins/languages/__init__.py

```python
"""
Language Mixins for Protocol Renderers.

Each mixin provides language-specific syntax.
"""

from protocol_codegen.generators.renderers.protocol.mixins.languages.cpp import (
    CppProtocolMixin,
)
from protocol_codegen.generators.renderers.protocol.mixins.languages.java import (
    JavaProtocolMixin,
)

__all__ = [
    "CppProtocolMixin",
    "JavaProtocolMixin",
]
```

#### 5.4 Tests

```bash
# Test imports
.venv/Scripts/python.exe -c "
from protocol_codegen.generators.renderers.protocol.mixins.languages import (
    CppProtocolMixin,
    JavaProtocolMixin,
)
print('CppProtocolMixin:', CppProtocolMixin)
print('JavaProtocolMixin:', JavaProtocolMixin)

# Test mixin usage
cpp = CppProtocolMixin()
java = JavaProtocolMixin(package='com.example')

print('C++ is_cpp:', cpp.is_cpp)
print('Java is_java:', java.is_java)
print('Java package:', java.package)
print('OK')
"

# Tous les tests
.venv/Scripts/python.exe -m pytest -v --tb=short
```

#### 5.5 Commit

```bash
git add -A && git commit -m "feat(mixins): add language mixins for protocol renderers

- Create CppProtocolMixin with C++ syntax methods
- Create JavaProtocolMixin with Java syntax methods
- Both provide: file_header, class_declaration, send_method, etc.
- Mixins are independent of protocol framing"
```

#### Critères de Succès
- [x] CppProtocolMixin créé avec toutes les méthodes
- [x] JavaProtocolMixin créé avec toutes les méthodes
- [x] __init__.py avec exports
- [x] Imports fonctionnent
- [x] Tests passent (commit 795c81d)

---

### Phase 6: Mixins Protocol

**Objectif:** Créer les mixins pour framing Serial8 et SysEx

**Durée estimée:** 1h

#### 6.1 Créer protocol/mixins/framings/serial8.py

```python
"""
Serial8 Framing Mixin for Protocol Renderers.

Provides Serial8 protocol framing (COBS, MessageID prefix).
"""


class Serial8FramingMixin:
    """
    Mixin providing Serial8 framing for protocol templates.

    Wire format: [MessageID][payload...]
    Framing: COBS handled by transport layer
    """

    @property
    def protocol_name(self) -> str:
        return "Serial8"

    @property
    def transport_description(self) -> str:
        return "USB Serial with COBS framing"

    @property
    def default_transport_type(self) -> str:
        if self.is_cpp:
            return "oc::hal::ISerialTransport"
        return "ISerialTransport"

    def render_framing_constants(self) -> str:
        """Render protocol-specific constants usage."""
        if self.is_cpp:
            return """        using Protocol::MAX_MESSAGE_SIZE;
        using Protocol::MESSAGE_TYPE_OFFSET;
        using Protocol::PAYLOAD_OFFSET;
"""
        return ""

    def render_frame_build(self) -> str:
        """Render frame building code (send path)."""
        if self.is_cpp:
            return f"""
        // Serial8 frame: [MessageID][payload...]
        frame[offset++] = {self.render_cast_message_id()};
        {self.render_memcpy("frame + offset", "payload", "payloadLen")}
        offset += payloadLen;
"""
        else:
            return f"""
            // Serial8 frame: [MessageID][payload...]
            frame[offset++] = {self.render_cast_message_id()};
            {self.render_arraycopy("payload", "0", "frame", "offset", "payload.length")}
            offset += payload.length;
"""

    def render_frame_validate(self) -> str:
        """Render frame validation code (receive path)."""
        if self.is_cpp:
            return """        if (data == nullptr || len < MIN_MESSAGE_LENGTH) {
            return;
        }
"""
        else:
            return """        if (data == null || data.length < ProtocolConstants.MIN_MESSAGE_LENGTH) {
            return;
        }
"""

    def render_frame_parse(self) -> str:
        """Render frame parsing code (receive path)."""
        if self.is_cpp:
            return """
        MessageID messageId = static_cast<MessageID>(data[MESSAGE_TYPE_OFFSET]);
        uint16_t payloadLen = len - PAYLOAD_OFFSET;
        const uint8_t* payload = data + PAYLOAD_OFFSET;

        DecoderRegistry::dispatch(*this, messageId, payload, payloadLen);
"""
        else:
            return """
        byte idByte = data[ProtocolConstants.MESSAGE_TYPE_OFFSET];
        MessageID messageId = MessageID.fromValue(idByte);
        if (messageId == null) return;

        int payloadLen = data.length - ProtocolConstants.PAYLOAD_OFFSET;
        byte[] payload = new byte[payloadLen];
        System.arraycopy(data, ProtocolConstants.PAYLOAD_OFFSET, payload, 0, payloadLen);

        DecoderRegistry.dispatch(this, messageId, payload);
"""

    def render_transport_includes(self) -> str:
        """Render transport-specific includes."""
        if self.is_cpp:
            return '#include <oc/hal/ISerialTransport.hpp>\n'
        return ""
```

#### 6.2 Créer protocol/mixins/framings/sysex.py

```python
"""
SysEx Framing Mixin for Protocol Renderers.

Provides SysEx MIDI protocol framing (F0...F7).
"""


class SysExFramingMixin:
    """
    Mixin providing SysEx framing for protocol templates.

    Wire format: [F0][MANUFACTURER_ID][DEVICE_ID][MessageID][payload...][F7]
    All payload bytes must be < 0x80 (7-bit encoding)
    """

    @property
    def protocol_name(self) -> str:
        return "SysEx"

    @property
    def transport_description(self) -> str:
        return "MIDI SysEx"

    @property
    def default_transport_type(self) -> str:
        if self.is_cpp:
            return "IMidiTransport"
        return "MidiOut"

    def render_framing_constants(self) -> str:
        """Render protocol-specific constants usage."""
        if self.is_cpp:
            return """        using Protocol::SYSEX_START;
        using Protocol::SYSEX_END;
        using Protocol::MANUFACTURER_ID;
        using Protocol::DEVICE_ID;
        using Protocol::MAX_MESSAGE_SIZE;
"""
        return ""

    def render_frame_build(self) -> str:
        """Render frame building code (send path)."""
        if self.is_cpp:
            return f"""
        // SysEx frame: [F0][MANUF][DEVICE][MessageID][payload...][F7]
        frame[offset++] = SYSEX_START;
        frame[offset++] = MANUFACTURER_ID;
        frame[offset++] = DEVICE_ID;
        frame[offset++] = {self.render_cast_message_id()};
        {self.render_memcpy("frame + offset", "payload", "payloadLen")}
        offset += payloadLen;
        frame[offset++] = SYSEX_END;
"""
        else:
            return f"""
            // SysEx frame: [F0][MANUF][DEVICE][MessageID][payload...][F7]
            frame[offset++] = ProtocolConstants.SYSEX_START;
            frame[offset++] = ProtocolConstants.MANUFACTURER_ID;
            frame[offset++] = ProtocolConstants.DEVICE_ID;
            frame[offset++] = {self.render_cast_message_id()};
            {self.render_arraycopy("payload", "0", "frame", "offset", "payload.length")}
            offset += payload.length;
            frame[offset++] = ProtocolConstants.SYSEX_END;
"""

    def render_frame_validate(self) -> str:
        """Render frame validation code (receive path)."""
        if self.is_cpp:
            return """        if (data == nullptr || len < MIN_MESSAGE_LENGTH) {
            return;
        }

        if (data[0] != SYSEX_START || data[len - 1] != SYSEX_END) {
            return;
        }

        if (data[1] != MANUFACTURER_ID || data[2] != DEVICE_ID) {
            return;
        }
"""
        else:
            return """        if (data == null || data.length < ProtocolConstants.MIN_MESSAGE_LENGTH) {
            return;
        }

        if (data[0] != ProtocolConstants.SYSEX_START ||
            data[data.length - 1] != ProtocolConstants.SYSEX_END) {
            return;
        }

        if (data[1] != ProtocolConstants.MANUFACTURER_ID ||
            data[2] != ProtocolConstants.DEVICE_ID) {
            return;
        }
"""

    def render_frame_parse(self) -> str:
        """Render frame parsing code (receive path)."""
        if self.is_cpp:
            return """
        MessageID messageId = static_cast<MessageID>(data[MESSAGE_TYPE_OFFSET]);
        uint16_t payloadLen = len - MIN_MESSAGE_LENGTH;
        const uint8_t* payload = data + PAYLOAD_OFFSET;

        DecoderRegistry::dispatch(*this, messageId, payload, payloadLen);
"""
        else:
            return """
        byte idByte = data[ProtocolConstants.MESSAGE_TYPE_OFFSET];
        MessageID messageId = MessageID.fromValue(idByte);
        if (messageId == null) return;

        int payloadLen = data.length - ProtocolConstants.MIN_MESSAGE_LENGTH;
        byte[] payload = new byte[payloadLen];
        System.arraycopy(data, ProtocolConstants.PAYLOAD_OFFSET, payload, 0, payloadLen);

        DecoderRegistry.dispatch(this, messageId, payload);
"""

    def render_transport_includes(self) -> str:
        """Render transport-specific includes."""
        if self.is_cpp:
            return ""  # SysEx typically uses existing MIDI includes
        return ""
```

#### 6.3 Créer protocol/mixins/framings/__init__.py

```python
"""
Framing Mixins for Protocol Renderers.

Each mixin provides protocol-specific framing logic.
"""

from protocol_codegen.generators.renderers.protocol.mixins.framings.serial8 import (
    Serial8FramingMixin,
)
from protocol_codegen.generators.renderers.protocol.mixins.framings.sysex import (
    SysExFramingMixin,
)

__all__ = [
    "Serial8FramingMixin",
    "SysExFramingMixin",
]
```

#### 6.4 Tests

```bash
# Test imports et composition
.venv/Scripts/python.exe -c "
from protocol_codegen.generators.renderers.protocol.mixins.languages import (
    CppProtocolMixin,
    JavaProtocolMixin,
)
from protocol_codegen.generators.renderers.protocol.mixins.framings import (
    Serial8FramingMixin,
    SysExFramingMixin,
)

# Test composition (simule ce que feront les implémentations)
class TestSerial8Cpp(CppProtocolMixin, Serial8FramingMixin):
    pass

class TestSysExJava(JavaProtocolMixin, SysExFramingMixin):
    def __init__(self):
        JavaProtocolMixin.__init__(self, package='test')

s8cpp = TestSerial8Cpp()
print('Serial8 C++ protocol:', s8cpp.protocol_name)
print('Serial8 C++ is_cpp:', s8cpp.is_cpp)
print('Serial8 C++ frame_build:')
print(s8cpp.render_frame_build())

sxjava = TestSysExJava()
print('SysEx Java protocol:', sxjava.protocol_name)
print('SysEx Java is_java:', sxjava.is_java)
print('OK')
"

# Tous les tests
.venv/Scripts/python.exe -m pytest -v --tb=short
```

#### 6.5 Commit

```bash
git add -A && git commit -m "feat(mixins): add framing mixins for protocol renderers

- Create Serial8FramingMixin with COBS/Serial framing
- Create SysExFramingMixin with MIDI F0/F7 framing
- Both provide: frame_build, frame_validate, frame_parse
- Mixins use language mixin methods (is_cpp, render_memcpy, etc.)"
```

#### Critères de Succès
- [x] Serial8FramingMixin créé
- [x] SysExFramingMixin créé
- [x] Composition fonctionne (C++ + Serial8, Java + SysEx)
- [x] __init__.py avec exports
- [x] Tests passent (commit 1f5c3b7)

---

### Phase 7: Implémentation Renderers

**Objectif:** Créer les renderers concrets par composition de mixins

**Durée estimée:** 2h

#### 7.1 Créer protocol/base.py

```python
"""
Base Protocol Renderer.

Template method pattern for protocol template generation.
"""

from abc import ABC
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from protocol_codegen.core.message import Message


class ProtocolRendererBase(ABC):
    """
    Base class for protocol template renderers.

    Uses template method pattern - subclasses provide mixins,
    this class provides the assembly logic.
    """

    def render(
        self,
        messages: list["Message"],
        output_path: Path,
        class_name: str = "Protocol",
        namespace: str = "Protocol",
    ) -> str:
        """
        Render complete protocol template file.

        Args:
            messages: List of message definitions
            output_path: Target file path
            class_name: Protocol class name
            namespace: C++ namespace (ignored for Java)

        Returns:
            Generated file content
        """
        parts = []

        # File header
        parts.append(self.render_file_header(output_path))
        parts.append(self.render_transport_includes())

        # Namespace (C++ only)
        parts.append(self.render_namespace_open(namespace))

        # Class
        parts.append(self.render_class_declaration(class_name))
        parts.append(self.render_constructor(class_name, self.default_transport_type))

        # Methods include (C++ only for .inl)
        if self.is_cpp:
            parts.append('\n#include "ProtocolMethods.inl"\n')

        # Send method
        parts.append(self.render_send_method_signature())
        parts.append(self.render_send_method_body_start())
        parts.append(self.render_framing_constants())
        parts.append(self.render_frame_build())
        parts.append(self.render_send_method_body_end())

        # Dispatch method
        parts.append(self._render_dispatch_method())

        # Private section
        parts.append(self.render_private_section(self.default_transport_type))

        # Close class
        parts.append(self.render_class_close())

        # Close namespace (C++ only)
        parts.append(self.render_namespace_close(namespace))

        # Usage example
        parts.append(self._render_usage_example(messages, class_name))

        return "".join(parts)

    def _render_dispatch_method(self) -> str:
        """Render complete dispatch method."""
        parts = [
            "\n",
            self.render_dispatch_method_signature(),
            " {\n",
            self.render_frame_validate(),
            self.render_frame_parse(),
            "    }\n",
        ]
        return "".join(parts)

    def _render_usage_example(
        self,
        messages: list["Message"],
        class_name: str,
    ) -> str:
        """Render usage example as comments."""
        lines = ["\n// " + "=" * 76]
        lines.append(f"// USAGE EXAMPLE")
        lines.append("// " + "=" * 76)
        lines.append("//")
        lines.append(f"// {class_name} protocol(...);")
        lines.append("//")
        lines.append("// // Register callbacks")

        # Show first 3 TO_CONTROLLER messages as callback examples
        count = 0
        for msg in messages:
            if msg.is_to_controller() and count < 3:
                pascal = "".join(w.capitalize() for w in msg.name.split("_"))
                lines.append(f"// protocol.on{pascal} = [](const {pascal}Message& msg) {{ }};")
                count += 1

        lines.append("//")
        lines.append("// // Send messages")

        # Show first 3 TO_HOST messages as send examples
        count = 0
        for msg in messages:
            if msg.is_to_host() and count < 3:
                pascal = "".join(w.capitalize() for w in msg.name.split("_"))
                lines.append(f"// protocol.send({pascal}Message{{...}});")
                count += 1

        lines.append("")
        return "\n".join(lines)
```

#### 7.2 Créer les 4 implémentations

**protocol/implementations/serial8_cpp.py:**
```python
"""Serial8 C++ Protocol Renderer."""

from pathlib import Path

from protocol_codegen.generators.renderers.protocol.base import ProtocolRendererBase
from protocol_codegen.generators.renderers.protocol.mixins.languages.cpp import (
    CppProtocolMixin,
)
from protocol_codegen.generators.renderers.protocol.mixins.framings.serial8 import (
    Serial8FramingMixin,
)
from protocol_codegen.generators.renderers.registry import register_renderer


@register_renderer("protocol", "cpp", "serial8")
class Serial8CppProtocolRenderer(
    CppProtocolMixin,
    Serial8FramingMixin,
    ProtocolRendererBase,
):
    """
    Protocol.hpp.template renderer for Serial8 + C++.

    Combines:
    - CppProtocolMixin: C++ syntax
    - Serial8FramingMixin: COBS/Serial framing
    - ProtocolRendererBase: Assembly logic
    """
    pass
```

**protocol/implementations/serial8_java.py:**
```python
"""Serial8 Java Protocol Renderer."""

from protocol_codegen.generators.renderers.protocol.base import ProtocolRendererBase
from protocol_codegen.generators.renderers.protocol.mixins.languages.java import (
    JavaProtocolMixin,
)
from protocol_codegen.generators.renderers.protocol.mixins.framings.serial8 import (
    Serial8FramingMixin,
)
from protocol_codegen.generators.renderers.registry import register_renderer


@register_renderer("protocol", "java", "serial8")
class Serial8JavaProtocolRenderer(
    JavaProtocolMixin,
    Serial8FramingMixin,
    ProtocolRendererBase,
):
    """
    Protocol.java.template renderer for Serial8 + Java.
    """

    def __init__(self, package: str = "protocol") -> None:
        JavaProtocolMixin.__init__(self, package)
```

**protocol/implementations/sysex_cpp.py:**
```python
"""SysEx C++ Protocol Renderer."""

from protocol_codegen.generators.renderers.protocol.base import ProtocolRendererBase
from protocol_codegen.generators.renderers.protocol.mixins.languages.cpp import (
    CppProtocolMixin,
)
from protocol_codegen.generators.renderers.protocol.mixins.framings.sysex import (
    SysExFramingMixin,
)
from protocol_codegen.generators.renderers.registry import register_renderer


@register_renderer("protocol", "cpp", "sysex")
class SysExCppProtocolRenderer(
    CppProtocolMixin,
    SysExFramingMixin,
    ProtocolRendererBase,
):
    """
    Protocol.hpp.template renderer for SysEx + C++.
    """
    pass
```

**protocol/implementations/sysex_java.py:**
```python
"""SysEx Java Protocol Renderer."""

from protocol_codegen.generators.renderers.protocol.base import ProtocolRendererBase
from protocol_codegen.generators.renderers.protocol.mixins.languages.java import (
    JavaProtocolMixin,
)
from protocol_codegen.generators.renderers.protocol.mixins.framings.sysex import (
    SysExFramingMixin,
)
from protocol_codegen.generators.renderers.registry import register_renderer


@register_renderer("protocol", "java", "sysex")
class SysExJavaProtocolRenderer(
    JavaProtocolMixin,
    SysExFramingMixin,
    ProtocolRendererBase,
):
    """
    Protocol.java.template renderer for SysEx + Java.
    """

    def __init__(self, package: str = "protocol") -> None:
        JavaProtocolMixin.__init__(self, package)
```

#### 7.3 Créer protocol/implementations/__init__.py

```python
"""
Protocol Renderer Implementations.

Concrete renderers created by combining language + framing mixins.
"""

# Import to trigger registration
from protocol_codegen.generators.renderers.protocol.implementations.serial8_cpp import (
    Serial8CppProtocolRenderer,
)
from protocol_codegen.generators.renderers.protocol.implementations.serial8_java import (
    Serial8JavaProtocolRenderer,
)
from protocol_codegen.generators.renderers.protocol.implementations.sysex_cpp import (
    SysExCppProtocolRenderer,
)
from protocol_codegen.generators.renderers.protocol.implementations.sysex_java import (
    SysExJavaProtocolRenderer,
)

__all__ = [
    "Serial8CppProtocolRenderer",
    "Serial8JavaProtocolRenderer",
    "SysExCppProtocolRenderer",
    "SysExJavaProtocolRenderer",
]
```

#### 7.4 Mettre à jour protocol/__init__.py

```python
"""
Protocol Renderers.

Mixin-based renderers for protocol template generation.
"""

from protocol_codegen.generators.renderers.protocol.base import ProtocolRendererBase
from protocol_codegen.generators.renderers.protocol.implementations import (
    Serial8CppProtocolRenderer,
    Serial8JavaProtocolRenderer,
    SysExCppProtocolRenderer,
    SysExJavaProtocolRenderer,
)

__all__ = [
    "ProtocolRendererBase",
    "Serial8CppProtocolRenderer",
    "Serial8JavaProtocolRenderer",
    "SysExCppProtocolRenderer",
    "SysExJavaProtocolRenderer",
]
```

#### 7.5 Créer tests/generators/renderers/test_protocol_renderers.py

```python
"""Tests for protocol renderers."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from protocol_codegen.generators.renderers.protocol import (
    Serial8CppProtocolRenderer,
    Serial8JavaProtocolRenderer,
    SysExCppProtocolRenderer,
    SysExJavaProtocolRenderer,
)


@pytest.fixture
def mock_message():
    """Create a mock message."""
    msg = MagicMock()
    msg.name = "test_message"
    msg.is_to_controller.return_value = True
    msg.is_to_host.return_value = False
    return msg


class TestSerial8CppProtocolRenderer:
    def test_render_contains_pragma_once(self, mock_message):
        renderer = Serial8CppProtocolRenderer()
        output = renderer.render([mock_message], Path("Protocol.hpp"))
        assert "#pragma once" in output

    def test_render_contains_serial8_framing(self, mock_message):
        renderer = Serial8CppProtocolRenderer()
        output = renderer.render([mock_message], Path("Protocol.hpp"))
        assert "MESSAGE_TYPE_OFFSET" in output
        # No SYSEX_START for Serial8
        assert "SYSEX_START" not in output


class TestSysExJavaProtocolRenderer:
    def test_render_contains_package(self, mock_message):
        renderer = SysExJavaProtocolRenderer(package="com.example")
        output = renderer.render([mock_message], Path("Protocol.java"))
        assert "package com.example;" in output

    def test_render_contains_sysex_framing(self, mock_message):
        renderer = SysExJavaProtocolRenderer()
        output = renderer.render([mock_message], Path("Protocol.java"))
        assert "SYSEX_START" in output
        assert "SYSEX_END" in output
```

#### 7.6 Tests

```bash
# Test unitaires nouveaux
.venv/Scripts/python.exe -m pytest tests/generators/renderers/ -v --tb=short

# Test registry
.venv/Scripts/python.exe -c "
from protocol_codegen.generators.renderers import get_renderer
from protocol_codegen.generators.backends import CppBackend, JavaBackend
from protocol_codegen.generators.common.encoding import Serial8EncodingStrategy, SysExEncodingStrategy

# Force import des implementations pour enregistrement
from protocol_codegen.generators.renderers.protocol.implementations import *

cpp = CppBackend()
java = JavaBackend()
serial8 = Serial8EncodingStrategy()
sysex = SysExEncodingStrategy()

# Ces appels doivent fonctionner
r1 = get_renderer('protocol', cpp, serial8)
r2 = get_renderer('protocol', java, sysex)
print('Serial8 C++ renderer:', type(r1).__name__)
print('SysEx Java renderer:', type(r2).__name__)
print('OK')
"

# Tous les tests
.venv/Scripts/python.exe -m pytest -v --tb=short
```

#### 7.7 Commit

```bash
git add -A && git commit -m "feat(renderers): implement protocol renderers with mixins

- Create ProtocolRendererBase with template method pattern
- Implement Serial8CppProtocolRenderer
- Implement Serial8JavaProtocolRenderer
- Implement SysExCppProtocolRenderer
- Implement SysExJavaProtocolRenderer
- Add tests for protocol renderers
- Register all renderers via decorator"
```

#### Critères de Succès
- [ ] ProtocolRendererBase créé
- [ ] 4 implémentations créées
- [ ] Tests unitaires ajoutés
- [ ] Registry fonctionne
- [ ] Tous les tests passent

---

### Phase 8: Intégration Orchestrateurs

**Objectif:** Modifier Serial8Generator et SysExGenerator pour utiliser les nouveaux renderers

**Durée estimée:** 1h30

#### 8.1 Modifier methods/serial8/generator.py

```python
# AVANT - import
from protocol_codegen.generators.serial8.cpp import (
    generate_protocol_template_hpp,
    ...
)
from protocol_codegen.generators.serial8.java import (
    generate_protocol_template_java,
    ...
)

# APRÈS - import
from protocol_codegen.generators.renderers.protocol import (
    Serial8CppProtocolRenderer,
    Serial8JavaProtocolRenderer,
)

# AVANT - dans _generate_cpp (~ligne 173-178)
cpp_protocol_template_path = cpp_base / "Protocol.hpp.template"
was_written = write_if_changed(
    cpp_protocol_template_path,
    generate_protocol_template_hpp(self.messages, cpp_protocol_template_path),
)

# APRÈS
cpp_protocol_template_path = cpp_base / "Protocol.hpp.template"
protocol_renderer = Serial8CppProtocolRenderer()
was_written = write_if_changed(
    cpp_protocol_template_path,
    protocol_renderer.render(self.messages, cpp_protocol_template_path),
)

# AVANT - dans _generate_java (~ligne 300-306)
java_protocol_template_path = java_base / "Protocol.java.template"
was_written = write_if_changed(
    java_protocol_template_path,
    generate_protocol_template_java(
        self.messages, java_protocol_template_path, java_package
    ),
)

# APRÈS
java_protocol_template_path = java_base / "Protocol.java.template"
protocol_renderer = Serial8JavaProtocolRenderer(package=java_package)
was_written = write_if_changed(
    java_protocol_template_path,
    protocol_renderer.render(self.messages, java_protocol_template_path),
)
```

#### 8.2 Modifier methods/sysex/generator.py

```python
# Mêmes changements mais avec SysExCppProtocolRenderer et SysExJavaProtocolRenderer
```

#### 8.3 Tests

```bash
# Génération end-to-end (TEST CRITIQUE)
cd ../../midi-studio/plugin-bitwig
./script/protocol/generate_protocol.sh

# Vérifier que les fichiers générés sont corrects
diff -q src/protocol/Protocol.hpp.template src/protocol/Protocol.hpp.template.backup || echo "Files differ (expected if backup exists)"

# Tests unitaires
cd ../../../open-control/protocol-codegen
.venv/Scripts/python.exe -m pytest -v --tb=short
```

#### 8.4 Commit

```bash
git add -A && git commit -m "refactor(generators): use new protocol renderers in orchestrators

- Update Serial8Generator to use Serial8Cpp/JavaProtocolRenderer
- Update SysExGenerator to use SysExCpp/JavaProtocolRenderer
- Remove imports of old generate_protocol_template_* functions
- All tests pass, generation produces equivalent output"
```

#### Critères de Succès
- [ ] Serial8Generator utilise nouveaux renderers
- [ ] SysExGenerator utilise nouveaux renderers
- [ ] Génération produit output équivalent
- [ ] Tous les tests passent

---

### Phase 9: Nettoyage Final

**Objectif:** Supprimer tout le code obsolète, finaliser l'architecture

**Durée estimée:** 1h

#### 9.1 Supprimer les anciens protocol_generator.py

```bash
# Supprimer les fichiers
rm src/protocol_codegen/generators/serial8/cpp/protocol_generator.py
rm src/protocol_codegen/generators/serial8/java/protocol_generator.py
rm src/protocol_codegen/generators/sysex/cpp/protocol_generator.py
rm src/protocol_codegen/generators/sysex/java/protocol_generator.py
```

#### 9.2 Mettre à jour les __init__.py

**generators/serial8/cpp/__init__.py:**
```python
"""
C++ Code Generators for Serial8 Protocol.

Note: Protocol template generation now uses:
  - Serial8CppProtocolRenderer from renderers/protocol/
"""

from protocol_codegen.generators.common.cpp import (
    generate_constants_hpp,
    generate_decoder_registry_hpp,
    generate_enum_hpp,
    generate_message_structure_hpp,
    generate_messageid_hpp,
    generate_protocol_callbacks_hpp,
    generate_protocol_methods_hpp,
    generate_struct_hpp,
)

__all__ = [
    "generate_constants_hpp",
    "generate_decoder_registry_hpp",
    "generate_enum_hpp",
    "generate_message_structure_hpp",
    "generate_messageid_hpp",
    "generate_protocol_callbacks_hpp",
    "generate_protocol_methods_hpp",
    "generate_struct_hpp",
]
```

(Répéter pour serial8/java, sysex/cpp, sysex/java)

#### 9.3 Vérifier tous les imports

```bash
# Script de vérification
.venv/Scripts/python.exe -c "
import importlib
import sys

modules_to_check = [
    'protocol_codegen.generators',
    'protocol_codegen.generators.backends',
    'protocol_codegen.generators.common',
    'protocol_codegen.generators.common.encoding',
    'protocol_codegen.generators.templates',
    'protocol_codegen.generators.renderers',
    'protocol_codegen.generators.renderers.protocol',
    'protocol_codegen.generators.serial8.cpp',
    'protocol_codegen.generators.serial8.java',
    'protocol_codegen.generators.sysex.cpp',
    'protocol_codegen.generators.sysex.java',
    'protocol_codegen.methods.serial8.generator',
    'protocol_codegen.methods.sysex.generator',
]

for mod in modules_to_check:
    try:
        importlib.import_module(mod)
        print(f'✓ {mod}')
    except ImportError as e:
        print(f'✗ {mod}: {e}')
        sys.exit(1)

print('All imports OK')
"
```

#### 9.4 Tests finaux

```bash
# Tous les tests
.venv/Scripts/python.exe -m pytest -v --tb=short

# Linting
python -m ruff check src/ tests/

# Génération complète
cd ../../midi-studio/plugin-bitwig
./script/protocol/generate_protocol.sh

# Vérification visuelle des fichiers générés
cat src/protocol/Protocol.hpp.template | head -50
cat host/src/protocol/Protocol.java.template | head -50
```

#### 9.5 Commit final

```bash
git add -A && git commit -m "chore: remove legacy protocol generators

- Delete serial8/cpp/protocol_generator.py
- Delete serial8/java/protocol_generator.py
- Delete sysex/cpp/protocol_generator.py
- Delete sysex/java/protocol_generator.py
- Update __init__.py files to remove obsolete exports
- All functionality now provided by renderers/protocol/"
```

#### 9.6 Merge

```bash
# Squash ou merge selon préférence
git checkout main
git merge --no-ff refactor/mixin-architecture -m "feat: mixin-based architecture for protocol generators

Major refactoring of protocol-codegen:
- Extract ProtocolConfig to common/config.py
- Unify java_package as parameter
- Hide struct_utils from public API
- Implement mixin-based protocol renderers
- Zero duplication, clean architecture

Breaking changes:
- generate_enum_java() requires package parameter
- Protocol renderers moved to renderers/protocol/"
```

#### Critères de Succès
- [ ] Anciens protocol_generator.py supprimés
- [ ] __init__.py mis à jour
- [ ] Tous les imports fonctionnent
- [ ] Tous les tests passent
- [ ] Linting passe
- [ ] Génération fonctionne
- [ ] Merge sur main

---

## 4. Validation Finale

### Checklist Complète

```
Phase 0: Préparation
  [ ] Branche créée
  [ ] Tests initiaux passent
  [ ] Checkpoint commit

Phase 1: Extraction Config
  [x] common/config.py créé
  [x] Duplication supprimée
  [x] Tests passent

Phase 2: Unification java_package
  [x] java_package retiré de EnumDef
  [x] Paramètre ajouté à generate_enum_java
  [x] Orchestrateurs mis à jour
  [x] Tests passent

Phase 3: Nettoyage API
  [x] struct_utils cachés
  [x] API surface réduite
  [x] Tests passent

Phase 4: Infrastructure Renderers
  [x] Structure créée
  [x] ABCs définis
  [x] Registry fonctionnel

Phase 5: Mixins Langage
  [x] CppProtocolMixin créé
  [x] JavaProtocolMixin créé
  [x] Tests passent

Phase 6: Mixins Protocol
  [x] Serial8FramingMixin créé
  [x] SysExFramingMixin créé
  [x] Composition fonctionne

Phase 7: Implémentation Renderers
  [ ] 4 renderers créés
  [ ] Tests unitaires ajoutés
  [ ] Registry fonctionne

Phase 8: Intégration
  [ ] Serial8Generator utilise renderers
  [ ] SysExGenerator utilise renderers
  [ ] Génération équivalente

Phase 9: Nettoyage
  [ ] Anciens fichiers supprimés
  [ ] Imports vérifiés
  [ ] Merge sur main
```

### Métriques Finales Attendues

| Métrique | Avant | Après |
|----------|-------|-------|
| Tests | 405 | 420+ |
| Fichiers generators/ | 46 | ~35 |
| LOC duplication | ~30% | <5% |
| Ajout nouveau langage | 6+ fichiers | 1 mixin + N implémentations |
| Ajout nouveau protocole | 4+ fichiers | 1 mixin + N implémentations |

---

## 5. Rollback Strategy

Si problème majeur à n'importe quelle phase:

```bash
# Revenir au checkpoint
git checkout main
git branch -D refactor/mixin-architecture

# Ou revenir à un commit spécifique
git log --oneline
git reset --hard <commit-hash>
```

Le code legacy reste fonctionnel jusqu'à la Phase 9 - rollback possible à tout moment.

---

**Document prêt pour implémentation.**
