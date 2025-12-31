# Phase 2B : Correction des Asymétries Serial8 ↔ SysEx

**Date de création** : 2025-12-31
**Dernière mise à jour** : 2025-12-31
**Statut** : 🟢 Plan validé
**Priorité** : HAUTE (bloquant pour Phase 3)
**Dépendances** : Phase 2 complétée

---

## 1. Contexte

L'analyse de symétrie a révélé des différences problématiques entre Serial8 et SysEx qui empêchent de switcher facilement entre les protocoles.

### 1.1 Différences INTENTIONNELLES (à conserver)

| Feature | Serial8 | SysEx | Raison |
|---------|---------|-------|--------|
| MESSAGE_NAME dans payload | ✅ Oui | ❌ Non | Bridge logging (Serial8 only) |
| Encoding description | "8-bit binary" | "7-bit MIDI-safe" | Protocole différent |
| Validation enum ≤127 | Non | Oui | Contrainte 7-bit SysEx |

### 1.2 Asymétries PROBLÉMATIQUES (à corriger)

| Problème | Serial8 (référence) | SysEx (à corriger) |
|----------|---------------------|-------------------|
| fromHost field | ❌ Supprimé | ⚠️ Encore présent |
| Arrays Java primitifs | `T[]` natifs | `List<T>` |
| Arrays Java composites | `T[]` natifs | `List<T>` |
| count prefix C++ arrays | Toujours encodé | Seulement si `dynamic` |

---

## 2. Modifications détaillées

### 2.1 Supprimer fromHost de SysEx C++

**Fichier** : `generators/sysex/cpp/struct_generator.py`

**Lignes 211-215** - SUPPRIMER :
```python
    # Add fromHost field LAST (injected by DecoderRegistry after construction)
    lines.append("    // Origin tracking (set by DecoderRegistry during decode)")
    lines.append("    bool fromHost = false;")

    lines.append("")
```

**Résultat attendu** (comme Serial8 lignes 204-209) :
```python
    # Add fields FIRST (use new helper that handles both primitive and composite)
    for field in fields:
        cpp_type = _get_cpp_type_for_field(field, type_registry)
        lines.append(f"    {cpp_type} {field.name};")

    lines.append("")
    return "\n".join(lines)
```

---

### 2.2 Supprimer fromHost de SysEx Java

**Fichier** : `generators/sysex/java/struct_generator.py`

**Ligne 16** - SUPPRIMER de la docstring :
```python
- fromHost field for origin tracking (SysEx-specific)
```

**Lignes 207-210** - SUPPRIMER dans `_generate_field_declarations()` :
```python
    # Add fromHost field (injected by DecoderRegistry, ignored during encode)
    lines.append("    // Origin tracking (set by DecoderRegistry during decode)")
    lines.append("    public boolean fromHost = false;")
    lines.append("")
```

---

### 2.3 Unifier Arrays Java : List<T> → T[]

**Fichier** : `generators/sysex/java/struct_generator.py`

#### 2.3.1 Dans `_generate_field_declarations()` (lignes 223-232)

**Avant** :
```python
        elif isinstance(field, PrimitiveField):
            ...
            if field.is_array():
                boxed_type = _get_boxed_java_type(java_type)
                lines.append(f"    private final List<{boxed_type}> {field.name};")
        elif isinstance(field, CompositeField):
            ...
            if field.array:
                lines.append(f"    private final List<{class_name}> {field.name};")
```

**Après** (comme Serial8) :
```python
        elif isinstance(field, PrimitiveField):
            ...
            if field.is_array():
                # Primitive arrays use T[] (no boxing, zero-allocation)
                lines.append(f"    private final {java_type}[] {field.name};")
        elif isinstance(field, CompositeField):
            ...
            if field.array:
                # Composite arrays use T[] (aligned with C++ std::array)
                lines.append(f"    private final {class_name}[] {field.name};")
```

#### 2.3.2 Dans `_generate_constructor()` (lignes 274-282)

**Avant** :
```python
        elif isinstance(field, PrimitiveField):
            ...
            if field.is_array():
                boxed_type = _get_boxed_java_type(java_type)
                params.append(f"List<{boxed_type}> {field.name}")
        elif isinstance(field, CompositeField):
            ...
            if field.array:
                params.append(f"List<{class_name}> {field.name}")
```

**Après** (comme Serial8) :
```python
        elif isinstance(field, PrimitiveField):
            ...
            if field.is_array():
                # Primitive arrays use T[] (no boxing)
                params.append(f"{java_type}[] {field.name}")
        elif isinstance(field, CompositeField):
            ...
            if field.array:
                # Composite arrays use T[] (aligned with C++ std::array)
                params.append(f"{class_name}[] {field.name}")
```

#### 2.3.3 Dans `_generate_getters()` (lignes ~317-325)

**Avant** :
```python
        elif isinstance(field, PrimitiveField):
            ...
            if field.is_array():
                boxed_type = _get_boxed_java_type(java_type)
                java_type = f"List<{boxed_type}>"
        elif isinstance(field, CompositeField):
            java_type = f"List<{class_name}>" if field.array else class_name
```

**Après** (comme Serial8) :
```python
        elif isinstance(field, PrimitiveField):
            ...
            if field.is_array():
                # Primitive arrays use T[] (no boxing)
                java_type = f"{java_type}[]"
        elif isinstance(field, CompositeField):
            # Composite arrays use T[] (aligned with C++ std::array)
            java_type = f"{class_name}[]" if field.array else class_name
```

#### 2.3.4 Dans `_generate_encode_method()` (lignes ~414-432)

**Avant** :
```python
                lines.append(
                    f"        offset += Encoder.writeUint8(buffer, offset, {field.name}.size());"
                )
```

**Après** (comme Serial8) :
```python
                lines.append(
                    f"        offset += Encoder.writeUint8(buffer, offset, {field.name}.length);"
                )
```

Également dans les boucles composites :
```python
# Avant
f"        offset += Encoder.writeUint8(buffer, offset, {field.name}.size());"

# Après
f"        offset += Encoder.writeUint8(buffer, offset, {field.name}.length);"
```

#### 2.3.5 Dans `_generate_decode_method()`

Vérifier que le décodage utilise aussi `T[]` au lieu de `List<T>`.

---

### 2.4 Unifier count prefix C++ : toujours encoder

**Fichier** : `generators/sysex/cpp/struct_generator.py`

**Lignes 288-296** dans `_generate_encode_function()` :

**Avant** :
```python
            if field.is_array():
                # Primitive array (e.g., string[16])
                # Only encode count prefix for dynamic arrays
                if field.dynamic:
                    lines.append(f"        encodeUint8(ptr, {field.name}.size());")
                lines.append(f"        for (const auto& item : {field.name}) {{")
```

**Après** (comme Serial8) :
```python
            if field.is_array():
                # Primitive array (e.g., string[16])
                # ALWAYS encode count prefix (same as composite arrays for consistency)
                lines.append(f"        encodeUint8(ptr, {field.name}.size());")
                lines.append(f"        for (const auto& item : {field.name}) {{")
```

---

### 2.5 Corriger les __init__.py

**Fichier** : `generators/serial8/cpp/__init__.py`

Ajouter les exports manquants :
```python
from .logger_generator import generate_logger_hpp
from .method_generator import generate_protocol_methods_hpp
from .protocol_generator import generate_protocol_template_hpp

__all__ = [
    ...
    "generate_logger_hpp",
    "generate_protocol_methods_hpp",
    "generate_protocol_template_hpp",
]
```

**Fichier** : `generators/serial8/java/__init__.py`

Ajouter les exports manquants :
```python
from .logger_generator import generate_logger_java
from .method_generator import generate_protocol_methods_java
from .protocol_generator import generate_protocol_template_java

__all__ = [
    ...
    "generate_logger_java",
    "generate_protocol_methods_java",
    "generate_protocol_template_java",
]
```

---

## 3. Ordre d'exécution

| # | Tâche | Fichier | Risque |
|---|-------|---------|--------|
| 1 | Supprimer fromHost C++ | sysex/cpp/struct_generator.py | Faible |
| 2 | Supprimer fromHost Java | sysex/java/struct_generator.py | Faible |
| 3 | Unifier arrays Java declarations | sysex/java/struct_generator.py | Moyen |
| 4 | Unifier arrays Java constructor | sysex/java/struct_generator.py | Moyen |
| 5 | Unifier arrays Java getters | sysex/java/struct_generator.py | Moyen |
| 6 | Unifier arrays Java encode | sysex/java/struct_generator.py | Moyen |
| 7 | Unifier arrays Java decode | sysex/java/struct_generator.py | Moyen |
| 8 | Unifier count prefix C++ | sysex/cpp/struct_generator.py | Faible |
| 9 | Corriger __init__.py serial8/cpp | serial8/cpp/__init__.py | Faible |
| 10 | Corriger __init__.py serial8/java | serial8/java/__init__.py | Faible |
| 11 | Lancer pytest | - | - |
| 12 | Tester génération plugin-bitwig | - | - |

---

## 4. Critères de validation

- [ ] `ruff check src/` : 0 erreur
- [ ] `pyright src/` : 0 erreur
- [ ] `pytest` : tous les tests passent (197 tests)
- [ ] Code SysEx généré n'a plus de `fromHost`
- [ ] Arrays Java SysEx utilisent `T[]` (pas `List<T>`)
- [ ] Count prefix C++ toujours encodé (même pour arrays fixes)
- [ ] __init__.py exports symétriques entre Serial8 et SysEx
- [ ] Génération plugin-bitwig fonctionne

---

## 5. Fichiers impactés

| Fichier | Action | Lignes modifiées |
|---------|--------|------------------|
| `sysex/cpp/struct_generator.py` | Modifier | ~10 lignes |
| `sysex/java/struct_generator.py` | Modifier | ~30 lignes |
| `serial8/cpp/__init__.py` | Modifier | ~6 lignes |
| `serial8/java/__init__.py` | Modifier | ~6 lignes |

**Total** : 4 fichiers, ~52 lignes modifiées

---

## 6. Risques et mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Régression SysEx | Moyenne | Élevé | Tests pytest + plugin-bitwig |
| Breaking change API Java | Moyenne | Moyen | Pas de consommateurs actuels |
| Format wire incompatible | Faible | Élevé | Tests de compilation Phase 3 |

---

## 7. Notes de révision

_Cette phase doit être complétée AVANT Phase 3 (tests de compilation)._
