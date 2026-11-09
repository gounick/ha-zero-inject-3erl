# 3ERL Zero-Injection

[![hassfest](https://github.com/gounick/ha-zero-inject-3erl/actions/workflows/hassfest.yaml/badge.svg?branch=main)](https://github.com/gounick/ha-zero-inject-3erl/actions/workflows/hassfest.yaml)
[![HACS](https://github.com/gounick/ha-zero-inject-3erl/actions/workflows/hacs.yml/badge.svg?branch=main)](https://github.com/gounick/ha-zero-inject-3erl/actions/workflows/hacs.yml)
[![Tests](https://github.com/gounick/ha-zero-inject-3erl/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/gounick/ha-zero-inject-3erl/actions/workflows/tests.yml)
[![Security](https://github.com/gounick/ha-zero-inject-3erl/actions/workflows/security.yml/badge.svg?branch=main)](https://github.com/gounick/ha-zero-inject-3erl/actions/workflows/security.yml)
[![Release checks](https://github.com/gounick/ha-zero-inject-3erl/actions/workflows/release.yml/badge.svg?branch=main)](https://github.com/gounick/ha-zero-inject-3erl/actions/workflows/release.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
![Version](https://img.shields.io/github/v/release/gounick/ha-zero-inject-3erl?style=plastic)

> **Travail en cours** : cette intégration est en développement actif. Des ruptures de compatibilité peuvent survenir avant la première version stable.

Intégration Home Assistant personnalisée qui surveille l’API française [3ERL](https://3erl.fr) et commande un relais à contact sec pour limiter l’injection photovoltaïque sur demande.

> Projet inspiré de [Automatisation-Bridage-3ERL-Emphase](https://github.com/ALP40/Automatisation-Bridage-3ERL-Emphase).

## Fonctionnalités

- Interroge l’API publique 3ERL (`https://3erl.fr/api.json`) pour les signaux de bridage.
- Prend en charge les contrats **ACI** (`Bridage`) et **ACC** (`Bridage_CDC`).
- Disponible comme intégration personnalisée HACS.
- Crée des capteurs pour les champs 3ERL : `Bridage`, `Bridage_CDC`, `Dernier_PREP`, `PRD4`, `PREP_Profile`, `Heure_Update`, `Bridage_Long_Terme`, etc.
- Pilote un ou plusieurs switchs relais en trois modes :
  - **Auto** — le relais suit le signal 3ERL ;
  - **On** — limitation toujours active ;
  - **Off** — limitation désactivée.
- Ne mesure ni n’estime l’énergie bridée ; la rémunération est publiée par 3ERL sur <https://dashboard.3erl.fr>.
- Envoie des notifications optionnelles lorsque la commande change, sans prétendre confirmer le relais ou l’absence d’export.
- Fournit un bypass manuel persistant qui suspend toutes les commandes, même pendant une panne 3ERL.
- Supervise séparément l’acquittement du relais et une mesure optionnelle d’export réseau, y compris ZLinky en W ou VA.
- Masque les entités propres à ACI/ACC selon le contrat tout en préservant les choix manuels.
- N’enregistre aucun service personnalisé ; le contrôle se fait par entités et options.

## Systèmes PV pris en charge

L’intégration pilote des switchs relais fournis par l’utilisateur et peut observer un capteur d’export réseau. L’auto-détection de marques d’onduleurs (Enphase, SMA, Fronius, etc.) pourra arriver plus tard via des modules providers ; les contributions sont bienvenues.

## Prérequis

- Home Assistant 2026.9.3 ou plus récent.
- Une ou plusieurs entités `switch` pilotant les relais de zéro-injection.
- Optionnel : capteur d’export positif en W/kW ou VA/kVA pour l’observation.

## Installation

### HACS (recommandé)

1. Installez [HACS](https://hacs.xyz).
2. Ajoutez ce dépôt comme dépôt personnalisé.
3. Installez **3ERL Zero-Injection**.

   [![Ouvrir votre instance Home Assistant et ajouter un dépôt dans HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=gounick&repository=ha-zero-inject-3erl&category=integration)

4. Ajoutez **3ERL Zero-Injection** à Home Assistant :

   [![Ouvrir votre instance Home Assistant et lancer la configuration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=zero_inject_3erl)

### Manuel

1. Copiez `custom_components/zero_inject_3erl` dans `config/custom_components`.
2. Redémarrez Home Assistant.
3. Ajoutez **3ERL Zero-Injection** :

   [![Ouvrir votre instance Home Assistant et lancer la configuration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=zero_inject_3erl)

## Configuration

Suivez [docs/how-to/install-and-configure.fr.md](docs/how-to/install-and-configure.fr.md). Tous les champs sont décrits dans la [référence de configuration](docs/reference/configuration-options.fr.md).

Choix important : sélectionnez le **type de contrat d’autoconsommation** (`aci` ou `acc`) correspondant à votre contrat 3ERL. Il détermine le signal API suivi et le niveau relais à configurer dans l’Envoy.

## Entités

L’intégration crée des sensors pour les champs API et les prix informatifs, des binary sensors pour la demande et la commande, ainsi qu’un select Auto / On / Off. Voir la [référence des entités](docs/reference/entities.fr.md).

## Rémunération et énergie bridée

L’intégration n’estime pas la rémunération. 3ERL la publie sur son tableau de bord : <https://dashboard.3erl.fr>.

Elle ne mesure ni n’estime non plus l’énergie bridée. Un capteur de puissance ne peut pas connaître la production contrefactuelle qui aurait eu lieu sans limitation ; l’ancien compteur expérimental a donc été supprimé plutôt que conservé sous un nom trompeur.

## Changements d’entités en développement

Cette version introduit l’entité de limitation commandée et supprime les entités et actions purement estimatives :

- `binary_sensor.3erl_zero_injection_commanded_limitation`
- `sensor.3erl_zero_injection_curtailed_energy` — supprimé
- `zero_inject_3erl.reset_counters` — supprimé
- `sensor.3erl_zero_injection_estimated_cumulative_remuneration` — supprimé
- `sensor.3erl_zero_injection_estimated_hourly_remuneration` — supprimé

Aucune migration ni alias n’est fourni. Mettez à jour les références dans dashboards, automatisations et scripts. D’anciens registres peuvent rester indisponibles et les anciennes statistiques ne sont pas transférées.

## Contrôle manuel et supervision

Activez **Manual bypass** pour suspendre toutes les commandes, y compris On/Off forcés. Pilotez alors directement le switch relais d’origine. Le bypass survit aux rechargements et redémarrages ; sa désactivation reprend le mode sélectionné et peut basculer le relais immédiatement.

**Commanded limitation** décrit seulement l’intention. Le diagnostic de défaut relais signale immédiatement les indisponibilités puis les désaccords persistants après 30 secondes. Le diagnostic d’export signale un dépassement de seuil pendant une limitation commandée après confirmation. L’absence d’export observée ne prouve pas un bridage effectif.

Configurez une mesure positive d’export dans les options. Les mesures ZLinky actives en W et apparentes en VA sont prises en charge comme grandeurs distinctes. Les défauts sont : seuil 50 W ou VA, confirmation 120 secondes et âge maximal 300 secondes. Une mesure absente, périmée, négative ou non finie produit `unknown`, jamais zéro.

## Services

L’intégration n’enregistre aucun service personnalisé.

## Tableau de bord

Des exemples de cartes Lovelace sont disponibles dans [docs/how-to/build-a-dashboard.fr.md](docs/how-to/build-a-dashboard.fr.md).

## Documentation

Voir [docs/README.fr.md](docs/README.fr.md) pour l’index complet.

- [Fonctionnement du zéro-injection 3ERL](docs/explanation/concepts.fr.md)
- [Configurer le port DRM Envoy](docs/how-to/configure-envoy-drm.fr.md)
- [Câbler le relais à contact sec](docs/how-to/wire-the-relay.fr.md)
- [Installer et configurer](docs/how-to/install-and-configure.fr.md)
- [Entités](docs/reference/entities.fr.md), [options](docs/reference/configuration-options.fr.md), [champs API](docs/reference/api-fields.fr.md), [services](docs/reference/services.fr.md)
- [Dépannage](docs/troubleshooting.fr.md)
- [Workflow et architecture](WORKFLOW.fr.md)

## Contributions

Les contributions pour d’autres systèmes PV ou agrégateurs de bridage sont bienvenues. Ouvrez un ticket avant une pull request.

## Développement

Le projet utilise [prek](https://prek.j178.dev/) pour les hooks locaux :

```sh
prek run --all-files
```

Tests :

```sh
uv sync --extra test
uv run pytest tests/ -v
```

## Licence

Projet sous licence MIT.
