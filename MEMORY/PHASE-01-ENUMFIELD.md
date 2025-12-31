# Phase 1 : Synchronisation SysEx avec Serial8

**Date de création** : 2025-12-31
**Dernière mise à jour** : 2025-12-31
**Statut** : 🟢 Plan validé
**Priorité** : HAUTE

---

## 1. Résumé des décisions validées

| Question | Décision | Justification |
|----------|----------|---------------|
| Q1: Copier ou factoriser enum_generators | **Copier** | Factorisation en phase ultérieure |
| Q2: Validation enum ≤127 pour SysEx | **Strict (erreur)** | Sécurité protocole 7-bit |
| Q3: fromHost dans sysex | **Supprimer** | Alignement sur serial8 |
| Q4: MESSAGE_NAME | **Serial8 only, default=false** | SysEx n'en a pas besoin |
| Q5: fromHost suppression | **Option A - supprimer** | N'existe plus |
| Q6: Où valider enum ≤127 | **ProtocolValidator** | Centralisation |

---

## 2. Liste exhaustive des modifications

### 2.1 Fichiers à CRÉER

| Fichier | Source | Modifications |
|---------|--------|---------------|
| `generators/sysex/cpp/enum_generator.py` | Copie de serial8 | Aucune |
| `generators/sysex/java/enum_generator.py` | Copie de serial8 | Aucune |

### 2.2 Fichiers à MODIFIER

#### 2.2.1 Configuration Serial8

**Fichier** : `src/protocol_codegen/methods/serial8/config.py`

**Modification** : Ajouter option `encode_message_name`

```python
class Serial8Structure(BaseModel):
    """Message structure offsets for Serial8 protocol."""

    message_type_offset: int = Field(...)
    payload_offset: int = Field(...)

    # AJOUTER :
    encode_message_name: bool = Field(
        default=False,
        description="Encode MESSAGE_NAME string in payload (for bridge logging)",
    )
```

#### 2.2.2 Générateur Serial8 struct (C++)

**Fichier** : `src/protocol_codegen/generators/serial8/cpp/struct_generator.py`

**Modification** : Conditionner l'encodage MESSAGE_NAME sur config

- Passer `encode_message_name: bool` à `generate_struct_hpp()`
- Conditionner le code d'encodage/décodage MESSAGE_NAME
- Ajuster `_calculate_max_payload_size()` et `_calculate_min_payload_size()`

#### 2.2.3 Générateur Serial8 struct (Java)

**Fichier** : `src/protocol_codegen/generators/serial8/java/struct_generator.py`

**Modification** : Idem C++

#### 2.2.4 Orchestrateur Serial8

**Fichier** : `src/protocol_codegen/methods/serial8/generator.py`

**Modification** : Passer `encode_message_name` aux générateurs struct

#### 2.2.5 Exports SysEx

**Fichier** : `src/protocol_codegen/generators/sysex/cpp/__init__.py`

```python
# AJOUTER ligne ~11 :
from .enum_generator import generate_enum_hpp

# AJOUTER dans __all__ :
__all__ = [
    ...
    "generate_enum_hpp",
]
```

**Fichier** : `src/protocol_codegen/generators/sysex/java/__init__.py`

```python
# AJOUTER ligne ~12 :
from .enum_generator import generate_enum_java

# AJOUTER dans __all__ :
__all__ = [
    ...
    "generate_enum_java",
]
```

#### 2.2.6 Struct Generator SysEx (C++)

**Fichier** : `src/protocol_codegen/generators/sysex/cpp/struct_generator.py`

**Modifications** :

1. **Ligne 26** - Ajouter import EnumField :
```python
from protocol_codegen.core.field import CompositeField, EnumField, FieldBase, PrimitiveField
```

2. **Supprimer fromHost** (lignes 199-201) :
```python
# SUPPRIMER ces lignes :
# lines.append("    // Origin tracking (set by DecoderRegistry during decode)")
# lines.append("    bool fromHost = false;")
```

3. **Fonction `_analyze_includes_needed()`** - Ajouter cas EnumField :
```python
def _analyze_includes_needed(...) -> tuple[bool, bool, bool, set[str]]:
    # Ajouter enum_names: set[str] = set()
    # Ajouter cas isinstance(field, EnumField)
```

4. **Fonction `_generate_header()`** - Ajouter includes enum :
```python
# Ajouter génération des #include "../{enum_name}.hpp"
```

5. **Fonction `_generate_encode_function()`** - Ajouter cas EnumField :
```python
# Ajouter elif isinstance(field, EnumField): avant elif isinstance(field, CompositeField)
# Encoder via encodeUint8(ptr, static_cast<uint8_t>(field))
```

6. **Fonction `_generate_decode_function()`** - Ajouter cas EnumField :
```python
# Ajouter elif isinstance(field, EnumField): avant elif isinstance(field, CompositeField)
# Décoder via decodeUint8 + static_cast
```

7. **Fonction `_calculate_max_payload_size()`** - Ajouter cas EnumField :
```python
elif isinstance(field, EnumField):
    array_size = field.array if field.array else 1
    if field.array:
        total_size += 1  # Array count byte
    total_size += 1 * array_size  # 1 byte per enum value
```

8. **Fonction `_calculate_min_payload_size()`** - Ajouter cas EnumField :
```python
elif isinstance(field, EnumField):
    if field.array:
        total_size += 1  # Array count byte only
    else:
        total_size += 1  # 1 byte for enum value
```

9. **Fonction `_get_cpp_type_for_field()`** - Ajouter cas EnumField :
```python
if isinstance(field, EnumField):
    cpp_type = field.enum_def.cpp_type
    if field.array:
        return f"std::array<{cpp_type}, {field.array}>"
    return cpp_type
```

10. **Fonction `_generate_single_composite_struct()`** - Ajouter cas EnumField nested

#### 2.2.7 Struct Generator SysEx (Java)

**Fichier** : `src/protocol_codegen/generators/sysex/java/struct_generator.py`

**Modifications** : Similaires à C++ (adapter syntaxe Java)

#### 2.2.8 Logger Generator SysEx (C++)

**Fichier** : `src/protocol_codegen/generators/sysex/cpp/logger_generator.py`

**Modifications** :

1. **Ligne 27** - Ajouter import EnumField :
```python
from protocol_codegen.core.field import CompositeField, EnumField, FieldBase, PrimitiveField
```

2. **Ajouter fonctions** (copier depuis serial8) :
```python
def _format_enum_scalar(field: EnumField, indent: int, is_last: bool) -> list[str]:
    ...

def _format_enum_array(field: EnumField, indent: int, is_last: bool) -> list[str]:
    ...
```

3. **Modifier `_generate_field_logging()`** - Ajouter cas EnumField

#### 2.2.9 Logger Generator SysEx (Java)

**Fichier** : `src/protocol_codegen/generators/sysex/java/logger_generator.py`

**Modifications** : Similaires à C++

#### 2.2.10 Orchestrateur SysEx

**Fichier** : `src/protocol_codegen/methods/sysex/generator.py`

**Modifications** :

1. **Ajouter imports** (après ligne 64) :
```python
from protocol_codegen.core.enum_def import EnumDef
from protocol_codegen.core.field import EnumField, CompositeField, FieldBase
from protocol_codegen.generators.sysex.cpp.enum_generator import generate_enum_hpp
from protocol_codegen.generators.sysex.java.enum_generator import generate_enum_java
```

2. **Ajouter fonction `_collect_enum_defs()`** (copier depuis serial8) :
```python
def _collect_enum_defs(messages: list[Message]) -> list[EnumDef]:
    """Collect all unique EnumDefs from all messages."""
    enum_defs: dict[str, EnumDef] = {}

    def collect_from_fields(fields: list[FieldBase]) -> None:
        for field in fields:
            if isinstance(field, EnumField):
                if field.enum_def.name not in enum_defs:
                    enum_defs[field.enum_def.name] = field.enum_def
            elif isinstance(field, CompositeField):
                collect_from_fields(field.fields)

    for message in messages:
        collect_from_fields(message.fields)

    return list(enum_defs.values())
```

3. **Dans `_generate_cpp()`** - Ajouter génération enums (après structs) :
```python
# Generate enum files
enum_defs = _collect_enum_defs(messages)
enum_stats = GenerationStats()
for enum_def in enum_defs:
    cpp_enum_path = cpp_base / f"{enum_def.name}.hpp"
    cpp_enum_code = generate_enum_hpp(enum_def, cpp_enum_path)
    was_written = write_if_changed(cpp_enum_path, cpp_enum_code)
    enum_stats.record_write(cpp_enum_path, was_written)

if verbose and enum_defs:
    print(f"  ✓ C++ enum files: {enum_stats.summary()}")
```

4. **Dans `_generate_java()`** - Idem pour Java

#### 2.2.11 Validateur de protocole

**Fichier** : `src/protocol_codegen/core/validator.py`

**Modification** : Ajouter validation enum ≤127 pour SysEx

```python
def validate_messages(
    self,
    messages: list[Message],
    protocol: str = "serial8"  # AJOUTER paramètre
) -> list[str]:
    ...

    # AJOUTER après validation existante :
    if protocol == "sysex":
        errors.extend(self._validate_enum_values_for_sysex(messages))

    return errors

def _validate_enum_values_for_sysex(self, messages: list[Message]) -> list[str]:
    """Validate that all enum values are ≤127 for SysEx 7-bit protocol."""
    errors: list[str] = []

    def check_fields(fields: list[FieldBase], context: str) -> None:
        for field in fields:
            if isinstance(field, EnumField):
                for name, value in field.enum_def.values.items():
                    if value > 127:
                        errors.append(
                            f"{context}: EnumField '{field.name}' has value "
                            f"'{name}={value}' which exceeds SysEx 7-bit limit (127)"
                        )
            elif isinstance(field, CompositeField):
                check_fields(field.fields, f"{context}.{field.name}")

    for message in messages:
        check_fields(message.fields, message.name)

    return errors
```

**Fichier** : `src/protocol_codegen/methods/sysex/generator.py`

**Modification** : Passer `protocol="sysex"` au validateur

```python
# Ligne ~191, modifier :
errors = validator.validate_messages(messages, protocol="sysex")
```

---

## 3. Ordre d'exécution

### Étape 1 : Modifications de config (sans impact)
1. [ ] Modifier `serial8/config.py` - ajouter `encode_message_name`

### Étape 2 : Créer fichiers enum_generator sysex
2. [ ] Copier `serial8/cpp/enum_generator.py` → `sysex/cpp/enum_generator.py`
3. [ ] Copier `serial8/java/enum_generator.py` → `sysex/java/enum_generator.py`
4. [ ] Modifier `sysex/cpp/__init__.py` - ajouter export
5. [ ] Modifier `sysex/java/__init__.py` - ajouter export

### Étape 3 : Modifier struct_generators sysex
6. [ ] Modifier `sysex/cpp/struct_generator.py` - support EnumField + supprimer fromHost
7. [ ] Modifier `sysex/java/struct_generator.py` - support EnumField

### Étape 4 : Modifier logger_generators sysex
8. [ ] Modifier `sysex/cpp/logger_generator.py` - support EnumField
9. [ ] Modifier `sysex/java/logger_generator.py` - support EnumField

### Étape 5 : Modifier orchestrateur sysex
10. [ ] Modifier `methods/sysex/generator.py` - collect + generate enums

### Étape 6 : Ajouter validation sysex
11. [ ] Modifier `core/validator.py` - validation enum ≤127
12. [ ] Modifier `methods/sysex/generator.py` - passer protocol="sysex"

### Étape 7 : Rendre MESSAGE_NAME optionnel dans serial8
13. [ ] Modifier `serial8/cpp/struct_generator.py` - conditionner MESSAGE_NAME
14. [ ] Modifier `serial8/java/struct_generator.py` - conditionner MESSAGE_NAME
15. [ ] Modifier `methods/serial8/generator.py` - passer encode_message_name

### Étape 8 : Tests
16. [ ] Tester génération sysex avec EnumField
17. [ ] Tester génération serial8 avec encode_message_name=false
18. [ ] Tester génération serial8 avec encode_message_name=true
19. [ ] Vérifier que plugin-bitwig génère correctement

---

## 4. Fichiers impactés (récapitulatif)

| Fichier | Action | Risque |
|---------|--------|--------|
| `methods/serial8/config.py` | Modifier | Faible |
| `generators/sysex/cpp/enum_generator.py` | Créer | Aucun |
| `generators/sysex/java/enum_generator.py` | Créer | Aucun |
| `generators/sysex/cpp/__init__.py` | Modifier | Faible |
| `generators/sysex/java/__init__.py` | Modifier | Faible |
| `generators/sysex/cpp/struct_generator.py` | Modifier | Moyen |
| `generators/sysex/java/struct_generator.py` | Modifier | Moyen |
| `generators/sysex/cpp/logger_generator.py` | Modifier | Moyen |
| `generators/sysex/java/logger_generator.py` | Modifier | Moyen |
| `methods/sysex/generator.py` | Modifier | Moyen |
| `core/validator.py` | Modifier | Faible |
| `generators/serial8/cpp/struct_generator.py` | Modifier | Moyen |
| `generators/serial8/java/struct_generator.py` | Modifier | Moyen |
| `methods/serial8/generator.py` | Modifier | Faible |

**Total** : 14 fichiers (2 créations, 12 modifications)

---

## 5. Critères de validation

- [ ] `ruff check src/` : 0 erreur
- [ ] `pyright src/` : 0 erreur
- [ ] `pytest` : tous les tests passent
- [ ] Génération SysEx avec EnumField : pas d'erreur
- [ ] Génération SysEx avec enum value >127 : erreur de validation
- [ ] Code C++ sysex généré : compile
- [ ] Code Java sysex généré : compile
- [ ] Génération Serial8 avec `encode_message_name=false` : MESSAGE_NAME absent du payload
- [ ] Génération Serial8 avec `encode_message_name=true` : MESSAGE_NAME présent dans payload
- [ ] plugin-bitwig : génère et compile correctement

---

## 6. Risques et mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Régression sysex existant | Moyenne | Élevé | Tester sur projet consommateur |
| Oubli d'un cas EnumField | Moyenne | Élevé | Diff systématique serial8↔sysex |
| Breaking change MESSAGE_NAME | Faible | Moyen | Default=false préserve comportement |
| Validation trop stricte | Faible | Faible | Erreur claire avec contexte |

---

## 7. Estimation

| Tâche | Temps estimé |
|-------|--------------|
| Étapes 1-2 (config + enum_generator) | 15 min |
| Étapes 3-4 (struct + logger sysex) | 45 min |
| Étape 5 (orchestrateur sysex) | 15 min |
| Étape 6 (validation) | 15 min |
| Étape 7 (MESSAGE_NAME optionnel) | 30 min |
| Étape 8 (tests) | 30 min |
| **Total** | **~2h30** |
