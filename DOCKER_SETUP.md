# Configuration Docker pour gbnqr

## Fichiers créés

J'ai créé les fichiers suivants pour dockeriser votre projet Django :

1. **Dockerfile** - Définit l'image Docker pour l'application
2. **docker-compose.yml** - Configuration pour orchestrer les services
3. **.dockerignore** - Exclut les fichiers inutiles du build Docker

## Prérequis

Installez Docker Desktop depuis : https://www.docker.com/products/docker-desktop

## Commandes Docker

### 1. Build l'image Docker
```bash
docker compose build
```

### 2. Démarrer le projet
```bash
docker compose up
```

Ou en mode détaché (background) :
```bash
docker compose up -d
```

### 3. Voir les logs
```bash
docker compose logs -f
```

### 4. Arrêter le projet
```bash
docker compose down
```

### 5. Reconstruire et redémarrer
```bash
docker compose up --build
```

## Accès à l'application

Une fois démarré, accédez à :
- **URL principale** : http://localhost:8000/
- **Dashboard** : http://localhost:8000/dashboard/
- **Admin** : http://localhost:8000/admin/

## Commandes utiles

### Exécuter des commandes Django dans le conteneur
```bash
# Créer un superuser
docker compose exec web python manage.py createsuperuser

# Faire des migrations
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate

# Collecter les fichiers statiques
docker compose exec web python manage.py collectstatic

# Accéder au shell Django
docker compose exec web python manage.py shell

# Accéder au bash du conteneur
docker compose exec web bash
```

### Voir les conteneurs en cours d'exécution
```bash
docker compose ps
```

### Supprimer les volumes (ATTENTION: supprime la base de données)
```bash
docker compose down -v
```

## Structure des volumes

Les volumes Docker sont configurés pour :
- **Code source** : Monté depuis `.` vers `/app` (modifications en temps réel)
- **Fichiers statiques** : Volume persistant `static_volume`
- **Fichiers média** : Volume persistant `media_volume`

## Modifications apportées à settings.py

J'ai ajouté les modifications suivantes pour supporter Docker :

1. **ALLOWED_HOSTS** : Lit depuis les variables d'environnement
2. **STATIC_ROOT** : Défini pour collecter les fichiers statiques

## Développement local vs Docker

### Mode développement local (sans Docker)
```bash
python3 manage.py runserver
```

### Mode Docker
```bash
docker compose up
```

## Troubleshooting

### Port 8000 déjà utilisé
Si le port 8000 est déjà utilisé, modifiez dans `docker-compose.yml` :
```yaml
ports:
  - "8001:8000"  # Change 8001 au port de votre choix
```

### Rebuilder après modification de requirements.txt
```bash
docker compose up --build
```

### Voir les erreurs
```bash
docker compose logs web
```
