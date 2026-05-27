"""
tests/test_access_control.py
Unit tests for OPALE Service Hub — Phase 6 Access Control Validation.

Tests:
  1. Unauthorized app access is blocked and redirected to dashboard
  2. Authorized app access is logged and redirected to app URL
  3. Annuaire requires authentication
  4. Audit dashboard requires staff status
  5. LogActivite is created on every authorized app launch
"""
from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import Utilisateur
from organizations.models import Direction
from catalogue.models import Application, DirectionApplication
from audit.models import LogActivite


class AccessControlTestCase(TestCase):
    """
    Validates the direction-level access control for app launching.
    A user from Direction A must never see or launch apps restricted to Direction B.
    """

    def setUp(self):
        """Create test fixtures: 2 directions, 2 apps, 2 users."""
        self.client = Client()

        # Directions
        self.direction_a = Direction.objects.create(nom="Direction Technique", code="DT")
        self.direction_b = Direction.objects.create(nom="Direction Financière", code="DAF")

        # Applications
        self.app_a = Application.objects.create(
            nom="App Direction A",
            url_acces="https://app-a.art.cm",
            est_actif=True,
        )
        self.app_b = Application.objects.create(
            nom="App Direction B",
            url_acces="https://app-b.art.cm",
            est_actif=True,
        )

        # Assign app_a to direction_a, app_b to direction_b
        DirectionApplication.objects.create(direction=self.direction_a, application=self.app_a)
        DirectionApplication.objects.create(direction=self.direction_b, application=self.app_b)

        # Users
        self.user_a = Utilisateur.objects.create_user(
            username="employe_dt",
            password="testpass123",
            direction=self.direction_a,
            role="EMPLOYE",
        )
        self.user_b = Utilisateur.objects.create_user(
            username="employe_daf",
            password="testpass123",
            direction=self.direction_b,
            role="EMPLOYE",
        )
        self.admin_user = Utilisateur.objects.create_user(
            username="admin_art",
            password="testpass123",
            is_staff=True,
            role="ADMIN",
        )

    # ------------------------------------------------------------------
    # Test 1: Unauthorized app access is blocked
    # ------------------------------------------------------------------
    def test_unauthorized_app_access_is_blocked(self):
        """
        An employee of Direction A must NOT be able to launch an app
        that is restricted to Direction B.
        They should be silently redirected back to the dashboard.
        """
        self.client.login(username="employe_dt", password="testpass123")
        url = reverse("launch_app", args=[self.app_b.id])
        response = self.client.get(url)

        # Should redirect to dashboard, NOT to the app URL
        self.assertRedirects(response, reverse("dashboard"), fetch_redirect_response=False)

    # ------------------------------------------------------------------
    # Test 2: Authorized app access succeeds
    # ------------------------------------------------------------------
    def test_authorized_app_access_redirects_to_url(self):
        """
        An employee of Direction A CAN launch an app assigned to Direction A.
        The response should redirect to the app's external URL.
        """
        self.client.login(username="employe_dt", password="testpass123")
        url = reverse("launch_app", args=[self.app_a.id])
        response = self.client.get(url)

        # Should redirect to the actual app URL
        self.assertRedirects(response, self.app_a.url_acces, fetch_redirect_response=False)

    # ------------------------------------------------------------------
    # Test 3: Annuaire requires authentication
    # ------------------------------------------------------------------
    def test_annuaire_requires_login(self):
        """
        The company directory must redirect unauthenticated visitors to the login page.
        """
        url = reverse("annuaire")
        response = self.client.get(url)  # anonymous request

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    # ------------------------------------------------------------------
    # Test 4: Audit dashboard requires staff
    # ------------------------------------------------------------------
    def test_audit_dashboard_requires_staff(self):
        """
        A regular employee must NOT be able to access the audit dashboard.
        They should be redirected to the login/admin login page.
        """
        self.client.login(username="employe_dt", password="testpass123")
        url = reverse("audit_logs")
        response = self.client.get(url)

        # staff_member_required redirects non-staff to admin login
        self.assertEqual(response.status_code, 302)

    def test_audit_dashboard_accessible_to_staff(self):
        """
        A staff user CAN access the audit dashboard.
        """
        self.client.login(username="admin_art", password="testpass123")
        url = reverse("audit_logs")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    # ------------------------------------------------------------------
    # Test 5: LogActivite is created on authorized app launch
    # ------------------------------------------------------------------
    def test_log_created_on_authorized_launch(self):
        """
        Every authorized app launch must create a LogActivite record
        with the correct user and action string.
        """
        self.client.login(username="employe_dt", password="testpass123")
        initial_count = LogActivite.objects.count()

        url = reverse("launch_app", args=[self.app_a.id])
        self.client.get(url)

        # One log entry must have been created
        self.assertEqual(LogActivite.objects.count(), initial_count + 1)

        # Verify the log content
        log = LogActivite.objects.latest("cree_le")
        self.assertEqual(log.utilisateur, self.user_a)
        self.assertIn(self.app_a.nom, log.action)

    def test_log_created_on_unauthorized_attempt(self):
        """
        Even denied access attempts must be logged (for security monitoring).
        """
        self.client.login(username="employe_dt", password="testpass123")
        initial_count = LogActivite.objects.count()

        url = reverse("launch_app", args=[self.app_b.id])
        self.client.get(url)

        # A denial log must also be created
        self.assertEqual(LogActivite.objects.count(), initial_count + 1)
        log = LogActivite.objects.latest("cree_le")
        self.assertIn("REFUSÉ", log.action)
