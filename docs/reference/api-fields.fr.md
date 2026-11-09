# Champs de l’API 3ERL

L’intégration interroge `https://3erl.fr/api.json` et expose les champs suivants.

| Champ | Type | Utilisation |
|---|---|---|
| `Bridage` | 0 / 1 | Signal de bridage ACI. Pilote le relais quand le contrat est `aci`. |
| `Bridage_CDC` | 0 / 1 | Signal de bridage ACC. Pilote le relais quand le contrat est `acc`. |
| `Dernier_PREP` | €/MWh | Dernier prix de règlement positif des écarts (PRE+). |
| `PRD4` | €/MWh | Moyenne journalière pondérée du PRE+ publiée par 3ERL. En ACI, c’est le prix appliqué au surplus injecté. Voir [calcul du PRE+ journalier](../explanation/daily-prep-estimate.fr.md). |
| `PREP_Profile` | chaîne | Indicateur de tendance journalière des prix. |
| `PREP_Profile_Num` | €/MWh | Forme numérique de la tendance journalière. |
| `Heure_Update` | chaîne | Horodatage de la dernière mise à jour de l’API. |
| `Bridage_Long_Terme` | nombre | Indicateur de bridage long terme. |
| `mode_degrade` | — | Indicateur de mode dégradé publié par 3ERL. |
| `rte_indispo_depuis` | chaîne | Horodatage depuis lequel les données RTE sont indisponibles, le cas échéant. |
| `Commentaires` | chaîne | Commentaires de l’opérateur. |

## Calendrier de mise à jour

Selon 3ERL, les données sont rafraîchies aux minutes 3, 18, 33 et 48 de chaque heure, à quelques secondes près. Quand 3ERL n’a pas reçu les données RTE à temps, il réessaie chaque minute jusqu’à leur arrivée.

L’intégration suit ce calendrier : après chaque poll réussi, elle lit `Heure_Update` et attend environ 18 minutes avant de réinterroger l’API. Si l’horodatage est absent, mal formé ou plus ancien qu’attendu, elle réessaie après environ une minute. Interroger plus souvent ne produirait pas de données plus fraîches.
