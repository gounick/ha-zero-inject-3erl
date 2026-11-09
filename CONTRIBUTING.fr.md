# Contribuer

Les contributions sont les bienvenues — adaptateurs de systèmes PV, intégrations liées à 3ERL, tests et documentation.

## Avant d’ouvrir une pull request

- Ouvrez d’abord un ticket pour discuter du changement, sauf correction triviale.
- Gardez les pull requests ciblées : un problème par PR.

## Exigences pour les contributions acceptables

Les conventions de code, l’architecture, les exigences de tests et la politique
de documentation sont définies dans [AGENTS.md](AGENTS.md) (version française :
[AGENTS.fr.md](AGENTS.fr.md)). En résumé :

- Anglais pour le code, les commentaires et la documentation ; français uniquement
  dans `translations/fr.json` et les fichiers secondaires `*.fr.md`.
- `uv run pytest tests/ -v` doit passer ; exécutez `prek run --all-files` avant de soumettre.
- Ajoutez ou mettez à jour les tests pour tout changement de logique ou nouvelle fonctionnalité.
- Mettez à jour `README.md`, `docs/`, `WORKFLOW.md` et `CHANGELOG.md` pour les
  changements visibles ou architecturaux.
- Ne journalisez ni ne commettez jamais de secrets ou d’identifiants.

## Signaler un problème

Utilisez les [tickets GitHub](https://github.com/gounick/ha-zero-inject-3erl/issues)
pour les rapports de bug et demandes d’amélioration. Pour les vulnérabilités de
sécurité, n’ouvrez pas de ticket public — suivez la [politique de sécurité](SECURITY.md).
