import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'opale_project.settings')
django.setup()

from organizations.models import Direction
from catalogue.models import Application, DirectionApplication
from accounts.models import Utilisateur
from django.contrib.auth.hashers import make_password

def seed_data():
    print("Sowing the seeds of the ART Portal...")

    # 1. Directions
    directions = [
        {"nom": "Direction des Affaires Juridiques", "code": "DAJ", "description": "Gestion des aspects légaux et réglementaires."},
        {"nom": "Direction Technique", "code": "DT", "description": "Supervision technique et régulation des réseaux."},
        {"nom": "Direction Financière", "code": "DAF", "description": "Gestion budgétaire et comptable."},
        {"nom": "Direction des Ressources Humaines", "code": "DRH", "description": "Gestion du personnel."},
    ]

    dir_objs = {}
    for d in directions:
        obj, created = Direction.objects.get_or_create(nom=d["nom"], defaults=d)
        dir_objs[d["code"]] = obj
        if created: print(f"  [+] Direction créée : {d['nom']}")

    # 2. Applications
    apps = [
        {"nom": "Gestion des Plaintes", "url_acces": "http://plaintes.art.local", "icone_name": "message-square-warning", "description": "Plateforme de gestion des plaintes des consommateurs."},
        {"nom": "Monitoring des Réseaux", "url_acces": "http://monitoring.art.local", "icone_name": "activity", "description": "Outil de surveillance en temps réel de la qualité de service."},
        {"nom": "Comptabilité Analytique", "url_acces": "http://finance.art.local", "icone_name": "pie-chart", "description": "Système de suivi des coûts et budgets."},
        {"nom": "Portail RH (MyART)", "url_acces": "http://rh.art.local", "icone_name": "users", "description": "Libre-service employé (Congés, Paie)."},
        {"nom": "Base de Connaissance Légale", "url_acces": "http://legal.art.local", "icone_name": "book-open", "description": "Référentiel des textes de loi et règlements."},
        
        # Applications PoC (Single Sign-On AD)
        {"nom": "Zimbra Mail", "url_acces": "/apps/zimbra-mail/", "icone_name": "mail", "description": "Messagerie collaborative interne (Simulation Zimbra)."},
        {"nom": "Suivi des Licences", "url_acces": "/apps/licences/", "icone_name": "landmark", "description": "Suivi réglementaire des concessions et titres d'exploitation."},
        {"nom": "Supervision du Spectre", "url_acces": "/apps/spectre/", "icone_name": "radio", "description": "Régulation technique et supervision du spectre radioélectrique."},
    ]

    app_objs = {}
    for a in apps:
        obj, created = Application.objects.get_or_create(nom=a["nom"], defaults=a)
        app_objs[a["nom"]] = obj
        if created: print(f"  [+] Application créée : {a['nom']}")

    # 3. Habilitations (DirectionApplication)
    habilitations = [
        ("DAJ", "Base de Connaissance Légale"),
        ("DT", "Monitoring des Réseaux"),
        ("DT", "Gestion des Plaintes"),
        ("DAF", "Comptabilité Analytique"),
        ("DRH", "Portail RH (MyART)"),
        
        # Habilitations PoC
        ("DT", "Zimbra Mail"),
        ("DAF", "Zimbra Mail"),
        ("DRH", "Zimbra Mail"),
        ("DAJ", "Zimbra Mail"),
        
        ("DT", "Suivi des Licences"),
        ("DAF", "Suivi des Licences"),
        ("DAJ", "Suivi des Licences"),
        
        ("DT", "Supervision du Spectre"),
    ]

    for dir_code, app_name in habilitations:
        DirectionApplication.objects.get_or_create(
            direction=dir_objs[dir_code],
            application=app_objs[app_name]
        )

    # 4. Utilisateurs de test
    users = [
        {"username": "juriste_art", "email": "juriste@art.local", "first_name": "Jean", "last_name": "Légal", "role": "EMPLOYE", "direction": dir_objs["DAJ"]},
        {"username": "tech_art", "email": "tech@art.local", "first_name": "Paul", "last_name": "Réseau", "role": "EMPLOYE", "direction": dir_objs["DT"]},
        {"username": "admin_art", "email": "admin@art.local", "first_name": "Admin", "last_name": "Portal", "role": "ADMIN", "direction": dir_objs["DT"], "is_staff": True, "is_superuser": True},
    ]

    for u in users:
        direction = u.pop("direction")
        password = make_password("art_2026")
        user, created = Utilisateur.objects.get_or_create(
            username=u["username"], 
            defaults={**u, "password": password, "direction": direction}
        )
        if created: print(f"  [+] Utilisateur créé : {u['username']} (Pass: art_2026)")

    print("\n[SUCCESS] Le système Opale a été peuplé avec succès.")

if __name__ == "__main__":
    seed_data()
