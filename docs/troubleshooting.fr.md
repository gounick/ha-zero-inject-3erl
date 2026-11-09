# Dépannage

## L’intégration n’apparaît pas dans l’interface

- Vérifiez que `custom_components/zero_inject_3erl` est bien copié dans `config/custom_components`.
- Redémarrez complètement Home Assistant, pas seulement un rechargement.
- Videz le cache du navigateur ou essayez une fenêtre privée.

## Le flux de configuration échoue avec « cannot connect »

- Vérifiez que l’hôte Home Assistant peut joindre `https://3erl.fr/api.json`.
- Contrôlez l’URL saisie ; la valeur par défaut est `https://3erl.fr/api.json`.
- Consultez les journaux Home Assistant pour l’erreur exacte.
- Une réponse API incomplète ou mal formée est également rejetée : le signal du contrat et `Heure_Update` doivent être exploitables.

## Le relais ne se ferme pas

- Vérifiez que l’entité `switch.*` saisie est correcte.
- Contrôlez d’abord le bypass manuel : lorsqu’il est actif, toutes les commandes automatiques sont suspendues, y compris les modes forcés.
- Sans bypass, passez le mode sur **On** pour tester le relais. Les bascules manuelles sont corrigées à la prochaine évaluation du contrôleur.
- Consultez les journaux pour vérifier l’appel du service.
- Pour un relais Zigbee, vérifiez son appairage et sa disponibilité.

## Signal 3ERL figé ou indisponible

1. Activez le bypass manuel : l’intégration cesse de commander tous les relais configurés et conserve ce choix après redémarrage.
2. Pilotez les switchs d’origine et vérifiez l’export au compteur.
3. Quand la source redevient fiable, choisissez le mode souhaité puis désactivez le bypass. Le mode et le signal courants sont appliqués immédiatement.

En Auto, le dernier signal valide est conservé pendant une panne API après une première réponse réussie. Avant cette première réponse, les relais restent inchangés. Un drapeau qui ne change pas n’est pas forcément une panne : vérifiez l’horodatage API et le diagnostic de données périmées. Le bypass n’est jamais activé automatiquement.

## Défaut de pilotage des relais

Inspectez `unavailable_relays`, `misaligned_relays` et `relay_states`. Une indisponibilité est signalée immédiatement ; un désaccord bénéficie de 30 secondes de tolérance. Au retour, le relais est aligné sur la commande actuelle, pas sur une ancienne demande. Il n’existe pas de minuteur de retry dédié d’une minute. La supervision locale vérifie l’état toutes les cinq secondes sans envoyer de commande.

## Le diagnostic d’export est inconnu

Choisissez un capteur d’export positif dans les options. N’utilisez ni index cumulé ni capteur net signé. Pour un ZLinky, distinguez la puissance active en W et la puissance apparente en VA : cette dernière n’est pas une mesure active. Choisissez une source avec une cadence adaptée, réglez le seuil dans son unité de base W/VA et l’âge maximal selon sa cadence.

Une mesure numériquement inchangée peut tout de même être périmée si Home Assistant n’a pas reçu de rapport récent. Pour une source ZLinky `SINSTI` qui ne remonte que sur changement, [examples/zlinky-sinsti-refresh.yaml](examples/zlinky-sinsti-refresh.yaml) publie périodiquement une lecture MQTT : toutes les 4 minutes normalement et chaque minute pendant une limitation commandée. Ce diagnostic est seulement une observation : il ne bascule pas les relais et n’active pas le bypass. Une alerte confirmée s’efface quand l’export repasse sous le seuil, quand la commande se termine ou quand le bypass est activé ; une mesure invalide produit `unknown`.

## L’export n’est pas limité alors que le relais est actif

- Vérifiez la limitation configurée dans les paramètres installateur de l’Envoy.
- Confirmez que le niveau 2 correspond à **0 %** en ACI ou au palier attendu en ACC.
- Mesurez la continuité entre les bornes DRM quand le relais est fermé.
- Consultez [le guide de câblage](how-to/wire-the-relay.fr.md) et [la configuration Envoy](how-to/configure-envoy-drm.fr.md).

## Capteurs d’énergie bridée ou de rémunération manquants

Ces entités ont été supprimées volontairement. L’intégration ne peut pas mesurer la production qui aurait eu lieu sans limitation, et 3ERL publie déjà la rémunération estimée sur <https://dashboard.3erl.fr>. Supprimez les anciennes références à `sensor.3erl_zero_injection_curtailed_energy`, aux capteurs de rémunération et à `zero_inject_3erl.reset_counters` dans les dashboards, automatisations et scripts.
