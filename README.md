# AutoLoc

AutoLoc est une application Django de gestion de location de voitures, avec un catalogue public, des réservations, des paiements manuels et un tableau de bord réservé au personnel. L'interface et la documentation sont en français.

## Prérequis

- Python 3.10 ou supérieur
- PostgreSQL 14 ou supérieur pour une installation de production
- Windows, macOS ou Linux

Pour un premier lancement local sans PostgreSQL, AutoLoc utilise SQLite si `DATABASE_URL` n'est pas défini. En production, configurez impérativement une URL PostgreSQL.

## Installation sous Windows

À la racine du projet, ouvrez **PowerShell** (et non l'invite de commandes `cmd.exe`) :

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Si vous utilisez l'invite de commandes Windows (`cmd.exe`), remplacez la ligne de copie par `copy .env.example .env` et activez l'environnement avec `.venv\Scripts\activate.bat`.

Ouvrez ensuite http://127.0.0.1:8000/. Sous Linux/macOS, activez l'environnement avec `source .venv/bin/activate`.

Le fichier `.env` n'est pas versionné. Pour employer PostgreSQL localement, définissez `DATABASE_URL`, par exemple `postgresql://autoloc:mot_de_passe@localhost:5432/autoloc`. Ajustez les variables dans `.env` selon votre environnement.

## Utilisation

- Les visiteurs peuvent parcourir et filtrer les voitures, puis s'inscrire pour réserver et gérer leurs favoris.
- Une réservation est créée « en attente » et bloque la voiture pendant ses dates. Le personnel peut ensuite la confirmer, démarrer, terminer ou annuler.
- Les dates sont traitées comme une période de location : la date de fin est exclue et le nombre de jours est la différence entre les deux dates. La date de fin doit être postérieure au début.
- Les paiements sont saisis manuellement par le personnel. Ils servent uniquement à suivre des montants réellement reçus ; aucun paiement bancaire n'est traité et aucune donnée de carte n'est collectée.
- Le tableau de bord est visible uniquement par les utilisateurs du personnel. Créez le premier compte de gestion avec `createsuperuser`.
- L'espace de gestion personnalisé est disponible sur `/gestion/` après connexion avec un compte personnel. Il permet de gérer les voitures, consulter les dossiers clients et réservations, modifier les statuts autorisés et enregistrer les paiements manuels. Pour ajouter un véhicule, ouvrez **Voitures → Ajouter une voiture**, remplissez ses informations et enregistrez ; l'archivage conserve les réservations déjà liées.
- L'administration Django classique reste disponible sur `/admin/` comme outil de secours. Son accès est réservé au personnel autorisé.

## Tests et contrôles

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

La suite de tests utilise SQLite et ne requiert pas de service PostgreSQL. En production, les migrations doivent être exécutées sur la base PostgreSQL configurée.

## Déploiement sur Render

Le fichier [`render.yaml`](./render.yaml) sélectionne l'offre gratuite pour le service Web et PostgreSQL, sans disque persistant. Pour essayer le déploiement :

1. Envoyez le projet sur GitHub (`git add .`, `git commit -m "Prepare AutoLoc deployment"`, puis `git push`).
2. Dans le tableau de bord Render, choisissez **New → Blueprint Instance**, reliez votre compte GitHub, sélectionnez le dépôt AutoLoc et appliquez le Blueprint trouvé dans `render.yaml`.
3. Vérifiez avant de confirmer que Render propose bien les plans **Free** pour les deux services. Le Blueprint génère `SECRET_KEY`, définit `DEBUG=False`, relie `DATABASE_URL` à PostgreSQL et utilise `build.sh` pour installer les dépendances, collecter les fichiers statiques et appliquer les migrations. Gunicorn se lie au port fourni par Render avec `gunicorn autoloc.wsgi:application --bind 0.0.0.0:$PORT`. Django ajoute automatiquement le domaine Render externe à `ALLOWED_HOSTS` et à `CSRF_TRUSTED_ORIGINS`.
4. Une fois le déploiement réussi, ouvrez l'URL `https://…onrender.com` affichée dans le tableau de bord.

Si un domaine personnalisé est ajouté, renseignez aussi `ALLOWED_HOSTS` avec le nom d'hôte sans `https://`, et `CSRF_TRUSTED_ORIGINS` avec l'origine complète, par exemple `https://www.mon-autoloc.com`.

**Limites de l'offre gratuite :**

- Le service Web se met en veille après une période d'inactivité ; le premier accès suivant peut prendre environ une minute. L'offre est destinée aux essais et démonstrations, pas à un service de production.
- Le système de fichiers du service est éphémère. Les photos téléversées par le formulaire d'administration ne sont donc pas conservées après une veille, un redémarrage ou un redéploiement. Les images déjà incluses dans `static/`, comme la photo du hero, restent présentes car elles sont reconstruites à chaque déploiement.
- PostgreSQL gratuit est limité (notamment à 1 Go) et expire 30 jours après sa création selon les conditions Render actuelles ; après expiration, il existe une période de grâce limitée avant suppression. Ne l'utilisez pas pour des données importantes sans sauvegarde.
- Les quotas gratuits, disponibilités et conditions peuvent évoluer ; consultez les [limites de l'offre gratuite Render](https://render.com/docs/free) avant de déployer. Le Blueprint ne demande pas de disque persistant payant.

Pour créer le premier compte personnel sans terminal Render, ouvrez **Environment** dans les paramètres du service Web et ajoutez `AUTOLOC_ADMIN_USERNAME`, `AUTOLOC_ADMIN_EMAIL` et `AUTOLOC_ADMIN_PASSWORD`. Choisissez un mot de passe fort et unique ; ne le mettez jamais dans le code, `build.sh`, le dépôt Git ou un message. Enregistrez les variables puis déclenchez un déploiement : après les migrations, `build.sh` exécute une commande idempotente qui crée le superutilisateur seulement s'il n'existe pas. Le mot de passe n'est pas affiché dans les journaux. Une fois le déploiement réussi, supprimez `AUTOLOC_ADMIN_PASSWORD` des variables Render et relancez un déploiement ; le compte existant ne sera ni supprimé ni modifié. Si le nom est déjà occupé par un compte ordinaire, la commande échoue sans changer ce compte : choisissez un autre nom. L'espace de gestion AutoLoc est sur `/gestion/` et l'interface Django de secours sur `/admin/`.

Aucun déploiement n'est effectué par ce dépôt et aucun lien public n'est donc fourni.

## Données et sécurité

Ne renseignez jamais de secret dans le code ou dans Git. Les valeurs d'exemple de `.env.example` doivent être remplacées localement. Les vues de gestion vérifient les permissions côté serveur, les favoris et réservations sont limités à leur propriétaire, les formulaires Django appliquent CSRF et le calcul des tarifs est exécuté côté serveur.
