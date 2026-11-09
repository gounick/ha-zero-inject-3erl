# Journal des modifications

Tous les changements notables du projet sont documentés dans ce fichier.

## [0.2.0] - 2026-11-09

### Ajouté

- Interrupteur de bypass manuel persistant : suspend toutes les commandes de relais, y compris les modes forcés, afin de piloter les relais directement pendant un signal figé ou une panne API.
- Diagnostic de défaut de pilotage des relais avec signalement immédiat des indisponibilités et tolérance de 30 secondes pour les désaccords, avec états par relais en attributs.
- Supervision optionnelle de l’export réseau avec seuil, durée de confirmation et fraîcheur configurables. Prend en charge W/kW et VA/kVA sans confondre puissance apparente et active.
- Visibilité ACI/ACC des entités selon le contrat, avec conservation des choix explicites de l’utilisateur et des ID existants.
- Contrôle local et diagnostics chargés même si la première requête 3ERL échoue ; Auto laisse les relais inchangés jusqu’au premier signal valide. Les options peuvent être sauvegardées sans API disponible.
- Capteurs tarifaires RTE/Enedis informatifs sur un coordinator indépendant : une panne de prix ne retarde pas le contrôle.
- Nouveau binary sensor `3ERL data stale`, rafraîchi par un minuteur local afin que son âge progresse sans événement API ou capteur.
- Workflows GitHub Actions : hassfest, validation HACS, analyses de sécurité et contrôles de release.
- Documentation restructurée selon Diátaxis avec guides de câblage, Envoy, dashboard et dépannage.

### Modifié

- **Rupture de développement :** les signaux 3ERL mal formés, absents ou futurs sont rejetés puis réessayés au lieu d’être interprétés comme « pas de bridage ». Le dernier signal valide reste utilisé après une première réponse réussie.
- `Bridage`/`Bridage_CDC` sous forme de chaîne `"1"` est reconnu comme actif ; les valeurs inattendues deviennent inconnues plutôt que fausses.
- Le polling suit le calendrier de publication 3ERL et borne les horodatages externes, empêchant un `Heure_Update` futur de retarder le polling de plusieurs mois.
- Les commandes relais sont regroupées par domaine et état, dédupliquées pendant l’exécution d’un appel lent et revérifiées avant envoi effectif.
- `relay_entity` et `notify_service` acceptent plusieurs entités ; les anciennes entrées à valeur unique sont normalisées.
- Les calculs tarifaires sont ancrés sur Europe/Paris ; les échecs RTE et Enedis sont indépendants du coordinator de contrôle.
- Les options remplacent maintenant complètement les données initiales : un champ optionnel effacé ne réapparaît plus à la sauvegarde suivante.
- Les noms d’entités utilisent des clés de traduction ; le select de mode reçoit un préfixe de domaine via une migration.
- Le diagnostic `3ERL data stale` expose un âge calculé en direct et considère aussi un horodatage futur comme périmé.

### Supprimé

- **Rupture de développement :** le capteur d’énergie bridée, le stockage cumulatif, `pv_power_entity`, `consumption_power_entity` et `zero_inject_3erl.reset_counters` ont été supprimés. Un capteur de puissance ne peut pas mesurer la production contrefactuelle qui aurait eu lieu sans limitation.
- Les capteurs de rémunération estimée et leurs champs de stockage ont été supprimés. La rémunération est publiée par 3ERL sur <https://dashboard.3erl.fr> et reste hors périmètre.
- Les entités et champs `puissance_bridable`, `update_interval` et `pv_system_type` ont été supprimés.
- Aucune migration, alias ni transfert de statistiques n’est fourni pour les entités supprimées ; d’anciennes entrées du registre peuvent rester indisponibles.

### Corrigé

- L’ouverture du flux d’options ne plante plus et ne restaure plus un champ optionnel précédemment supprimé.
- Les notifications utilisent `notify.send_message` et ne sont envoyées que lors d’un changement de commande.
- `Current PRE+` utilise le dernier créneau quart-horaire publié au lieu de rester `unknown`.
- Les valeurs RTE/Enedis invalides ou non finies sont ignorées au lieu de propager `NaN` ou l’infini dans les capteurs.
- La réponse JSON Enedis servie en `text/html` est correctement analysée.
- Le déchargement pendant une récupération tarifaire bloquée annule la tâche sans faire échouer l’entrée.
- La documentation ne promet plus un comportement matériel fail-open que le logiciel ne peut pas garantir.

## [0.1.0] - 2026-09-30

### Ajouté en 0.1.0

- Version initiale de l’intégration 3ERL Zero-Injection.
- Interrogation de l’API publique 3ERL pour les signaux de bridage et les prix PRE+.
- Pilotage d’un relais configurable pour le zéro-injection avec modes Auto/On/Off.
- Suivi de l’énergie PV bridée et estimation de la rémunération 3ERL à 70 % du PRE+.
- Persistance des compteurs cumulatifs d’énergie et de gain entre redémarrages.
- Service de remise à zéro des compteurs.
- Configuration et options par flux Home Assistant.
- Ajout de `helpers.py` pour la logique partagée de bridage et de mode.
- Ajout de tests unitaires pour le client API, les helpers et le coordinator.
