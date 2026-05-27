"""
catalogue/forms.py
Forms for Application management in OPALE.
"""
from django import forms
from .models import Application
from organizations.models import Direction


LUCIDE_ICON_CHOICES = [
    ('box',         '📦 box'),
    ('settings',    '⚙️  settings'),
    ('landmark',    '🏦 landmark'),
    ('mail',        '✉️  mail'),
    ('activity',    '📊 activity'),
    ('users',       '👥 users'),
    ('database',    '🗄️  database'),
    ('file-text',   '📄 file-text'),
    ('layout-dashboard', '🖥️  layout-dashboard'),
    ('globe',       '🌐 globe'),
    ('shield-check','🛡️  shield-check'),
    ('cpu',         '💻 cpu'),
    ('bar-chart-2', '📈 bar-chart-2'),
    ('calendar',    '📅 calendar'),
    ('tool',        '🔧 tool'),
    ('truck',       '🚚 truck'),
    ('zap',         '⚡ zap'),
    ('printer',     '🖨️  printer'),
    ('map',         '🗺️  map'),
    ('video',       '🎥 video'),
]


class ApplicationForm(forms.ModelForm):
    """Form for creating / editing an Application in the catalogue."""

    directions = forms.ModelMultipleChoiceField(
        queryset=Direction.objects.all().order_by('nom'),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label="Directions autorisées",
    )

    class Meta:
        model = Application
        fields = ['nom', 'url_acces', 'icone_name', 'description', 'est_actif']
        widgets = {
            'nom':         forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nom du logiciel'}),
            'url_acces':   forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://...'}),
            'icone_name':  forms.Select(choices=LUCIDE_ICON_CHOICES, attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'est_actif':   forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
        labels = {
            'nom':         'Nom du logiciel',
            'url_acces':   "URL d'accès",
            'icone_name':  'Icône',
            'description': 'Description',
            'est_actif':   'Application active',
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        if instance:
            self.fields['directions'].initial = instance.directions_autorisees.all()
