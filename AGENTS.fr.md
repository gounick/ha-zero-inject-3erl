# AGENTS.md

Ce fichier guide les outils agentiques compatibles lorsqu’ils génèrent ou relisent du code dans ce dépôt.

**Remarque :** ce fichier est destiné aux assistants IA. Les développeurs humains doivent consulter le guide de contribution du projet.

---

## Important : commencer ici

1. **Lisez d’abord ce fichier** — ne travaillez pas de mémoire ou sur des suppositions.
2. **Parcourez le code existant** — identifiez les utilitaires, helpers et motifs disponibles.
3. **Respectez les principes ci-dessous** — ils sont non négociables.
4. **Auto-vérifiez avant de répondre** — utilisez la liste en bas du fichier.

---

## Principes essentiels

### Utiliser l’anglais partout

- Utilisez toujours l’anglais pour le code, les commentaires, la documentation et les messages visibles.
- L’anglais est la langue principale de la documentation. Lors de l’ajout ou de la modification d’un fichier Markdown, créez ou mettez à jour sa version secondaire française `<name>.fr.md` à côté.
- Gardez les fichiers Markdown français synchronisés avec leur source anglaise et préférez les liens vers les fichiers `.fr.md` correspondants depuis les pages françaises.
- Aucune autre langue, sauf dans le fichier de traduction (`translations/fr.json`) et les fichiers documentaires secondaires `*.fr.md`.

### DRY — Ne pas se répéter

- Ne dupliquez jamais la logique. Réutilisez ou étendez les fonctions existantes avant d’en créer.
- Extrayez une aide commune quand le même motif apparaît deux fois.
- Exemples de concepts partagés :
  - Décision de bridage : `ThreeERLUpdateCoordinator.curtailment_requested`, construit sur `helpers.is_bridage_active`.
  - Résolution du mode : `helpers.get_mode_entity_id` et `helpers.get_current_mode`.
  - Paramètres actifs : `helpers.entry_settings` — les options remplacent les données après sauvegarde.
  - Informations d’appareil : `helpers.build_device_info`.

### KISS — Rester simple

- Préférez la solution lisible la plus simple.
- Évitez les abstractions prématurées.

### Pas de code mort

- Supprimez le code jamais exécuté : fonctions inutilisées, branches inaccessibles, constantes obsolètes, imports orphelins et blocs commentés.
- Lors d’un remplacement de comportement, supprimez l’ancienne implémentation dans le même changement.
- Ne conservez pas de shim de compatibilité, alias ou entités dépréciées sauf si une migration documentée l’exige ; le projet est en développement et les ruptures annoncées dans `CHANGELOG.md` sont acceptables.
- Une entité, option ou action sans usage visible doit être supprimée avec ses traductions, tests et références.
- En cas de doute, vérifiez par une recherche globale avant de supprimer.

### Images de marque

- Les images de marque vivent dans `custom_components/zero_inject_3erl/brand/` et sont servies localement via `/api/brands/integration/{domain}/{image}` depuis Home Assistant 2026.3.
- N’ouvrez **pas** de pull request sur `home-assistant/brands` : les soumissions pour intégrations custom n’y sont plus acceptées.
- Fichiers pris en charge : `icon.png`, `dark_icon.png`, `logo.png`, `dark_logo.png` et leurs variantes `@2x`. Les icônes sont des PNG carrés ; le set actuel fait 256×256 avec `@2x` en 512×512, en RGBA.
- `custom_components/zero_inject_3erl/brand/` est la source de vérité unique des visuels ; ne dupliquez pas les images ailleurs dans le dépôt.

### Documentation et changelog

- Mettez à jour `README.md` pour tout changement visible par l’utilisateur.
- Mettez à jour `docs/*.md` et `WORKFLOW.md` pour les changements de câblage, configuration Envoy, exemples ou architecture.
- Ajoutez une entrée à `CHANGELOG.md` pour chaque changement fonctionnel ou architectural.

---

## Avant d’écrire du code

1. Examinez les utilitaires sous `custom_components/zero_inject_3erl/`.
2. Recherchez des motifs similaires dans les autres intégrations du dépôt.
3. Réutilisez avant de créer.
4. Pour ajouter un adaptateur de système PV, lisez d’abord les notes d’extensibilité.

---

## Style de code

- Fonctions courtes et ciblées, idéalement moins de 20–30 lignes.
- Noms explicites et descriptifs.
- Pas de code mort, blocs commentés ni espaces en fin de ligne.
- Docstrings au format Sphinx (`:param name:`, `:type name:`, `:return:`, `:rtype:`).
- Ne jamais journaliser de secrets ou identifiants.
- Toujours utiliser la syntaxe d’exceptions Python 3.

---

## Architecture du projet

```text
custom_components/zero_inject_3erl/
├── __init__.py       # Cycle de vie HA et câblage runtime
├── manifest.json     # Métadonnées de l’intégration
├── const.py          # Constantes, clés de configuration, défauts
├── config_flow.py    # Flux de configuration UI + options
├── api.py            # Client REST de l’API 3ERL
├── coordinator.py    # Coordinators API et prix
├── pricing.py        # Récupération RTE PRE+ et Enedis PRD3
├── helpers.py        # Aides communes de décision et d’entités
├── controller.py     # Logique de pilotage relais Auto / On / Off
├── sensor.py         # Sensors API et calculés
├── binary_sensor.py  # Demande ACI/ACC, commande, fraîcheur, supervision
├── supervision.py    # Diagnostics relais et export réseau
├── select.py         # Sélecteur de mode
├── switch.py         # Bypass manuel persistant
├── visibility.py     # Visibilité ACI/ACC avec choix utilisateur
├── services.yaml     # Définitions de services
└── translations/     # Traductions UI
```

- `ThreeERLApiClient` possède tous les appels HTTP vers `https://3erl.fr/api.json`.
- `ThreeERLUpdateCoordinator` interroge l’API ; `ThreeERLPricingCoordinator` rafraîchit les prix indépendamment.
- `ZeroInjectController` écoute le coordinator, le mode et les relais, puis aligne les relais sur l’état calculé.
- La plateforme select est configurée avant les autres pour résoudre son entity id.
- Les tests sont dans `tests/` ; `tests/conftest.py` fournit `config_entry` et `mock_fetch`.
- `sensor.py` et `binary_sensor.py` ne doivent pas appeler l’API directement ; ils lisent `coordinator.data`.

### Extensibilité pour d’autres systèmes PV

L’intégration pilote actuellement des switchs relais configurés par l’utilisateur. Les futurs providers — Enphase auto-détection, SMA, Fronius, etc. — doivent être placés sous `custom_components/zero_inject_3erl/providers/` et exposer :

- `is_supported(hass, entry)` — détecte si le provider s’applique ;
- `async_get_relay_entities(hass, entry)` — retourne les entity IDs des relais à piloter ;
- `async_get_export_entity(hass, entry)` — retourne éventuellement un capteur d’export positif à observer.

Les coordinators et le contrôleur restent indépendants du provider.

---

## Tests et qualité

- Exécutez `python3 -m py_compile <file>` pour chaque fichier Python modifié.
- Si `prek` ou `pre-commit` est configuré, exécutez `prek run --all-files`.
- Ajoutez ou mettez à jour les tests pour tout changement de logique ou fonctionnalité.

### Environnement de développement avec uv

```bash
uv sync --extra test
uv run pytest tests/ -v
prek run --all-files
uv run python3 -m py_compile <modified_files>
```

---

## Auto-vérification avant soumission

```text
□ Existe-t-il déjà une fonction pour cette logique ?
□ Est-ce que je duplique du code existant ?
□ Est-ce la solution la plus simple qui fonctionne ?
□ Ai-je supprimé le code inutilisé et les espaces finaux ?
□ Aucun secret ni identifiant n’est journalisé ou codé en dur ?
□ Ai-je mis à jour README.md, docs/*.md, WORKFLOW.md et CHANGELOG.md ?
□ Ai-je ajouté ou mis à jour les tests de la logique modifiée ?
```

Si une réponse est **non**, corrigez avant de soumettre.
