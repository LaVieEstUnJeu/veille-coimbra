# Veille logement Coimbra - site public

Deux tableaux triables, generes depuis les veilles automatiques du workspace Jarvis :

- `courte-duree.html` : logements meubles entiers reservables en ligne (sejour 1 mois, sept. 2026)
- `longue-duree.html` : T2 bail 12 mois (visa D7), quartiers Solum / Santo Antonio dos Olivais

Mise a jour : `python generer_site.py` (lit les data/ des deux veilles), puis commit + push.
Le deploiement Netlify suit le push automatiquement.
