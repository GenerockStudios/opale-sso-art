from django import forms
from .models import Direction

class DirectionForm(forms.ModelForm):
    """Form for creating / editing a Direction in OPALE."""

    class Meta:
        model = Direction
        fields = ['nom', 'code', 'description']
        widgets = {
            'nom':         forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nom complet de la direction'}),
            'code':        forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Code (ex: DT, DAF)'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Description optionnelle...'}),
        }
        labels = {
            'nom':         'Nom de la direction',
            'code':        'Code / Triglyphe',
            'description': 'Description',
        }
