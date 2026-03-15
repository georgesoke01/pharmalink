# PharmaLink — Backend Django

> API centrale de la plateforme de localisation et gestion de pharmacies.

## Prérequis

- Python 3.12+
- Docker + docker-compose
- PostgreSQL 15 + PostGIS (via Docker en dev)

## Installation (développement)

```bash
# 1. Cloner le repo
git clone https://github.com/georgesoke01/pharmalink.git
cd pharmalink

# 2. Copier et configurer les variables d'environnement
cp .env.example .env

# 3. Lancer l'infra Docker
docker-compose up -d db redis

# 4. Créer l'environnement virtuel Python
python -m venv venv && source venv/bin/activate

# 5. Installer les dépendances
pip install -r requirements.txt

# 6. Appliquer les migrations
python manage.py migrate

# 7. Créer un super admin
python manage.py createsuperuser

# 8. Lancer le serveur
python manage.py runserver
```

## Lancer avec Docker (tout en un)

```bash
docker-compose up --build
```

L'API est disponible sur http://localhost:8000/api/v1/
La documentation Swagger est sur http://localhost:8000/api/docs/

## Tests

```bash
pytest
```

## Structure du projet

Voir [ARCHITECTURE.md](./ARCHITECTURE.md) pour la documentation complète.

## Endpoints principaux

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/auth/token/` | Obtenir un JWT |
| `POST /api/v1/auth/token/refresh/` | Rafraîchir le token |
| `GET /api/v1/pharmacies/` | Liste des pharmacies |
| `GET /api/v1/produits/` | Catalogue produits |
| `GET /api/v1/gardes/` | Pharmacies de garde |
| `POST /api/v1/lgo/sync/` | Déclencher une sync LGO |