from django.db import models
from organizations.models import Direction

class Application(models.Model):
    nom = models.CharField(max_length=100, verbose_name="Nom du logiciel")
    url_acces = models.URLField(verbose_name="Lien d'accès")
    icone_name = models.CharField(max_length=50, default="box", help_text="Nom de l'icône Lucide (ex: box, activity, users)")
    description = models.TextField(null=True, blank=True)
    est_actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    directions_autorisees = models.ManyToManyField(
        Direction, 
        through='DirectionApplication',
        related_name='applications'
    )

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Application"
        verbose_name_plural = "Applications"

class DirectionApplication(models.Model):
    direction = models.ForeignKey(Direction, on_delete=models.CASCADE)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    date_attribution = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('direction', 'application')
        verbose_name = "Habilitation"
        verbose_name_plural = "Habilitations"
