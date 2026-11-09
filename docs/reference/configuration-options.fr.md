# Options de configuration

Tous les champs sont renseignés dans le flux de configuration et restent modifiables sous **Paramètres → Appareils et services → 3ERL Zero-Injection → Configurer**.

| Champ | Clé | Requis | Défaut | Description |
|---|---|---|---|---|
| URL de l’API 3ERL | `api_url` | oui | `https://3erl.fr/api.json` | Point d’accès interrogé pour les données de bridage. |
| Type de contrat | `aggregation_mode` | oui | `aci` | `aci` suit `Bridage` ; `acc` suit `Bridage_CDC`. Voir [ACI vs ACC](../explanation/concepts.fr.md#aci-vs-acc). |
| Interrupteurs des relais | `relay_entity` | oui | — | Une ou plusieurs entités `switch` câblées au(x) port(s) DRM. |
| Capteur d’export réseau | `injection_power_entity` | non | — | Mesure positive d’export en W/kW ou VA/kVA, utilisée uniquement pour l’observation. |
| Seuil d’export | `injection_threshold` | non | `50` | Seuil en W pour une puissance active ou VA pour une puissance apparente. |
| Durée de confirmation | `injection_delay` | non | `120` | Durée d’export au-dessus du seuil avant activation du diagnostic. |
| Âge maximal de mesure | `injection_max_age` | non | `300` | Âge maximal de la dernière mesure reçue avant un état inconnu. |
| Entités de notification | `notify_service` | non | — | Entités `notify` recevant `notify.send_message` lors d’un changement de commande. |
| Décalage du profil PRD3 | `prd3_day_offset` | non | `-2` | Jour utilisé pour choisir le profil PRD3 Enedis dans l’estimation ACI. |

## Instance unique

Une seule entrée peut être créée : un foyer possède soit un contrat ACI, soit un contrat ACC, et l’API 3ERL est un point d’accès unique.

## Polling

Il n’existe pas d’option d’intervalle. L’intégration suit le calendrier publié par 3ERL : environ 18 minutes après chaque `Heure_Update`, puis une nouvelle tentative après environ une minute si les données sont en retard. Voir [champs de l’API](api-fields.fr.md#calendrier-de-mise-à-jour).

## Modifier les options

Les changements prennent effet après le rechargement de l’entrée. L’URL de l’API, les relais, le capteur d’export, le type de contrat, les notifications et le décalage PRD3 peuvent être modifiés sans supprimer l’intégration. Le contrôle local reste disponible pendant une panne.
