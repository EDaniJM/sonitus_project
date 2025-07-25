from django.utils import timezone
from django.db import models

# Create your models here.

# Modelo para la tabla t_country
class Country(models.Model):
    name = models.CharField(max_length=100)
    phone_code = models.CharField(max_length=50, blank=True)
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Countries"

# Modelo para la tabla t_client_type
class ClientType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Client type"
        verbose_name_plural = "Clients type"

# Modelo para la tabla t_support_channel
class SupportChannel(models.Model):
    name = models.CharField(max_length=100)
    is_call = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Support Channel"
        verbose_name_plural = "Support Channels"

# Modelo para la tabla t_client
class Client(models.Model):
    name = models.CharField(max_length=60)
    email = models.EmailField(max_length=60, blank=True,unique=True,null=True) # unique=True para evitar emails duplicados
    phone = models.CharField(max_length=30, blank=True, unique=True, null=True) # blank=True hace el campo opcional

    # Relaciones (Foreign Keys)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    client_type = models.ForeignKey(ClientType, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"


class CallStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Call Status"
        verbose_name_plural = "Call Statuses"

class CreditBalance(models.Model):
    remaining_minutes = models.IntegerField(default=3000)

    def __str__(self):
        return f"{self.remaining_minutes} minutos restantes"


# Modelo para la tabla t_support
class Support(models.Model):


    # Relaciones
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    support_channel = models.ForeignKey(SupportChannel, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Detalles del ticket
    problem_description = models.TextField()
    solution_description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    call_status = models.ForeignKey(
        CallStatus, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True
    )

    # IDs externos (opcionales)
    kerberus_id = models.CharField(max_length=100, blank=True)
    freshdesk_ticket = models.CharField(max_length=100, blank=True)
    
    # Tiempos (usando DurationField)
    waiting_time = models.DurationField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Primero, guarda el objeto Support como siempre
        super().save(*args, **kwargs)

        # Ahora, la lógica del crédito
        # Verificamos si el status es 'RETURNED' y si hay una duración
        if self.call_status and self.call_status.name == 'RETURNED' and self.duration:
            # Obtenemos el único registro de saldo que existe
            balance = CreditBalance.objects.first()
            if balance:
                # Calculamos la duración de esta llamada en minutos
                consumed = self.duration.total_seconds() / 60
                
                # Descontamos y nos aseguramos de que no sea negativo
                balance.remaining_minutes = max(0, balance.remaining_minutes - consumed)
                balance.save()
    
    def __str__(self):
        return f"Ticket de soporte para {self.client.name} - {self.created_at.strftime('%Y-%m-%d')}"

    class Meta:
        verbose_name = "Support"
        verbose_name_plural = "Supports"

