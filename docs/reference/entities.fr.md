# Entités

L’intégration crée les entités suivantes pour chaque entrée de configuration. Home Assistant construit chaque ID à partir du nom de l’appareil (`3ERL Zero-Injection`) et du nom de l’entité. Les ID ci-dessous correspondent à une nouvelle installation ; les entités renommées conservent leur ID personnalisé.

Les entités API et calculées exposent un attribut traduit `description` sous **Plus d’infos → Attributs**. Les diagnostics de supervision exposent une `reason` ainsi que les détails du relais ou de la mesure.

## Sensors

| Entité | Unité | Source | Description |
| --- | --- | --- | --- |
| `sensor.3erl_zero_injection_latest_pre` | €/MWh | `Dernier_PREP` | Dernier prix de règlement positif des écarts. |
| `sensor.3erl_zero_injection_daily_pre_average_prd4` | €/MWh | `PRD4` | Moyenne journalière pondérée du PRE+ publiée par 3ERL. |
| `sensor.3erl_zero_injection_daily_pre_weighted_by_prd3_3erl` | €/MWh | `PREP_Profile_Num` | PRE+ journalier pondéré par PRD3, calculé par 3ERL. |
| `sensor.3erl_zero_injection_current_pre` | €/MWh | calculé | PRE+ quart-horaire courant de RTE (utilisé en ACC). |
| `sensor.3erl_zero_injection_estimated_daily_pre` | €/MWh | calculé | PRE+ journalier estimé pour l’ACI avec le profil PRD3 Enedis. |
| `sensor.3erl_zero_injection_daily_trend` | — | `PREP_Profile` | Tendance journalière des prix. L’attribut `heure_update` porte l’horodatage API. |
| `sensor.3erl_zero_injection_last_rte_update` | timestamp | `Heure_Update` | Horodatage de la dernière mise à jour (`unknown` si le texte n’est pas analysable). L’attribut `raw_value` conserve la valeur brute. |
| `sensor.3erl_zero_injection_long_term_curtailment_until` | — | `Bridage_Long_Terme` | Indicateur de bridage long terme. |
| `sensor.3erl_zero_injection_degraded_mode` | — | `mode_degrade` | Indicateur brut de mode dégradé. |
| `sensor.3erl_zero_injection_rte_unavailable_since` | — | `rte_indispo_depuis` | Horodatage depuis lequel les données RTE sont indisponibles. |
| `sensor.3erl_zero_injection_comments` | — | `Commentaires` | Commentaires publiés par l’opérateur. |

L’intégration ne crée aucun capteur d’énergie bridée.

## Binary sensors

| Entité | Source | Description |
| --- | --- | --- |
| `binary_sensor.3erl_zero_injection_curtailment_requested` | `Bridage` | Actif quand le signal de bridage ACI est actif. |
| `binary_sensor.3erl_zero_injection_cdc_curtailment_requested` | `Bridage_CDC` | Actif quand le signal de bridage ACC est actif. |
| `binary_sensor.3erl_zero_injection_commanded_limitation` | calculé | Commande de limitation après application du mode ; inactive pendant le bypass, inconnue avant le premier signal en Auto. Attributs : `mode`, `reason`. |
| `binary_sensor.3erl_zero_injection_relay_control_fault` | supervision locale | Relais indisponibles immédiatement, ou désaccord pendant au moins 30 secondes. Attributs : `unavailable_relays`, `misaligned_relays`, `relay_states`, `manual_bypass`, `reason`. Inactif pendant le bypass. |
| `binary_sensor.3erl_zero_injection_grid_export_during_commanded_limitation` | mesure réseau optionnelle | Export au-dessus du seuil pendant une limitation commandée après la durée de confirmation. Inconnu si la mesure est absente, périmée ou invalide. L’absence d’export ne prouve pas un bridage effectif. |
| `binary_sensor.3erl_zero_injection_3erl_data_stale` | calculé | Actif quand les dernières données 3ERL dépassent deux cycles de publication. Attribut : `data_age_minutes`. |

L’entité `commanded_limitation` utilise le suffixe d’ID unique `commanded_limitation`. Les notifications décrivent une commande, pas l’acquittement du relais ni la mesure réseau. Les switchs relais d’origine restent la source des états remontés ; aucune entité d’état relais dupliquée n’est créée. Une panne API ne rend pas la supervision locale ni les commandes manuelles indisponibles.

## Interrupteur de bypass manuel

`switch.3erl_zero_injection_manual_bypass` suspend toutes les commandes de relais, y compris les modes forcés On/Off. Il ne change pas l’état physique du relais ; l’utilisateur pilote les switchs d’origine directement. Sa valeur est restaurée après redémarrage ou rechargement. Sa désactivation reprend immédiatement le mode sélectionné. Ce switch est indépendant de l’API.

## Visibilité par contrat

ACI masque `Bridage_CDC` et le PRE+ RTE courant. ACC masque `Bridage`, le PRE+ journalier estimé localement et le PRE+ pondéré PRD3 de 3ERL. Ces entités restent activées et conservent historique et identifiants. Un changement de contrat met à jour la visibilité gérée par l’intégration, sans écraser les choix explicites de l’utilisateur. Les cartes existantes continuent d’afficher les entités explicitement référencées.

| Contrat | Entité | Rôle |
| --- | --- | --- |
| ACI seulement | `binary_sensor.3erl_zero_injection_curtailment_requested` | Signal `Bridage`. |
| ACI seulement | `sensor.3erl_zero_injection_estimated_daily_pre` | PRE+ journalier estimé via PRD3. |
| ACI seulement | `sensor.3erl_zero_injection_daily_pre_weighted_by_prd3_3erl` | `PREP_Profile_Num` publié par 3ERL. |
| ACC seulement | `binary_sensor.3erl_zero_injection_cdc_curtailment_requested` | Signal `Bridage_CDC`. |
| ACC seulement | `sensor.3erl_zero_injection_current_pre` | PRE+ quart-horaire RTE courant. |
| ACI et ACC | `sensor.3erl_zero_injection_latest_pre` | `Dernier_PREP`. |
| ACI et ACC | `sensor.3erl_zero_injection_daily_pre_average_prd4` | `PRD4`. |
| ACI et ACC | `sensor.3erl_zero_injection_daily_trend` | `PREP_Profile`. |
| ACI et ACC | `sensor.3erl_zero_injection_last_rte_update` | `Heure_Update`. |
| ACI et ACC | `sensor.3erl_zero_injection_long_term_curtailment_until` | `Bridage_Long_Terme`. |
| ACI et ACC | `sensor.3erl_zero_injection_degraded_mode` | `mode_degrade`. |
| ACI et ACC | `sensor.3erl_zero_injection_rte_unavailable_since` | `rte_indispo_depuis`. |
| ACI et ACC | `sensor.3erl_zero_injection_comments` | `Commentaires`. |
| ACI et ACC | `binary_sensor.3erl_zero_injection_commanded_limitation` | Commande calculée après mode et bypass. |
| ACI et ACC | `binary_sensor.3erl_zero_injection_relay_control_fault` | Diagnostic des relais. |
| ACI et ACC | `binary_sensor.3erl_zero_injection_grid_export_during_commanded_limitation` | Observation d’export réseau. |
| ACI et ACC | `binary_sensor.3erl_zero_injection_3erl_data_stale` | Fraîcheur des données API. |
| ACI et ACC | `select.3erl_zero_injection_zero_injection_mode` | Mode Auto / On / Off. |
| ACI et ACC | `switch.3erl_zero_injection_manual_bypass` | Suspension manuelle des commandes. |

Les entités de rémunération estimée et d’énergie bridée ont été supprimées : la rémunération est publiée par 3ERL sur <https://dashboard.3erl.fr>, et l’énergie bridée ne peut pas être mesurée ou estimée de façon fiable à partir des entrées configurées. Aucune migration ni transfert de statistiques n’est fourni ; d’anciens registres peuvent rester indisponibles.

## Select

| Entité | Options | Description |
| --- | --- | --- |
| `select.3erl_zero_injection_zero_injection_mode` | `Auto`, `On`, `Off` | Mode de fonctionnement. `Auto` suit le signal 3ERL, `On` et `Off` forcent le relais. La dernière valeur est restaurée après redémarrage. |

## Pages liées

- [Options de configuration](configuration-options.fr.md)
- [Champs de l’API 3ERL](api-fields.fr.md)
