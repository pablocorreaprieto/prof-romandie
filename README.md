# Prof Romandie

Guide en français, espagnol et italien pour les enseignants formés à l'étranger qui veulent enseigner en Suisse romande. Auteur Pablo Correa Prieto. Site prévu sur https://profromandie.ch.

## Construire

```
pip install -r requirements.txt
python3 build.py --preview   # aperçu dans preview/, liens relatifs
python3 build.py             # site final dans site/
```

Les contenus sont dans `content/<langue>/` (Markdown avec en-tête YAML, et `home.yml` pour l'accueil). Après une nouvelle vérification des sources officielles, changer `CHECKED` dans `build.py`.

## Publier

Chaque push sur `main` lance `.github/workflows/pages.yml`, qui construit le site et le publie sur GitHub Pages. Réglages du dépôt, Pages, source GitHub Actions, domaine profromandie.ch, HTTPS imposé.

## Contact

L'adresse e-mail n'est jamais écrite dans le dépôt. Sans la variable `PR_CONTACT_EMAIL`, les pages renvoient vers l'adresse publiée sur pablocorreaprieto.ch. Pour afficher une adresse directe, créer la variable de dépôt `PR_CONTACT_EMAIL` (Settings, Secrets and variables, Actions, Variables).
