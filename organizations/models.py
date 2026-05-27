from django.db import models

class Direction(models.Model):
    nom = models.CharField(max_length=150, unique=True, verbose_name="Nom de la direction")
    code = models.CharField(max_length=10, unique=True, null=True, blank=True, verbose_name="Code (ex: DT, DAF)")
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} ({self.code})" if self.code else self.nom

    class Meta:
        verbose_name = "Direction"
        verbose_name_plural = "Directions"
