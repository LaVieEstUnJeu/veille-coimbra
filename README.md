# Veille logement Coimbra - site public (GitHub Pages)

Deux tableaux triables, generes depuis les veilles automatiques du workspace,
publies sur **GitHub Pages** : https://lavieestunjeu.github.io/veille-coimbra/

- `courte-duree.html` : logements meubles entiers reservables en ligne
  (sejour 1 mois, sept. 2026)
- `longue-duree.html` : T2 bail 12 mois (visa D7), quartiers Solum /
  Santo Antonio dos Olivais

Tri par defaut : date de decouverte, les plus recentes en premier.
Le site est LA sortie des veilles (les emails sont desactives depuis le
2026-07-12).

## Chaine de publication automatique

Chaque tache planifiee (9h00 courte duree, 9h20 et 13h00 T2) termine par
`python publier.py` : regeneration des pages -> commit -> push -> GitHub
Pages redeploie. Rien a pousser = sortie silencieuse. Journal :
`publier.log` (exclu du depot). Mise a jour manuelle : `python publier.py`.

## Pourquoi GitHub Pages et pas Netlify

Le compte Netlify (tarification a credits, 300/mois pour tout le compte,
15 credits par deploiement) est reserve a Champigrond. GitHub Pages :
pushes illimites, gratuits. Decision du 2026-07-12.

## REPO PUBLIC - regles de confidentialite

GitHub Pages gratuit exige un depot public. En consequence :
- JAMAIS de nom, de courriel personnel ni de secret dans ce dossier.
- L'identite Git du depot est l'adresse noreply GitHub
  (`LaVieEstUnJeu@users.noreply.github.com`), configuree en local dans
  `.git/config`. Ne pas la remplacer par un courriel reel.
- L'historique a ete reecrit a neuf le 2026-07-12 pour purger l'ancienne
  identite ; ne pas reintroduire d'anciens commits.

`.nojekyll` : sert le HTML tel quel (pas de build Jekyll cote GitHub).
