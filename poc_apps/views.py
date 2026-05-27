import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.test import RequestFactory
from accounts.views import sso_verify_view
from audit.logic import log_activite

# ── HABILITATIONS DES APPLICATIONS ─────────────────────────────────────────
APP_PERMISSIONS = {
    'zimbra_mail': ['DT', 'DAF', 'RH', 'DRH', 'DG'],
    'telecom_licences': ['DT', 'DAF', 'DG'],
    'spectre_monitoring': ['DT', 'DG'],
}

def get_poc_session(request, app_name):
    """
    Récupère la session locale simulée pour une application PoC donnée.
    """
    return request.session.get('poc_sessions', {}).get(app_name)


# ── 1. ZIMBRA WEBMAIL SIMULATION ───────────────────────────────────────────
def zimbra_mail_view(request):
    app_name = 'zimbra_mail'
    session_data = get_poc_session(request, app_name)
    
    if not session_data:
        # SSO Handshake : Rediriger vers le portail Opale pour obtenir un jeton
        callback_url = f"/apps/sso-callback/?app={app_name}"
        return redirect(f"/accounts/sso/authorize/?app={app_name}&next={callback_url}")

    # Données simulées d'e-mails professionnels par direction
    dir_code = session_data.get('direction_code', 'DG')
    mails_db = {
        'DT': [
            {"from": "directeur.technique@art.cm", "subject": "Audit de qualité de service MTN/Orange", "date": "Aujourd'hui, 09:15", "body": "Bonjour l'équipe, merci de préparer les équipements de mesure pour la campagne de test à Douala de la semaine prochaine."},
            {"from": "superviseur.spectre@art.cm", "subject": "Alerte brouillage FM - Yaoundé 98.1 MHz", "date": "Hier, 16:45", "body": "Nous détectons une émission pirate sur la fréquence 98.1 MHz dans la zone d'Omnisports. À inspecter rapidement."}
        ],
        'DAF': [
            {"from": "chef.comptable@art.cm", "subject": "Clôture des comptes de redevances 2025", "date": "Aujourd'hui, 11:30", "body": "Rappel pour la réconciliation des paiements de spectre de Camtel pour le troisième trimestre. Le dossier doit être transmis demain."},
            {"from": "recouvrement@art.cm", "subject": "Paiement pénalités Orange Cameroun", "date": "Il y a 2 jours", "body": "Le virement des pénalités de retard de paiement a été reçu sur notre compte BGFI. Veuillez émettre la quittance."}
        ],
        'RH': [
            {"from": "directeur.rh@art.cm", "subject": "Campagne d'évaluation annuelle 2026", "date": "Aujourd'hui, 08:00", "body": "Bonjour à tous, la plateforme d'évaluation annuelle est ouverte. Tous les managers doivent finaliser les entretiens avant le 15 juin."},
            {"from": "formation@art.cm", "subject": "Formation Cybersécurité et Réseaux 5G", "date": "18 Mai", "body": "Félicitations, votre demande de formation sur la sécurité des réseaux coeurs 5G a été approuvée par la Direction Générale."}
        ],
        'DG': [
            {"from": "ministere.postes@minpostel.gov.cm", "subject": "Plan stratégique Cameroun Numérique 2030", "date": "Hier, 14:00", "body": "Monsieur le Directeur Général, le Premier Ministère sollicite le rapport de contribution de l'ART sur le déploiement de la fibre optique nationale."},
            {"from": "secretaire.general@art.cm", "subject": "Ordre du jour du Conseil d'Administration", "date": "Il y a 3 jours", "body": "La session ordinaire du conseil d'administration se tiendra le 28 mai. Les documents préparatoires sont joints à ce courriel."}
        ]
    }
    
    # Récupérer les mails correspondants à la direction de l'utilisateur ou par défaut de la DG
    mails = mails_db.get(dir_code, mails_db['DG'])
    
    return render(request, 'poc_apps/webmail.html', {
        'user_session': session_data,
        'mails': mails,
        'app_name': app_name,
    })


# ── 2. SUIVI DES LICENCES TÉLÉCOMS (ART CAMEROUN) ──────────────────────────
def telecom_licences_view(request):
    app_name = 'telecom_licences'
    session_data = get_poc_session(request, app_name)
    
    if not session_data:
        callback_url = f"/apps/sso-callback/?app={app_name}"
        return redirect(f"/accounts/sso/authorize/?app={app_name}&next={callback_url}")

    # Données simulées des licences des opérateurs télécoms au Cameroun
    licences = [
        {"operateur": "MTN Cameroon", "type": "4G/5G Mobile & Fixe", "date_octroi": "11/03/2015", "expire": "11/03/2030", "statut": "Active", "redevance": "4.5 Mrd FCFA", "color": "success"},
        {"operateur": "Orange Cameroun", "type": "4G/5G Mobile & Fixe", "date_octroi": "11/03/2015", "expire": "11/03/2030", "statut": "Active", "redevance": "4.2 Mrd FCFA", "color": "success"},
        {"operateur": "Camtel (National)", "type": "3G/4G Mobile, Fixe & Transport", "date_octroi": "04/03/2020", "expire": "04/03/2035", "statut": "Active", "redevance": "2.8 Mrd FCFA", "color": "success"},
        {"operateur": "Viettel (Nexttel)", "type": "3G Mobile", "date_octroi": "12/12/2012", "expire": "12/12/2027", "statut": "En réévaluation", "redevance": "1.5 Mrd FCFA", "color": "warning"},
    ]

    return render(request, 'poc_apps/licences.html', {
        'user_session': session_data,
        'licences': licences,
        'app_name': app_name,
    })


# ── 3. SUPERVISION DU SPECTRE RADIOÉLECTRIQUE (ART) ────────────────────────
def spectre_monitoring_view(request):
    app_name = 'spectre_monitoring'
    session_data = get_poc_session(request, app_name)
    
    if not session_data:
        callback_url = f"/apps/sso-callback/?app={app_name}"
        return redirect(f"/accounts/sso/authorize/?app={app_name}&next={callback_url}")

    # Données de fréquences et alertes du spectre au Cameroun
    stations = [
        {"ville": "Yaoundé (Mont Fébé)", "frequence": "100.3 MHz (FM)", "utilisation": "Radiodiffusion", "statut": "Conforme", "color": "success", "interferences": "Aucune"},
        {"ville": "Douala (Bonanjo)", "frequence": "1800 MHz (LTE)", "utilisation": "Réseau Mobile MTN", "statut": "Alerte Brouillage", "color": "danger", "interferences": "Forte (Émetteur non autorisé détecté à Deido)"},
        {"ville": "Garoua (Plateau)", "frequence": "900 MHz (GSM)", "utilisation": "Réseau Mobile Orange", "statut": "Conforme", "color": "success", "interferences": "Aucune"},
        {"ville": "Limbe (Bota)", "frequence": "2.4 GHz (WiFi)", "utilisation": "Bande libre", "statut": "Optimisé", "color": "primary", "interferences": "Modérée"},
    ]

    return render(request, 'poc_apps/spectre.html', {
        'user_session': session_data,
        'stations': stations,
        'app_name': app_name,
    })


# ── 4. SSO CALLBACK HANDLER (SERVICE PROVIDER HANDSHAKE) ──────────────────
def sso_callback_view(request):
    """
    Callback SSO commun aux applications PoC.
    Reçoit le jeton d'autorisation depuis le portail, le valide en interrogeant
    l'IdP (programmatiquement), vérifie les habilitations d'accès de la direction,
    et enregistre le résultat en session locale de l'application cliente.
    """
    token = request.GET.get('token')
    app_name = request.GET.get('app')

    if not token or not app_name:
        return render(request, 'poc_apps/sso_error.html', {
            'error': "Paramètres SSO manquants (token ou application non spécifié)."
        })

    # Appel programmatique de sso_verify_view pour simuler l'appel API Web SSO
    factory = RequestFactory()
    mock_request = factory.get(f'/accounts/sso/verify/?token={token}')
    # Transmettre la session actuelle pour conserver le contexte si nécessaire
    mock_request.session = request.session
    mock_request.user = request.user
    
    try:
        response = sso_verify_view(mock_request)
        data = json.loads(response.content.decode('utf-8'))
    except Exception as e:
        return render(request, 'poc_apps/sso_error.html', {
            'error': f"Échec technique de vérification de jeton : {str(e)}"
        })

    if not data.get('valid'):
        return render(request, 'poc_apps/sso_error.html', {
            'error': data.get('error', "Jeton invalide ou expiré.")
        })

    # Vérification des habilitations (Role-based / Attribute-based Access Control)
    user_direction_code = data.get('direction_code', 'DG')
    allowed_directions = APP_PERMISSIONS.get(app_name, [])

    if user_direction_code not in allowed_directions:
        # L'utilisateur appartient à une direction non autorisée pour cette application
        log_activite(
            request,
            f"Accès Refusé SSO — Application : {app_name}",
            {
                "username": data.get('username'),
                "direction": data.get('direction'),
                "required_directions": allowed_directions,
                "status": "denied"
            }
        )
        return render(request, 'poc_apps/sso_error.html', {
            'error': f"Accès non autorisé pour votre Direction ({data.get('direction')}). Cette application est réservée à d'autres services de l'ART.",
            'unauthorized': True,
            'user_session': data,
            'app_name': app_name
        })

    # Si valide et autorisé, on initialise la session locale de l'application PoC
    if 'poc_sessions' not in request.session:
        request.session['poc_sessions'] = {}
        
    request.session['poc_sessions'][app_name] = data
    request.session.modified = True

    # Consigner l'établissement réussi de session applicative
    log_activite(
        request,
        f"Session Applicative Établie via SSO — Application : {app_name}",
        {
            "username": data.get('username'),
            "direction": data.get('direction'),
            "app_name": app_name,
            "status": "success"
        }
    )

    # Redirection finale vers l'application PoC autorisée
    target_urls = {
        'zimbra_mail': 'zimbra_mail',
        'telecom_licences': 'telecom_licences',
        'spectre_monitoring': 'spectre_monitoring'
    }
    
    return redirect(target_urls.get(app_name, 'dashboard'))


# ── 5. LOCAL SSO LOGOUT FOR DEMO PURPOSES ─────────────────────────────────
def poc_logout_view(request):
    """
    Déconnexion locale d'une ou toutes les applications PoC.
    Permet de nettoyer la session PoC pour rejouer l'animation de connexion SSO.
    """
    app_name = request.GET.get('app')
    
    if 'poc_sessions' in request.session:
        if app_name and app_name in request.session['poc_sessions']:
            del request.session['poc_sessions'][app_name]
            request.session.modified = True
            log_activite(request, f"Déconnexion locale — Application : {app_name}")
        else:
            # Tout déconnecter
            request.session['poc_sessions'] = {}
            request.session.modified = True
            log_activite(request, "Déconnexion locale globale de toutes les applications PoC")

    # Si 'next' est fourni, on y va
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)

    return redirect('dashboard')
