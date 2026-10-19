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

1. Poussez le projet sur un dépôt GitHub privé ou public.
2. Créez une base PostgreSQL et un service Web Render depuis le dépôt (ou utilisez `render.yaml` comme point de départ).
3. Configurez `DATABASE_URL` avec l'URL interne de la base PostgreSQL. Définissez `SECRET_KEY` comme secret Render, `DEBUG=False`, `ALLOWED_HOSTS` avec le domaine attribué et `CSRF_TRUSTED_ORIGINS` avec son origine HTTPS complète.
4. Utilisez `build.sh` comme commande de build et `gunicorn autoloc.wsgi:application` comme commande de démarrage.
5. Créez un compte de gestion avec `python manage.py createsuperuser` depuis une commande shell Render.

Les fichiers statiques sont servis par WhiteNoise. Les images téléversées sont stockées dans `media/` par défaut ; sur Render, un disque persistant doit être monté sur `/var/data` et `MEDIA_ROOT=/var/data` doit être défini pour conserver ces fichiers après redéploiement. Les médias sont servis par Django, ce qui convient à une démonstration de petite taille ; pour un trafic important, configurez un stockage d'objets adapté. Sans disque persistant, les images ajoutées en production ne sont pas garanties de survivre aux redéploiements.

Vérifiez les tarifs, limites, règles de conservation et disponibilités actuels des services Render et PostgreSQL avant toute publication. Aucun déploiement n'est effectué par ce dépôt et aucun lien public n'est donc fourni.

## Données et sécurité

Ne renseignez jamais de secret dans le code ou dans Git. Les valeurs d'exemple de `.env.example` doivent être remplacées localement. Les vues de gestion vérifient les permissions côté serveur, les favoris et réservations sont limités à leur propriétaire, les formulaires Django appliquent CSRF et le calcul des tarifs est exécuté côté serveur.
