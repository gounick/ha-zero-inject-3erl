# Services

## `zero_inject_3erl.set_bypass`

Active ou désactive le contournement manuel, éventuellement pour une durée limitée.

| Champ | Requis | Description |
|---|---|---|
| `enable` | non | `true` (par défaut) active le bypass ; `false` le désactive et annule une expiration en attente. |
| `duration` | non | Durée en minutes (1–1440) après laquelle le bypass se désactive automatiquement. Laisser vide pour un bypass persistant. |

Désactiver directement l'interrupteur de bypass — ou appeler `set_bypass` avec `enable: false` — annule une expiration en attente. La désactivation du bypass reprend le mode sélectionné et peut basculer le relais immédiatement.

## `zero_inject_3erl.set_mode`

Sélectionne le mode zéro-injection, éventuellement pour une durée limitée.

| Champ | Requis | Description |
|---|---|---|
| `mode` | oui | `Auto`, `On` ou `Off`. |
| `duration` | non | Durée en minutes (1–1440) après laquelle le mode revient à `Auto`. Laisser vide pour une sélection persistante. |

Changer le mode par un autre moyen (entité select, autre appel `set_mode`) annule un retour programmé.

Le contrôle utilisateur est aussi exposé par des entités :

- `select.3erl_zero_injection_zero_injection_mode` pour Auto / On / Off ;
- `switch.3erl_zero_injection_manual_bypass` pour suspendre toutes les commandes de relais.

La rémunération estimée et l'énergie bridée sont hors du périmètre de l'intégration.
Voir la [référence des entités](entities.fr.md).
