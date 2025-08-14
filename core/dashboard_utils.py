# core/dashboard_utils.py
from datetime import date, timedelta
from django.db.models import Count, Avg, Sum,Q
from .models import Support, Client, CreditBalance

def get_dashboard_data():
    """
    Calcula y devuelve todos los datos necesarios para el dashboard.
    """
    today = date.today()

    # --- CÁLCULOS PARA LAS TARJETAS ---
    total_tickets = Support.objects.count()
    total_clients = Client.objects.count()
    tickets_today = Support.objects.filter(created_at__date=today).count()

    # Conteo de llamadas perdidas hoy
    missed_calls_today = Support.objects.filter(
        created_at__date=today,
        call_status__name='MISSED'
    ).count()

    # # Promedio de tiempo de espera para llamadas recibidas hoy
    # avg_wait_time_str = "00:00"
    # filtered_calls = Support.objects.filter(
    #     created_at__date=today,
    #     call_status__name__in=['RECEIVED', 'MISSED', 'RETURNED'],
    #     waiting_time__isnull=False,  # Excluye filas donde waiting_time es NULL
    # ).exclude(
    #     waiting_time=timedelta(seconds=0) # Excluye filas donde waiting_time es 00:00:00
    # )


    # # Calcula el promedio del tiempo de espera para las llamadas filtradas
    # if filtered_calls.exists():
    #     avg_wait_time_result = filtered_calls.aggregate(avg_wait=Avg('waiting_time'))
    #     avg_wait_time_delta = avg_wait_time_result.get('avg_wait')
        
    #     if avg_wait_time_delta:
    #         total_seconds = int(avg_wait_time_delta.total_seconds())
    #         hours = total_seconds // 3600
    #         minutes = (total_seconds % 3600) // 60
    #         seconds = total_seconds % 60
    #         avg_wait_time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    total_wait_time_result = Support.objects.filter(
        created_at__date=today,
        support_channel__is_call=True  # Consideramos todas las llamadas
    ).aggregate(total_wait=Sum('waiting_time'))
    
    total_wait_time_delta = total_wait_time_result.get('total_wait') or timedelta(0)
    
    # Formateamos el resultado a HH:MM:SS
    total_seconds = int(total_wait_time_delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    total_wait_time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    # Lógica de créditos
    # total_credit_minutes = 3000
    # balance = CreditBalance.objects.first()
    # remaining_credit = balance.remaining_minutes if balance else 0
    # consumed_minutes = total_credit_minutes - remaining_credit

    total_recargado = CreditBalance.objects.aggregate(total=Sum('remaining_minutes'))['total'] or 0

    minutos_usados = Support.objects.filter(call_status__name='RETURNED').aggregate(
        total=Sum('duration')
    )['total'] or timedelta()

    # Convertimos a minutos
    minutos_usados_min = int(minutos_usados.total_seconds() // 60)

    # Ahora sí podemos operar
    remaining_credit = max(total_recargado - minutos_usados_min, 0)
    consumed_minutes = min(minutos_usados_min, total_recargado)


    # --- CÁLCULOS PARA LOS GRÁFICOS ---
    channel_stats = list(Support.objects.values('support_channel__name')
                         .annotate(count=Count('id')).order_by('-count'))
    
    country_stats = list(Support.objects.values('client__country__name')
                         .annotate(count=Count('id')).order_by('-count'))

    return {
        'total_tickets': total_tickets,
        'total_clients': total_clients,
        'tickets_today': tickets_today,
        'missed_calls_today': missed_calls_today,
        'total_wait_time': total_wait_time_str,
        'remaining_credit': remaining_credit,
        'consumed_minutes': consumed_minutes,
        'channel_stats': channel_stats,
        'country_stats': country_stats,
    }