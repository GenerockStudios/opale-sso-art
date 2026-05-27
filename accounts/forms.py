"""
accounts/forms.py
Forms for user profile management in OPALE.
"""
from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from .models import Utilisateur
from organizations.models import Direction


class ProfilForm(forms.ModelForm):
    """Form to update a user's basic info: full name and email."""

    first_name = forms.CharField(
        label="Prénom",
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Votre prénom',
            'autocomplete': 'given-name',
        }),
    )
    last_name = forms.CharField(
        label="Nom de famille",
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Votre nom de famille',
            'autocomplete': 'family-name',
        }),
    )
    email = forms.EmailField(
        label="Adresse e-mail",
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'votre@email.art.cm',
            'autocomplete': 'email',
        }),
    )

    class Meta:
        model = Utilisateur
        fields = ['first_name', 'last_name', 'email']


class OpalePasswordChangeForm(PasswordChangeForm):
    """Styled password change form inheriting from Django's secure implementation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-input'})
        self.fields['old_password'].widget.attrs['placeholder'] = 'Mot de passe actuel'
        self.fields['new_password1'].widget.attrs['placeholder'] = 'Nouveau mot de passe'
        self.fields['new_password2'].widget.attrs['placeholder'] = 'Confirmer le nouveau mot de passe'
        self.fields['old_password'].label = 'Mot de passe actuel'
        self.fields['new_password1'].label = 'Nouveau mot de passe'
        self.fields['new_password2'].label = 'Confirmation'


# ---------------------------------------------------------------------------
# Admin CRUD Forms
# ---------------------------------------------------------------------------

class UtilisateurAdminForm(forms.ModelForm):
    """Form for creating / editing a user from the admin panel."""

    password = forms.CharField(
        label="Mot de passe",
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Laisser vide pour ne pas modifier',
            'autocomplete': 'new-password',
        }),
        help_text="Laisser vide pour conserver le mot de passe actuel.",
    )

    class Meta:
        model = Utilisateur
        fields = ['username', 'first_name', 'last_name', 'email', 'direction', 'role', 'is_active', 'is_staff']
        widgets = {
            'username':   forms.TextInput(attrs={'class': 'form-input'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-input'}),
            'email':      forms.EmailInput(attrs={'class': 'form-input'}),
            'direction':  forms.Select(attrs={'class': 'form-input'}),
            'role':       forms.Select(attrs={'class': 'form-input'}),
            'is_active':  forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'is_staff':   forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
        labels = {
            'username':   'Identifiant',
            'first_name': 'Prénom',
            'last_name':  'Nom de famille',
            'email':      'Adresse e-mail',
            'direction':  'Direction',
            'role':       'Rôle',
            'is_active':  'Compte actif',
            'is_staff':   'Accès administration',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user

