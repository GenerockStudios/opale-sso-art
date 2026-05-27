from django.contrib.auth.models import AbstractUser
from django.db import models
from organizations.models import Direction

class Utilisateur(AbstractUser):
    ROLE_CHOICES = (
        ('EMPLOYE', 'Employé'),
        ('MANAGER', 'Manager'),
        ('ADMIN', 'Administrateur'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='EMPLOYE')
    direction = models.ForeignKey(
        Direction, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='utilisateurs'
    )
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
