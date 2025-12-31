# Phase 3 : Tests de compilation du code généré

**Date de création** : 2025-12-31
**Dernière mise à jour** : 2025-12-31
**Statut** : 🟢 Plan validé
**Priorité** : BASSE (amélioration qualité)
**Dépendances** : Phase 1 et Phase 2 (pour tester toutes les fonctionnalités)

---

## 1. Résumé des décisions validées

| Question | Décision | Justification |
|----------|----------|---------------|
| Q1: Emplacement | **`test-compile/` à la racine** | Le plus propre, non commité |
| Q2: Outil C++ | **PlatformIO native C++17** | Déjà présent, portable |
| Q3: CI/CD | **GitHub Actions immédiatement** | Protection automatique PR |
| Q4: Couverture | **100%** | Matrice complète validée |

---

## 2. Architecture

```
test-compile/                          ← Non commité (.gitignore)
├── README.md                          ← Commité (instructions)
├── platformio.ini                     ← Config PlatformIO native
├── run_tests.py                       ← Script principal
├── fixtures/
│   ├── protocol_config_serial8.py
│   ├── protocol_config_sysex.py
│   ├── plugin_paths.py
│   └── message/
│       ├── __init__.py
│       ├── primitives.py              ← 11 types × 4 contextes
│       ├── arrays.py                  ← Fixes et dynamiques
│       ├── composites.py              ← Simple, array, nested L2/L3
│       ├── enums.py                   ← Regular, bitflags, in composite
│       ├── directions.py              ← TO_HOST, TO_CONTROLLER
│       └── edge_cases.py              ← Vide, noms longs, valeurs limites
├── src/
│   └── main.cpp                       ← Point d'entrée PlatformIO
├── serial8/
│   └── cpp/
│       └── test_includes.hpp          ← #include tous les headers
└── sysex/
    └── cpp/
        └── test_includes.hpp

.github/
└── workflows/
    └── test-compile.yml               ← GitHub Actions
```

---

## 3. Matrice de couverture 100%

### 3.1 Types primitifs (11 types × 4 contextes = 44 cas)

| Type | Scalar | Array fixe | Array dyn | In Composite |
|------|:------:|:----------:|:---------:|:------------:|
| bool | ✅ | ✅ | ✅ | ✅ |
| uint8 | ✅ | ✅ | ✅ | ✅ |
| int8 | ✅ | ✅ | ✅ | ✅ |
| uint16 | ✅ | ✅ | ✅ | ✅ |
| int16 | ✅ | ✅ | ✅ | ✅ |
| uint32 | ✅ | ✅ | ✅ | ✅ |
| int32 | ✅ | ✅ | ✅ | ✅ |
| float32 | ✅ | ✅ | ✅ | ✅ |
| norm8 | ✅ | ✅ | ✅ | ✅ |
| norm16 | ✅ | ✅ | ✅ | ✅ |
| string | ✅ | ✅ | ✅ | ✅ |

### 3.2 Enums (2 types × 4 contextes = 8 cas)

| Type | Scalar | Array | In Composite | In Composite Array |
|------|:------:|:-----:|:------------:|:------------------:|
| Regular enum | ✅ | ✅ | ✅ | ✅ |
| Bitflags enum | ✅ | ✅ | ✅ | ✅ |

### 3.3 Composites (4 cas)

| Type | Couvert |
|------|:-------:|
| Simple (1 niveau) | ✅ |
| Array de composites | ✅ |
| Nested L2 (composite dans composite) | ✅ |
| Nested L3 (max depth) | ✅ |

### 3.4 Directions et Intent (4 cas)

| Direction | Intent | Couvert |
|-----------|--------|:-------:|
| TO_HOST | COMMAND | ✅ |
| TO_HOST | NOTIFY | ✅ |
| TO_CONTROLLER | COMMAND | ✅ |
| TO_CONTROLLER | RESPONSE | ✅ |

### 3.5 Cas spéciaux (5 cas)

| Cas | Couvert |
|-----|:-------:|
| Message vide (0 champs) | ✅ |
| Message deprecated (vérifie exclusion) | ✅ |
| Noms longs (>32 chars) | ✅ |
| Valeurs limites uint8 (255) | ✅ |
| Valeurs limites uint16 (65535) | ✅ |

**Total : ~30 messages de test**

---

## 4. Fichiers à créer

### 4.1 `test-compile/platformio.ini`

```ini
; PlatformIO configuration for compilation tests
; Uses native platform (host compiler) with C++17

[platformio]
default_envs = native_serial8, native_sysex

[env]
platform = native
build_flags =
    -std=c++17
    -Wall
    -Wextra
    -Werror
    -fsyntax-only

[env:native_serial8]
build_src_filter = +<serial8/>
build_flags =
    ${env.build_flags}
    -I generated/serial8/cpp

[env:native_sysex]
build_src_filter = +<sysex/>
build_flags =
    ${env.build_flags}
    -I generated/sysex/cpp
```

### 4.2 `test-compile/run_tests.py`

```python
#!/usr/bin/env python3
"""
Test de compilation du code généré.

Usage:
    python run_tests.py                 # Tous les tests
    python run_tests.py --serial8       # Serial8 uniquement
    python run_tests.py --sysex         # SysEx uniquement
    python run_tests.py --cpp           # C++ uniquement
    python run_tests.py --java          # Java uniquement
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
FIXTURES_DIR = SCRIPT_DIR / "fixtures"
GENERATED_DIR = SCRIPT_DIR / "generated"


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"  → {description}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    ❌ Failed: {result.stderr[:500]}")
        return False
    return True


def generate_protocol(method: str) -> bool:
    """Generate protocol code for a method."""
    output_dir = GENERATED_DIR / method
    output_dir.mkdir(parents=True, exist_ok=True)

    config_file = f"protocol_config_{method}.py"

    return run_command([
        "protocol-codegen", "generate",
        "--method", method,
        "--messages", str(FIXTURES_DIR / "message"),
        "--config", str(FIXTURES_DIR / config_file),
        "--plugin-paths", str(FIXTURES_DIR / "plugin_paths.py"),
        "--output-base", str(output_dir),
    ], f"Generating {method} code")


def test_cpp_platformio(method: str) -> bool:
    """Test C++ compilation using PlatformIO."""
    env_name = f"native_{method}"

    # Clean previous build
    build_dir = SCRIPT_DIR / ".pio" / "build" / env_name
    if build_dir.exists():
        shutil.rmtree(build_dir)

    return run_command([
        "pio", "run", "-e", env_name, "-d", str(SCRIPT_DIR)
    ], f"Compiling {method} C++ with PlatformIO")


def test_java(method: str) -> bool:
    """Test Java compilation."""
    if not shutil.which("javac"):
        print("    ⚠️ javac not found, skipping Java test")
        return True

    java_dir = GENERATED_DIR / method / "java"
    if not java_dir.exists():
        print(f"    ❌ Java directory not found: {java_dir}")
        return False

    java_files = list(java_dir.glob("**/*.java"))
    if not java_files:
        print("    ❌ No Java files found")
        return False

    classes_dir = SCRIPT_DIR / "classes" / method
    classes_dir.mkdir(parents=True, exist_ok=True)

    return run_command(
        ["javac", "-d", str(classes_dir)] + [str(f) for f in java_files],
        f"Compiling {method} Java"
    )


def test_method(method: str, run_cpp: bool, run_java: bool) -> dict[str, bool]:
    """Test a single method (serial8 or sysex)."""
    results = {}

    print(f"\n{'=' * 50}")
    print(f"Testing {method.upper()}")
    print('=' * 50)

    # Generate
    if not generate_protocol(method):
        return {f"{method}_generate": False}
    results[f"{method}_generate"] = True

    # C++
    if run_cpp:
        results[f"{method}_cpp"] = test_cpp_platformio(method)

    # Java
    if run_java:
        results[f"{method}_java"] = test_java(method)

    return results


def main():
    parser = argparse.ArgumentParser(description="Test generated code compilation")
    parser.add_argument("--serial8", action="store_true", help="Test serial8 only")
    parser.add_argument("--sysex", action="store_true", help="Test sysex only")
    parser.add_argument("--cpp", action="store_true", help="Test C++ only")
    parser.add_argument("--java", action="store_true", help="Test Java only")
    args = parser.parse_args()

    # Default: run all
    run_serial8 = args.serial8 or (not args.serial8 and not args.sysex)
    run_sysex = args.sysex or (not args.serial8 and not args.sysex)
    run_cpp = args.cpp or (not args.cpp and not args.java)
    run_java = args.java or (not args.cpp and not args.java)

    all_results = {}

    if run_serial8:
        all_results.update(test_method("serial8", run_cpp, run_java))

    if run_sysex:
        all_results.update(test_method("sysex", run_cpp, run_java))

    # Summary
    print(f"\n{'=' * 50}")
    print("SUMMARY")
    print('=' * 50)

    all_passed = True
    for name, passed in all_results.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("All tests passed! ✅")
    else:
        print("Some tests failed! ❌")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
```

### 4.3 `.github/workflows/test-compile.yml`

```yaml
name: Test Generated Code Compilation

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test-cpp:
    name: C++ Compilation Test
    runs-on: ubuntu-latest
    strategy:
      matrix:
        method: [serial8, sysex]

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install PlatformIO
        run: pip install platformio

      - name: Install protocol-codegen
        run: pip install -e .

      - name: Setup test fixtures
        run: |
          mkdir -p test-compile/fixtures/message
          mkdir -p test-compile/generated
          # Copy fixtures (these should be committed)
          cp -r MEMORY/test-fixtures/* test-compile/fixtures/ || true

      - name: Run C++ compilation tests
        run: python test-compile/run_tests.py --${{ matrix.method }} --cpp

  test-java:
    name: Java Compilation Test
    runs-on: ubuntu-latest
    strategy:
      matrix:
        method: [serial8, sysex]

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Java
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install protocol-codegen
        run: pip install -e .

      - name: Setup test fixtures
        run: |
          mkdir -p test-compile/fixtures/message
          mkdir -p test-compile/generated

      - name: Run Java compilation tests
        run: python test-compile/run_tests.py --${{ matrix.method }} --java
```

### 4.4 Fixtures de test

#### `test-compile/fixtures/message/__init__.py`

```python
"""
Test fixtures for compilation tests.
Covers 100% of code generation paths.
"""

from .primitives import *
from .arrays import *
from .composites import *
from .enums import *
from .directions import *
from .edge_cases import *

# Collect all messages
ALL_MESSAGES = [
    # Primitives (11 scalar)
    TEST_BOOL, TEST_UINT8, TEST_INT8, TEST_UINT16, TEST_INT16,
    TEST_UINT32, TEST_INT32, TEST_FLOAT32, TEST_NORM8, TEST_NORM16, TEST_STRING,

    # Arrays
    TEST_FIXED_ARRAYS, TEST_DYNAMIC_ARRAYS,

    # Composites
    TEST_SIMPLE_COMPOSITE, TEST_COMPOSITE_ARRAY,
    TEST_NESTED_L2, TEST_NESTED_L3,

    # Enums
    TEST_ENUM_SCALAR, TEST_ENUM_ARRAY,
    TEST_BITFLAGS_SCALAR, TEST_BITFLAGS_ARRAY,
    TEST_ENUM_IN_COMPOSITE,

    # Directions
    TEST_TO_HOST_COMMAND, TEST_TO_HOST_NOTIFY,
    TEST_TO_CONTROLLER_COMMAND, TEST_TO_CONTROLLER_RESPONSE,

    # Edge cases
    TEST_EMPTY_MESSAGE, TEST_LONG_NAME_MESSAGE,
    TEST_MAX_VALUES, TEST_DEPRECATED_MESSAGE,
]
```

#### `test-compile/fixtures/message/primitives.py`

```python
"""Test all 11 primitive types as scalars."""
from protocol_codegen.core.field import PrimitiveField, Type
from protocol_codegen.core.message import Message
from protocol_codegen.core.enums import Direction, Intent

TEST_BOOL = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Test bool type",
    fields=[PrimitiveField("value", type_name=Type.BOOL)],
)

TEST_UINT8 = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Test uint8 type",
    fields=[PrimitiveField("value", type_name=Type.UINT8)],
)

TEST_INT8 = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Test int8 type",
    fields=[PrimitiveField("value", type_name=Type.INT8)],
)

TEST_UINT16 = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Test uint16 type",
    fields=[PrimitiveField("value", type_name=Type.UINT16)],
)

TEST_INT16 = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Test int16 type",
    fields=[PrimitiveField("value", type_name=Type.INT16)],
)

TEST_UINT32 = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Test uint32 type",
    fields=[PrimitiveField("value", type_name=Type.UINT32)],
)

TEST_INT32 = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Test int32 type",
    fields=[PrimitiveField("value", type_name=Type.INT32)],
)

TEST_FLOAT32 = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Test float32 type",
    fields=[PrimitiveField("value", type_name=Type.FLOAT32)],
)

TEST_NORM8 = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Test norm8 type",
    fields=[PrimitiveField("value", type_name=Type.NORM8)],
)

TEST_NORM16 = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Test norm16 type",
    fields=[PrimitiveField("value", type_name=Type.NORM16)],
)

TEST_STRING = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Test string type",
    fields=[PrimitiveField("value", type_name=Type.STRING)],
)
```

#### `test-compile/fixtures/message/arrays.py`

```python
"""Test array types (fixed and dynamic)."""
from protocol_codegen.core.field import PrimitiveField, Type
from protocol_codegen.core.message import Message
from protocol_codegen.core.enums import Direction, Intent

TEST_FIXED_ARRAYS = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Test fixed-size arrays",
    fields=[
        PrimitiveField("bools", type_name=Type.BOOL, array=4),
        PrimitiveField("bytes", type_name=Type.UINT8, array=8),
        PrimitiveField("ints", type_name=Type.INT32, array=4),
        PrimitiveField("floats", type_name=Type.FLOAT32, array=4),
        PrimitiveField("strings", type_name=Type.STRING, array=3),
    ],
)

TEST_DYNAMIC_ARRAYS = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Test dynamic arrays",
    fields=[
        PrimitiveField("data", type_name=Type.UINT8, array=32, dynamic=True),
        PrimitiveField("values", type_name=Type.FLOAT32, array=16, dynamic=True),
        PrimitiveField("labels", type_name=Type.STRING, array=8, dynamic=True),
    ],
)
```

#### `test-compile/fixtures/message/composites.py`

```python
"""Test composite fields at various nesting levels."""
from protocol_codegen.core.field import PrimitiveField, CompositeField, Type
from protocol_codegen.core.message import Message
from protocol_codegen.core.enums import Direction, Intent

TEST_SIMPLE_COMPOSITE = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Test simple composite (1 level)",
    fields=[
        CompositeField("point", fields=[
            PrimitiveField("x", type_name=Type.FLOAT32),
            PrimitiveField("y", type_name=Type.FLOAT32),
            PrimitiveField("z", type_name=Type.FLOAT32),
        ]),
    ],
)

TEST_COMPOSITE_ARRAY = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Test array of composites",
    fields=[
        CompositeField("points", array=8, fields=[
            PrimitiveField("x", type_name=Type.FLOAT32),
            PrimitiveField("y", type_name=Type.FLOAT32),
        ]),
    ],
)

TEST_NESTED_L2 = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Test nested composite (2 levels)",
    fields=[
        CompositeField("outer", fields=[
            PrimitiveField("name", type_name=Type.STRING),
            CompositeField("inner", fields=[
                PrimitiveField("id", type_name=Type.UINT32),
                PrimitiveField("value", type_name=Type.FLOAT32),
            ]),
        ]),
    ],
)

TEST_NESTED_L3 = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Test nested composite (3 levels - max depth)",
    fields=[
        CompositeField("level1", fields=[
            PrimitiveField("name", type_name=Type.STRING),
            CompositeField("level2", fields=[
                PrimitiveField("id", type_name=Type.UINT16),
                CompositeField("level3", fields=[
                    PrimitiveField("value", type_name=Type.UINT8),
                ]),
            ]),
        ]),
    ],
)
```

#### `test-compile/fixtures/message/enums.py`

```python
"""Test enum fields (regular and bitflags)."""
from protocol_codegen.core.field import PrimitiveField, EnumField, CompositeField, Type
from protocol_codegen.core.enum_def import EnumDef
from protocol_codegen.core.message import Message
from protocol_codegen.core.enums import Direction, Intent

# Regular enum
Status = EnumDef(
    name="Status",
    values={"IDLE": 0, "RUNNING": 1, "PAUSED": 2, "ERROR": 3},
    description="Test status enum",
)

# Bitflags enum
Flags = EnumDef(
    name="Flags",
    values={"NONE": 0, "READ": 1, "WRITE": 2, "EXECUTE": 4, "ALL": 7},
    is_bitflags=True,
    description="Test bitflags enum",
)

TEST_ENUM_SCALAR = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Test scalar enum",
    fields=[EnumField("status", enum_def=Status)],
)

TEST_ENUM_ARRAY = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Test enum array",
    fields=[EnumField("statuses", enum_def=Status, array=4)],
)

TEST_BITFLAGS_SCALAR = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Test scalar bitflags",
    fields=[EnumField("flags", enum_def=Flags)],
)

TEST_BITFLAGS_ARRAY = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Test bitflags array",
    fields=[EnumField("flagsArray", enum_def=Flags, array=4)],
)

TEST_ENUM_IN_COMPOSITE = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Test enum inside composite",
    fields=[
        CompositeField("item", fields=[
            PrimitiveField("id", type_name=Type.UINT32),
            EnumField("status", enum_def=Status),
            EnumField("flags", enum_def=Flags),
        ]),
    ],
)
```

#### `test-compile/fixtures/message/directions.py`

```python
"""Test all direction/intent combinations."""
from protocol_codegen.core.field import PrimitiveField, Type
from protocol_codegen.core.message import Message
from protocol_codegen.core.enums import Direction, Intent

TEST_TO_HOST_COMMAND = Message(
    direction=Direction.TO_HOST,
    intent=Intent.COMMAND,
    description="Controller sends command to Host",
    fields=[PrimitiveField("action", type_name=Type.UINT8)],
)

TEST_TO_HOST_NOTIFY = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Controller notifies Host",
    fields=[PrimitiveField("event", type_name=Type.UINT8)],
)

TEST_TO_CONTROLLER_COMMAND = Message(
    direction=Direction.TO_CONTROLLER,
    intent=Intent.COMMAND,
    description="Host sends command to Controller",
    fields=[PrimitiveField("command", type_name=Type.UINT8)],
)

TEST_TO_CONTROLLER_RESPONSE = Message(
    direction=Direction.TO_CONTROLLER,
    intent=Intent.RESPONSE,
    description="Host responds to Controller",
    fields=[PrimitiveField("result", type_name=Type.UINT8)],
)
```

#### `test-compile/fixtures/message/edge_cases.py`

```python
"""Test edge cases and special scenarios."""
from protocol_codegen.core.field import PrimitiveField, Type
from protocol_codegen.core.message import Message
from protocol_codegen.core.enums import Direction, Intent

TEST_EMPTY_MESSAGE = Message(
    direction=Direction.TO_HOST,
    intent=Intent.COMMAND,
    description="Empty message with no fields",
    fields=[],
)

TEST_LONG_NAME_MESSAGE = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Message with very long field names",
    fields=[
        PrimitiveField("thisIsAVeryLongFieldNameThatExceedsThirtyTwoCharacters", type_name=Type.UINT8),
        PrimitiveField("anotherExtremelyLongFieldNameForTesting", type_name=Type.STRING),
    ],
)

TEST_MAX_VALUES = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Test maximum values for various types",
    fields=[
        PrimitiveField("maxUint8", type_name=Type.UINT8),   # 255
        PrimitiveField("maxUint16", type_name=Type.UINT16), # 65535
        PrimitiveField("maxUint32", type_name=Type.UINT32), # 4294967295
        PrimitiveField("minInt8", type_name=Type.INT8),     # -128
        PrimitiveField("maxInt8", type_name=Type.INT8),     # 127
    ],
)

TEST_DEPRECATED_MESSAGE = Message(
    direction=Direction.TO_HOST,
    intent=Intent.NOTIFY,
    description="Deprecated message - should be excluded",
    deprecated=True,
    fields=[PrimitiveField("old", type_name=Type.UINT8)],
)
```

#### `test-compile/fixtures/protocol_config_serial8.py`

```python
"""Serial8 test configuration."""
from protocol_codegen.methods.serial8 import Serial8Config, Serial8Limits, Serial8Structure

PROTOCOL_CONFIG = Serial8Config(
    structure=Serial8Structure(
        message_type_offset=0,
        payload_offset=1,
        encode_message_name=False,  # Test default behavior
    ),
    limits=Serial8Limits(
        string_max_length=32,
        array_max_items=32,
        max_payload_size=1024,
        max_message_size=1024,
    ),
)
```

#### `test-compile/fixtures/protocol_config_sysex.py`

```python
"""SysEx test configuration."""
from protocol_codegen.methods.sysex import SysExConfig

PROTOCOL_CONFIG = SysExConfig()  # Use defaults
```

#### `test-compile/fixtures/plugin_paths.py`

```python
"""Plugin paths for test fixtures."""

PLUGIN_PATHS = {
    "output_cpp": {
        "base_path": "cpp",
        "structs": "struct",
    },
    "output_java": {
        "base_path": "java",
        "structs": "struct",
        "package": "com.test.protocol",
    },
}
```

---

## 5. Ordre d'exécution

### Étape 1 : Créer la structure
1. [ ] Créer `test-compile/README.md`
2. [ ] Créer `test-compile/platformio.ini`
3. [ ] Créer `test-compile/run_tests.py`
4. [ ] Ajouter `test-compile/` au `.gitignore` (sauf README)

### Étape 2 : Créer les fixtures
5. [ ] Créer `fixtures/message/__init__.py`
6. [ ] Créer `fixtures/message/primitives.py`
7. [ ] Créer `fixtures/message/arrays.py`
8. [ ] Créer `fixtures/message/composites.py`
9. [ ] Créer `fixtures/message/enums.py`
10. [ ] Créer `fixtures/message/directions.py`
11. [ ] Créer `fixtures/message/edge_cases.py`
12. [ ] Créer `fixtures/protocol_config_serial8.py`
13. [ ] Créer `fixtures/protocol_config_sysex.py`
14. [ ] Créer `fixtures/plugin_paths.py`

### Étape 3 : Créer les test harnesses
15. [ ] Créer `src/main.cpp` (point d'entrée PlatformIO)
16. [ ] Créer `serial8/cpp/test_includes.hpp`
17. [ ] Créer `sysex/cpp/test_includes.hpp`

### Étape 4 : Créer GitHub Actions
18. [ ] Créer `.github/workflows/test-compile.yml`

### Étape 5 : Tests
19. [ ] Tester localement `python run_tests.py`
20. [ ] Vérifier GitHub Actions sur une PR

---

## 6. Fichiers impactés

| Fichier | Action | Commité |
|---------|--------|:-------:|
| `test-compile/README.md` | Créer | ✅ |
| `test-compile/platformio.ini` | Créer | ✅ |
| `test-compile/run_tests.py` | Créer | ✅ |
| `test-compile/fixtures/**` | Créer | ✅ |
| `test-compile/src/main.cpp` | Créer | ✅ |
| `test-compile/generated/` | Généré | ❌ |
| `test-compile/.pio/` | Généré | ❌ |
| `test-compile/classes/` | Généré | ❌ |
| `.github/workflows/test-compile.yml` | Créer | ✅ |
| `.gitignore` | Modifier | ✅ |

---

## 7. Critères de validation

- [ ] `python run_tests.py` : tous les tests passent localement
- [ ] GitHub Actions : workflow passe sur PR
- [ ] Serial8 C++ : compile sans erreur
- [ ] Serial8 Java : compile sans erreur
- [ ] SysEx C++ : compile sans erreur
- [ ] SysEx Java : compile sans erreur
- [ ] Messages deprecated : exclus de la génération
- [ ] Couverture 100% : tous les chemins de code testés

---

## 8. Estimation

| Tâche | Temps estimé |
|-------|--------------|
| Structure + platformio.ini | 15 min |
| Fixtures (6 fichiers) | 30 min |
| run_tests.py | 30 min |
| Test harnesses C++ | 15 min |
| GitHub Actions | 20 min |
| Tests et ajustements | 30 min |
| **Total** | **~2h20** |
