# Prof Romandie

Guide en français, anglais, espagnol et italien pour les enseignants formés à l'étranger qui veulent enseigner en Suisse romande. Auteur Pablo Correa Prieto. Site prévu sur https://profromandie.ch.

## Construire

```
pip install -r requirements.txt
python3 build.py --preview   # aperçu dans preview/, liens relatifs
python3 build.py             # site final dans site/
```

Les contenus sont dans `content/<langue>/` (Markdown avec en-tête YAML, et `home.yml` pour l'accueil). Après une nouvelle vérification des sources officielles, changer `CHECKED` dans `build.py`.

## Publier

Chaque push sur `main` lance `.github/workflows/pages.yml`, qui construit le site et le publie sur GitHub Pages. Réglages du dépôt, Pages, source GitHub Actions, domaine profromandie.ch, HTTPS imposé.

## Images de partage

`assets/img/og-<langue>.png` (1200 × 630) sont les images qui s'affichent quand on partage une page dans WhatsApp, Facebook, LinkedIn ou un e-mail. Elles reprennent le titre de l'accueil de chaque langue et la date de vérification des sources. Après un changement de titre ou de date :

```
pip install playwright && playwright install chromium
python3 tools/og/render.py
```

## IndexNow

Après chaque publication, le job `indexnow` du workflow signale les pages modifiées à Bing et aux autres moteurs IndexNow (Yandex, Seznam, Naver). La clé est `INDEXNOW_KEY` dans `build.py`, publiée par la construction à la racine du site. Ne pas la changer. Un lancement manuel du workflow envoie toutes les pages. Google n'utilise pas IndexNow, il faut passer par la Search Console.

## Contact

L'adresse e-mail n'est jamais écrite dans le dépôt. Sans la variable `PR_CONTACT_EMAIL`, les pages renvoient vers l'adresse publiée sur pablocorreaprieto.ch. Pour afficher une adresse directe, créer la variable de dépôt `PR_CONTACT_EMAIL` (Settings, Secrets and variables, Actions, Variables).
