# Instructions d'Implémentation - Protocol-Codegen

> **LECTURE OBLIGATOIRE** en début de chaque session et après chaque auto-compact.
> Lire également TOUS les fichiers `./docs/**/*.md` avant toute action.

---

## Règles d'Implémentation

### 1. Autonomie Totale
- Exécuter le plan phase par phase sans demander confirmation
- Résoudre les problèmes rencontrés de manière autonome

### 2. Commit Systématique
- **1 commit par étape/sous-étape** terminée
- Jamais de travail non commité entre les étapes

### 3. Synchronisation Plan ↔ Code
- **Mettre à jour le plan** (`MIGRATION_PLAN_MIXIN_ARCHITECTURE.md`) après chaque étape
- Marquer `[x]` les étapes complétées dans le document
- Le plan reflète TOUJOURS l'état réel du code

### 4. Persistance Auto-Compact
- Ces instructions doivent être **relues en début de session** ou après auto-compact
- Continuer le travail là où il s'est arrêté

### 5. Résolution Racine Obligatoire
- À chaque étape testable: **résoudre TOUS les problèmes à la racine**
- **Zéro fix rapide** - comprendre et corriger la cause
- Respecter la feuille de route **à la lettre**

### 6. Audit Avant Modification
- **TOUJOURS auditer l'état actuel** avant d'entamer de nouvelles modifications
- Vérifier que les étapes marquées "complétées" le sont **réellement dans le code**
- Confirmer la progression avant de continuer

---

## Procédure de Début de Session

```
1. Lire ./docs/INSTRUCTIONS.md (ce fichier)
2. Lire ./docs/MIGRATION_PLAN_MIXIN_ARCHITECTURE.md
3. Lire tous les autres ./docs/**/*.md
4. Auditer l'état du code vs le plan
5. Identifier la prochaine étape à exécuter
6. Continuer l'implémentation
```

---

## Fichiers de Référence

| Fichier | Contenu |
|---------|---------|
| `docs/INSTRUCTIONS.md` | Ce fichier - règles d'implémentation |
| `docs/MIGRATION_PLAN_MIXIN_ARCHITECTURE.md` | Plan détaillé avec progression |

---

## Commandes de Validation

```bash
# Tests unitaires
cd open-control/protocol-codegen
.venv/Scripts/python.exe -m pytest -v --tb=short

# Linting
python -m ruff check src/ tests/

# Génération end-to-end
cd ../../midi-studio/plugin-bitwig
./script/protocol/generate_protocol.sh
```

---

**Ne jamais ignorer ces instructions.**
