# Comment est calculé le PRE+ journalier

Cette page explique d'où vient la valeur **PRE+ journalier estimé** et pourquoi il s'agit d'une estimation.

> Basé sur l'explication publiée par la communauté dans [ce gist](https://gist.github.com/mathieucarbou/8d83d25247821e85a693dea61fe4f0d2).

## Contexte

3ERL annonce chaque soir (vers 22 h) le prix retenu pour rémunérer le surplus injecté dans la journée. Pour les contrats ACI, ce prix n'est **pas** le dernier PRE+ quart-horaire. C'est une moyenne journalière des PRE+, pondérée par la courbe d'ensoleillement nationale.

## La formule

Pour chaque pas quart-horaire de la journée, Enedis calcule :

```text
PRE+ ajusté (pas) = PRE+ (pas) × coefficient PRD3 (pas)
```

- Le **PRE+** (Prix de Règlement positif des Écarts) est publié par RTE pour chaque quart d'heure de la journée.
- Le **PRD3** est un coefficient de profil dynamique publié par Enedis. Il décrit la forme de la courbe de production solaire nationale du jour : proche de zéro la nuit, maximal autour du midi solaire.

En fin de journée, le prix de rémunération est :

```text
PRE+ journalier = SOMME(PRE+ ajustés) / SOMME(coefficients PRD3)
```

Autrement dit, le PRE+ de chaque quart d'heure ne compte qu'en proportion de la production solaire nationale à cet instant. Les heures creuses de milieu de journée pèsent beaucoup ; les heures du soir ne pèsent presque rien.

## Pourquoi l'intégration affiche une *estimation*

Le profil PRD3 du jour n'est connu qu'après coup : Enedis le publie le lendemain matin. Pour afficher une estimation en cours de journée, l'intégration combine donc :

- les PRE+ quart-horaires du jour, depuis l'[API open data de RTE](https://www.services-rte.com/), et
- le profil PRD3 d'un **jour passé** (par défaut : 2 jours avant, car le profil d'hier n'est disponible qu'en fin de matinée). C'est l'option `prd3_day_offset`.

```text
PRE+_journalier_estimé = SOMME(PRE+ du jour × coefficient PRD3 du jour passé) / SOMME(coefficients PRD3)
```

Les pas de temps PRE+ et PRD3 sont alignés sur l'heure de la journée (heure et minute), pas sur la date complète.

## Comment lire l'estimation dans la journée

- Avant le lever et après le coucher du soleil, l'estimation est absente ou sans signification : les coefficients PRD3 sont nuls et rien ne pèse encore dans la moyenne.
- En matinée, l'estimation bouge beaucoup : chaque nouveau pas ajoute une part importante du poids journalier.
- À partir du début d'après-midi, elle se stabilise : l'essentiel du poids de la journée est déjà connu et les pas suivants ne changent presque plus la moyenne.

La valeur exposée par l'intégration converge vers le chiffre que 3ERL annonce le soir. Des écarts restent possibles, car le calcul réel utilise le profil PRD3 du jour même, et non celui d'un jour passé.

## Contrats ACC

En autoconsommation collective (ACC), il n'y a pas de pondération journalière : chaque quart d'heure de surplus est valorisé au PRE+ de ce même pas. L'intégration expose pour cela le PRE+ quart-horaire courant et n'utilise pas le profil PRD3.

## Pages liées

- [Concepts : fonctionnement du zéro-injection 3ERL](concepts.md)
- [Référence des champs de l'API](../reference/api-fields.md)
- [Référence des entités](../reference/entities.md)
