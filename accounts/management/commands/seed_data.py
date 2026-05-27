from django.core.management.base import BaseCommand
from accounts.models import Utilisateur
from organizations.models import Direction
from catalogue.models import Application, DirectionApplication
from django.db import transaction

class Command(BaseCommand):
    help = 'Peuple la base de données avec des directions, applications et utilisateurs de test.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Début du peuplement de la base de données...'))
        
        with transaction.atomic():
            # 1. Création des Directions
            directions_data = [
                {'nom': 'Direction Technique', 'code': 'DT', 'description': 'Maintenance, infrastructure et développement.'},
                {'nom': 'Direction Financière', 'code': 'DAF', 'description': 'Comptabilité, budget et finances.'},
                {'nom': 'Ressources Humaines', 'code': 'RH', 'description': 'Gestion du personnel et carrières.'},
                {'nom': 'Direction Générale', 'code': 'DG', 'description': 'Pilotage stratégique de l\'ART.'},
            ]
            
            directions = {}
            for d_data in directions_data:
                d, created = Direction.objects.get_or_create(code=d_data['code'], defaults=d_data)
                directions[d_data['code']] = d
                if created:
                    self.stdout.write(f"Direction {d.nom} créée.")

            # 2. Création des Applications
            apps_data = [
                {
                    'nom': 'GMAO Expert',
                    'url_acces': 'https://gmao.art.cm',
                    'icone_name': 'settings',
                    'description': 'Gestion de la Maintenance Assistée par Ordinateur.',
                    'authorized': ['DT', 'DG']
                },
                {
                    'nom': 'Sage ERP',
                    'url_acces': 'https://sage.art.cm',
                    'icone_name': 'landmark',
                    'description': 'Gestion comptable et financière.',
                    'authorized': ['DAF', 'DG']
                },
                {
                    'nom': 'Zimbra Mail',
                    'url_acces': 'https://mail.art.cm',
                    'icone_name': 'mail',
                    'description': 'Messagerie collaborative interne.',
                    'authorized': ['DT', 'DAF', 'RH', 'DG']
                },
                {
                    'nom': 'Audit Tool',
                    'url_acces': 'https://audit.art.cm',
                    'icone_name': 'activity',
                    'description': 'Outil de monitoring et audit sécurité.',
                    'authorized': ['DT', 'DG']
                },
                {
                    'nom': 'Hiring Flow',
                    'url_acces': 'https://hr.art.cm',
                    'icone_name': 'users',
                    'description': 'Gestion du recrutement et des talents.',
                    'authorized': ['RH', 'DG']
                },
            ]

            for a_data in apps_data:
                auth_codes = a_data.pop('authorized')
                app, created = Application.objects.get_or_create(nom=a_data['nom'], defaults=a_data)
                if created:
                    self.stdout.write(f"Application {app.nom} créée.")
                
                for code in auth_codes:
                    DirectionApplication.objects.get_or_create(direction=directions[code], application=app)

            # 3. Création des Utilisateurs
            # Admin (Superuser)
            if not Utilisateur.objects.filter(username='admin').exists():
                admin = Utilisateur.objects.create_superuser(
                    username='admin',
                    email='admin@art.cm',
                    password='adminpassword123',
                    first_name='Admin',
                    last_name='Opale',
                    role='ADMIN',
                    direction=directions['DG']
                )
                self.stdout.write(self.style.SUCCESS("Super-utilisateur 'admin' créé (pwd: adminpassword123)."))

            # Utilisateurs par direction
            users_to_create = [
                # Technique
                {'username': 'j.dupont', 'first_name': 'Jean', 'last_name': 'Dupont', 'dir': 'DT', 'role': 'MANAGER'},
                {'username': 'm.tech', 'first_name': 'Michel', 'last_name': 'Technique', 'dir': 'DT', 'role': 'EMPLOYE'},
                # Finance
                {'username': 'a.finance', 'first_name': 'Alice', 'last_name': 'Comptable', 'dir': 'DAF', 'role': 'MANAGER'},
                {'username': 'b.budget', 'first_name': 'Bob', 'last_name': 'Budget', 'dir': 'DAF', 'role': 'EMPLOYE'},
                # RH
                {'username': 's.rh', 'first_name': 'Sarah', 'last_name': 'Recrutement', 'dir': 'RH', 'role': 'MANAGER'},
            ]

            for u_data in users_to_create:
                dir_code = u_data.pop('dir')
                username = u_data.pop('username')
                password = 'password123'
                
                if not Utilisateur.objects.filter(username=username).exists():
                    u = Utilisateur.objects.create_user(
                        username=username,
                        password=password,
                        email=f"{username}@art.cm",
                        direction=directions[dir_code],
                        **u_data
                    )
                    self.stdout.write(f"Utilisateur {username} créé (role: {u.role}, dir: {dir_code}).")

        self.stdout.write(self.style.SUCCESS('Peuplement terminé avec succès !'))
