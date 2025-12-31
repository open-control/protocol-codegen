# SUIVI GLOBAL - Synchronisation Serial8/SysEx + Tests Compilation

**Date de création** : 2025-12-31
**Dernière mise à jour** : 2025-12-31
**Statut** : 🔵 Phase 2 terminée, prêt pour Phase 3

---

## Vue d'ensemble

Ce fichier est le point d'entrée principal pour le suivi de la migration.
Il référence tous les plans détaillés et trace les déviations.

---

## Phases du projet

| Phase | Titre | Statut | Fichiers | Effort | Dépendances |
|-------|-------|--------|----------|--------|-------------|
| 1 | Support EnumField + fromHost + MESSAGE_NAME | ✅ Terminé | 14 (2 créations, 12 modifs) | ~2h30 | Aucune |
| 2 | Support deprecated + method_generator | ✅ Terminé | 5 (2 créations, 3 modifs) | ~45min | Phase 1 |
| 3 | Tests de compilation + CI/CD | 🟢 Plan validé | ~15 fichiers | ~2h20 | Phase 1, Phase 2 |

**Effort total estimé** : ~5h35

### Détail des plans

- [PHASE-01-ENUMFIELD.md](./PHASE-01-ENUMFIELD.md) - EnumField, fromHost, MESSAGE_NAME optionnel
- [PHASE-02-DEPRECATED-DIRECTION.md](./PHASE-02-DEPRECATED-DIRECTION.md) - Filtrage deprecated, method_generator
- [PHASE-03-TESTS-COMPILATION.md](./PHASE-03-TESTS-COMPILATION.md) - PlatformIO native, GitHub Actions, couverture 100%

---

## Légende des statuts

- 🔴 À planifier
- 🟡 En cours de planification
- 🟢 Plan validé
- 🔵 En cours d'implémentation
- ✅ Terminé

---

## Décisions clés validées

| # | Décision | Phase | Impact |
|---|----------|-------|--------|
| D1 | Copier (pas factoriser) enum_generator et method_generator | 1, 2 | Factorisation en phase future |
| D2 | Validation stricte enum ≤127 pour SysEx | 1 | Erreur si valeur >127 |
| D3 | Supprimer fromHost des structs sysex | 1 | Alignement sur serial8 |
| D4 | MESSAGE_NAME optionnel, default=false | 1 | Bitwig override à true |
| D5 | Implémenter filtrage deprecated maintenant | 2 | Cohérence serial8/sysex |
| D6 | PlatformIO native C++17 pour tests | 3 | Portable, déjà installé |
| D7 | GitHub Actions immédiatement | 3 | Protection automatique PR |
| D8 | Couverture 100% des chemins de génération | 3 | ~30 messages de test |

---

## Ordre d'exécution global

```
┌─────────────────────────────────────────────────────────────┐
│                        PHASE 1                               │
│              EnumField + fromHost + MESSAGE_NAME             │
│                      (~2h30)                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        PHASE 2                               │
│              deprecated + method_generator                   │
│                      (~45min)                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        PHASE 3                               │
│              Tests compilation + CI/CD                       │
│                      (~2h20)                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Journal des décisions

| Date | Décision | Impact | Phases impactées |
|------|----------|--------|------------------|
| 2025-12-31 | Copier enum/method_generator au lieu de factoriser | Duplication temporaire acceptable | 1, 2 |
| 2025-12-31 | Validation enum ≤127 stricte (erreur) | Sécurité protocole 7-bit | 1 |
| 2025-12-31 | fromHost supprimé de sysex | Alignement serial8 | 1 |
| 2025-12-31 | MESSAGE_NAME default=false | Rétrocompatibilité | 1 |
| 2025-12-31 | GitHub Actions immédiat | Protection PR automatique | 3 |

---

## Journal des déviations

| Date | Déviation | Cause | Action corrective | Phases impactées |
|------|-----------|-------|-------------------|------------------|
| _Aucune pour l'instant_ | | | | |

---

## Dépendances entre phases

```
Phase 1 (EnumField)
    │
    ├──► Phase 2 (method_generator utilise EnumField)
    │
    └──► Phase 3 (Tests nécessitent EnumField pour couverture 100%)

Phase 2 (deprecated)
    │
    └──► Phase 3 (Tests vérifient exclusion messages deprecated)
```

---

## Risques globaux

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Régression sysex existant | Moyenne | Élevé | Tests sur plugin-bitwig |
| Oubli de cas EnumField | Moyenne | Élevé | Diff systématique serial8↔sysex |
| CI/CD trop lent | Faible | Faible | Matrices parallèles |
| Breaking change pour consommateurs | Faible | Moyen | Default=false pour MESSAGE_NAME |

---

## Checklist pré-implémentation

- [x] Phase 1 : Plan détaillé rédigé
- [x] Phase 1 : Décisions validées
- [x] Phase 2 : Plan détaillé rédigé
- [x] Phase 2 : Décisions validées
- [x] Phase 3 : Plan détaillé rédigé
- [x] Phase 3 : Décisions validées
- [x] Créer branche `feature/sync-sysex-serial8`
- [x] Implémenter Phase 1
- [x] Tests Phase 1 passent (197 tests)
- [x] Implémenter Phase 2
- [x] Tests Phase 2 passent (197 tests + validation plugin-bitwig)
- [ ] Implémenter Phase 3
- [ ] CI/CD fonctionne
- [ ] PR review + merge

---

## Notes de révision

_Section réservée pour noter les ajustements majeurs au plan global lors de l'implémentation_

### Révision 1 (si nécessaire)
- Date :
- Changement :
- Raison :
- Impact :
