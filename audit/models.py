from django.db import models
from django.conf import settings

class LogActivite(models.Model):
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Utilisateur"
    )
    action = models.CharField(max_length=255, verbose_name="Action effectuée")
    ip_address = models.CharField(max_length=45, null=True, blank=True, verbose_name="Adresse IP")
    details = models.JSONField(null=True, blank=True, verbose_name="Détails (JSON)")
    cree_le = models.DateTimeField(auto_now_add=True, verbose_name="Date de l'action")

    def __str__(self):
        user_str = self.utilisateur.username if self.utilisateur else "Système"
        return f"{user_str} - {self.action} ({self.cree_le:%d/%m/%Y %H:%M})"

    class Meta:
        verbose_name = "Log d'activité"
        verbose_name_plural = "Logs d'activité"
        ordering = ['-cree_le']
