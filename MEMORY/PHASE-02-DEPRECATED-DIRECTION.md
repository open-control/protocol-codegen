# Phase 2 : Support deprecated et method_generator dans SysEx

**Date de création** : 2025-12-31
**Dernière mise à jour** : 2025-12-31
**Statut** : ✅ Terminé (2025-12-31)
**Priorité** : MOYENNE
**Dépendances** : Phase 1 (EnumField requis pour method_generator)

---

## 1. Résumé des décisions validées

| Question | Décision | Justification |
|----------|----------|---------------|
| Q1: Copier ou factoriser method_generator | **Copier** | Stabiliser d'abord, factoriser en phase ultérieure |
| Q2: Implémenter filtrage deprecated | **Oui, maintenant** | Cohérence avec serial8 |
| Q3: Priorité | **Phase séparée après Phase 1** | Dépend de EnumField |

---

## 2. Contexte

Les messages SysEx de plugin-bitwig utilisent `direction` et `intent` :
```python
TRANSPORT_PLAY = Message(
    direction=Direction.TO_HOST,
    intent=Intent.COMMAND,
    ...
)
```

Le method_generator est donc pertinent pour générer des méthodes explicites.

---

## 3. Liste exhaustive des modifications

### 3.1 Fichiers à CRÉER

| Fichier | Source | Modifications |
|---------|--------|---------------|
| `generators/sysex/cpp/method_generator.py` | Copie de serial8 | Aucune |
| `generators/sysex/java/method_generator.py` | Copie de serial8 | Aucune |

### 3.2 Fichiers à MODIFIER

#### 3.2.1 Exports SysEx

**Fichier** : `src/protocol_codegen/generators/sysex/cpp/__init__.py`

```python
# AJOUTER :
from .method_generator import generate_protocol_methods_hpp

# AJOUTER dans __all__ :
"generate_protocol_methods_hpp",
```

**Fichier** : `src/protocol_codegen/generators/sysex/java/__init__.py`

```python
# AJOUTER :
from .method_generator import generate_protocol_methods_java

# AJOUTER dans __all__ :
"generate_protocol_methods_java",
```

#### 3.2.2 Orchestrateur SysEx

**Fichier** : `src/protocol_codegen/methods/sysex/generator.py`

**Modification 1** : Ajouter imports method_generator

```python
# Après les autres imports de generators (ligne ~46) :
from protocol_codegen.generators.sysex.cpp.method_generator import generate_protocol_methods_hpp
from protocol_codegen.generators.sysex.java.method_generator import generate_protocol_methods_java
```

**Modification 2** : Ajouter filtrage deprecated (après import messages, ~ligne 182)

```python
# AVANT (ligne ~182) :
messages: list[Message] = message_module.ALL_MESSAGES

# APRÈS :
all_messages: list[Message] = message_module.ALL_MESSAGES
deprecated_count = sum(1 for m in all_messages if m.deprecated)
messages = [m for m in all_messages if not m.deprecated]
if deprecated_count > 0:
    log(
        f"  ✓ Imported {len(all_messages)} messages ({deprecated_count} deprecated, {len(messages)} active)"
    )
else:
    log(f"  ✓ Imported {len(messages)} messages")
```

**Modification 3** : Ajouter génération ProtocolMethods C++ (dans `_generate_cpp()`, après structs)

```python
# Filtrer les messages legacy pour les méthodes
new_style_messages = [m for m in messages if not m.is_legacy()]

# Generate ProtocolMethods.inl
if new_style_messages:
    cpp_methods_path = cpp_base / "ProtocolMethods.inl"
    cpp_methods_code = generate_protocol_methods_hpp(new_style_messages, cpp_methods_path)
    was_written = write_if_changed(cpp_methods_path, cpp_methods_code)
    stats.record_write(cpp_methods_path, was_written)

    if verbose:
        print(f"  ✓ C++ ProtocolMethods.inl: {'written' if was_written else 'unchanged'}")
```

**Modification 4** : Ajouter génération ProtocolMethods Java (dans `_generate_java()`, après structs)

```python
# Filtrer les messages legacy pour les méthodes
new_style_messages = [m for m in messages if not m.is_legacy()]

# Generate ProtocolMethods.java
if new_style_messages:
    java_methods_path = java_base / "ProtocolMethods.java"
    java_methods_code = generate_protocol_methods_java(
        new_style_messages, java_methods_path, java_package, registry
    )
    was_written = write_if_changed(java_methods_path, java_methods_code)
    stats.record_write(java_methods_path, was_written)

    if verbose:
        print(f"  ✓ Java ProtocolMethods.java: {'written' if was_written else 'unchanged'}")
```

---

## 4. Ordre d'exécution

### Étape 1 : Créer method_generators sysex
1. [ ] Copier `serial8/cpp/method_generator.py` → `sysex/cpp/method_generator.py`
2. [ ] Copier `serial8/java/method_generator.py` → `sysex/java/method_generator.py`
3. [ ] Modifier `sysex/cpp/__init__.py` - ajouter export
4. [ ] Modifier `sysex/java/__init__.py` - ajouter export

### Étape 2 : Modifier orchestrateur sysex
5. [ ] Ajouter imports method_generator dans `methods/sysex/generator.py`
6. [ ] Ajouter filtrage deprecated dans `methods/sysex/generator.py`
7. [ ] Ajouter génération ProtocolMethods C++ dans `_generate_cpp()`
8. [ ] Ajouter génération ProtocolMethods Java dans `_generate_java()`

### Étape 3 : Tests
9. [ ] Tester génération sysex avec messages deprecated
10. [ ] Vérifier ProtocolMethods.inl généré
11. [ ] Vérifier ProtocolMethods.java généré
12. [ ] Tester sur plugin-bitwig

---

## 5. Fichiers impactés (récapitulatif)

| Fichier | Action | Risque |
|---------|--------|--------|
| `generators/sysex/cpp/method_generator.py` | Créer | Aucun |
| `generators/sysex/java/method_generator.py` | Créer | Aucun |
| `generators/sysex/cpp/__init__.py` | Modifier | Faible |
| `generators/sysex/java/__init__.py` | Modifier | Faible |
| `methods/sysex/generator.py` | Modifier | Moyen |

**Total** : 5 fichiers (2 créations, 3 modifications)

---

## 6. Critères de validation

- [ ] `ruff check src/` : 0 erreur
- [ ] `pyright src/` : 0 erreur
- [ ] `pytest` : tous les tests passent
- [ ] Messages deprecated exclus de la génération sysex
- [ ] `ProtocolMethods.inl` généré avec méthodes TO_HOST
- [ ] `ProtocolMethods.java` généré avec callbacks et méthodes
- [ ] plugin-bitwig : génère correctement avec les nouvelles méthodes

---

## 7. Risques et mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Régression API existante | Faible | Moyen | Fichiers additifs, pas de modification |
| Messages legacy mal filtrés | Faible | Faible | Test sur plugin-bitwig |

---

## 8. Estimation

| Tâche | Temps estimé |
|-------|--------------|
| Copier method_generators | 5 min |
| Modifier __init__.py | 5 min |
| Modifier orchestrateur sysex | 20 min |
| Tests | 15 min |
| **Total** | **~45 min** |

---

## 9. Dépendances

```
Phase 1 (EnumField)
    │
    └──► Phase 2 (method_generator)
         - method_generator importe EnumField
         - method_generator utilise enum pour générer les types corrects
```

**Important** : Phase 2 ne peut être exécutée qu'après Phase 1 complétée.
