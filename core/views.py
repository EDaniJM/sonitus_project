import json
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .forms import SupportForm, ClientForm
from .models import Client, Support,SupportChannel, Country, CreditBalance
from django.db.models import Count, Sum
from django.db.models.functions import TruncYear, TruncMonth, TruncDay, TruncHour 
from datetime import date, datetime, timedelta
import calendar
from django.utils import timezone
# Create your views here.


def dashboard_view(request):
    # --- Estadísticas que ya teníamos ---
    total_tickets = Support.objects.count()
    total_clients = Client.objects.count()
    tickets_today = Support.objects.filter(created_at__date=date.today()).count()

    # --- Datos para el gráfico de dona (sin cambios) ---
    channel_stats_queryset = Support.objects.values('support_channel__name').annotate(
        count=Count('id')
    ).order_by('-count')
    channel_stats_list = list(channel_stats_queryset)

    # --- NUEVA LÓGICA PARA EL GRÁFICO DE LÍNEAS ---
    # 1. Obtenemos los datos de la BD: contamos las llamadas por mes y por estado
    call_stats = Support.objects \
        .filter(call_status__name__in=['RECEIVED', 'MISSED', 'RETURNED']) \
        .annotate(month=TruncMonth('created_at')) \
        .values('month', 'call_status__name') \
        .annotate(count=Count('id')) \
        .order_by('month')

    # 2. Procesamos los datos para que Chart.js los entienda
    line_chart_labels = [calendar.month_abbr[i] for i in range(1, 13)] # ["Jan", "Feb", ...]
    received_calls_data = [0] * 12 # [0, 0, 0, ...]
    missed_calls_data = [0] * 12   # [0, 0, 0, ...]
    returned_calls_data = [0] * 12

    for stat in call_stats:
        # El mes es un objeto datetime, obtenemos el número del mes (1-12)
        month_index = stat['month'].month - 1
        if stat['call_status__name'] == 'RECEIVED':
            received_calls_data[month_index] = stat['count']
        elif stat['call_status__name'] == 'MISSED':
            missed_calls_data[month_index] = stat['count']
        elif stat['call_status__name'] == 'RETURNED':
            returned_calls_data[month_index] = stat['count']
    
    total_credit_minutes = 3000
    balance = CreditBalance.objects.first()
    remaining_credit = balance.remaining_minutes if balance else 0
    consumed_minutes = total_credit_minutes - remaining_credit


    # --- Contexto Final ---
    context = {
        'total_tickets': total_tickets,
        'total_clients': total_clients,
        'tickets_today': tickets_today,
        'channel_stats': channel_stats_list,
        'line_chart_data': {
            'labels': line_chart_labels,
            'received': received_calls_data,
            'missed': missed_calls_data,
            'returned': returned_calls_data,
        },
        'remaining_credit': remaining_credit,
        'consumed_minutes': consumed_minutes
    }
    return render(request, 'dashboard.html', context)


def support_form_view(request):
    # Preparamos los datos para el JavaScript
    channel_call_data = {channel.id: channel.is_call for channel in SupportChannel.objects.all()}
    country_codes_data = {str(country.id): country.phone_code for country in Country.objects.all()}
    
    client_form_invalid = False

    # Instanciamos los formularios. Estarán vacíos a menos que sea un POST.
    support_form = SupportForm()
    client_form = ClientForm()

    if request.method == 'POST':
        if 'submit_support_form' in request.POST:
            support_form = SupportForm(request.POST) # Llenamos con datos
            if support_form.is_valid():
                support_form.save()
                return redirect('core:dashboard')
        
        elif 'submit_client_form' in request.POST:
            client_form = ClientForm(request.POST) # Llenamos con datos
            if client_form.is_valid():
                client_form.save()
                return redirect('core:forms')
            else:
                client_form_invalid = True
    
    context = {
        'support_form': support_form,
        'client_form': client_form,
        'client_form_invalid': client_form_invalid,
        'channel_call_data_json': json.dumps(channel_call_data),
        'country_codes_json': json.dumps(country_codes_data),
    }
    return render(request, 'forms.html', context)

def reports_view(request):
    context = {}
    return render(request, 'reports.html', context)

def test_page_view(request):
    return render(request, 'test_page.html')

def client_search_view(request):
    """
    Vista que busca clientes por nombre y devuelve los resultados en formato JSON
    para ser consumidos por Select2.
    """
    # 1. Obtenemos el término de búsqueda de los parámetros GET
    term = request.GET.get('term', '')
    
    # 2. Filtramos los clientes cuyo nombre contenga el término de búsqueda (ignorando mayúsculas/minúsculas)
    #    y limitamos los resultados a los primeros 10 para no sobrecargar.
    clients = Client.objects.filter(name__icontains=term)[:10]
    
    # 3. Formateamos los resultados en la estructura que Select2 espera: una lista de diccionarios con 'id' y 'text'.
    results = []
    for client in clients:
        results.append({
            'id': client.id,
            'text': client.name,
            'email': client.email,
            'phone': client.phone,
            'client_type': client.client_type.name if client.client_type else 'N/A',
            'country': client.country.name if client.country else 'N/A'
        })
        
    # 4. Devolvemos la lista de resultados como una respuesta JSON.
    return JsonResponse({'results': results})

def call_stats_chart_view(request):
    period = request.GET.get('period', 'month')
    
    try:
        year = int(request.GET.get('year', datetime.now().year))
        month = int(request.GET.get('month', datetime.now().month))
        day = int(request.GET.get('day', datetime.now().day))
    except (ValueError, TypeError):
        today = datetime.now()
        year, month, day = today.year, today.month, today.day

    target_date = datetime(year, month, day)
    
    base_query = Support.objects.filter(call_status__name__in=['RECEIVED', 'MISSED', 'RETURNED'])

    # --- LÓGICA PARA EL PERÍODO 'day' (CORREGIDA Y AISLADA) ---
    if period == 'day':
        daily_query = base_query.filter(created_at__date=target_date.date())
        
        labels = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]
        data_map = {label: {'RECEIVED': 0, 'MISSED': 0, 'RETURNED': 0} for label in labels}

        for call in daily_query:
            local_time = timezone.localtime(call.created_at)
            
            if call.call_status: # Asegurarse de que el estado no sea nulo
                minute_bucket = "00" if local_time.minute < 30 else "30"
                hour_bucket = f"{local_time.hour:02d}:{minute_bucket}"
                if hour_bucket in data_map:
                    # CORREGIDO: Es 'call.call_status.name', no 'call.created_at.call_status.name'
                    data_map[hour_bucket][call.call_status.name] += 1
        
        # Preparamos los datos y los devolvemos directamente desde aquí
        received_data = [data_map[label]['RECEIVED'] for label in labels]
        missed_data = [data_map[label]['MISSED'] for label in labels]
        returned_data = [data_map[label]['RETURNED'] for label in labels]
        
        return JsonResponse({
            'labels': labels, 'received': received_data,
            'missed': missed_data, 'returned': returned_data,
        })

    # --- LÓGICA COMPARTIDA PARA 'year' Y 'month' ---
    if period == 'year':
        trunc_func = TruncMonth('created_at')
        date_format = "%b"
        base_query = base_query.filter(created_at__year=target_date.year)
        labels = [calendar.month_abbr[i] for i in range(1, 13)]
    else: # 'month'
        trunc_func = TruncDay('created_at')
        date_format = "%b %d"
        first_day = target_date.replace(day=1)
        _, num_days = calendar.monthrange(target_date.year, target_date.month)
        last_day = target_date.replace(day=num_days)
        base_query = base_query.filter(created_at__range=[first_day, last_day])
        labels = [(first_day + timedelta(days=i)).strftime(date_format) for i in range(num_days)]
    
    call_stats = base_query \
        .annotate(period_start=trunc_func) \
        .values('period_start', 'call_status__name') \
        .annotate(count=Count('id')) \
        .order_by('period_start')

    data_map = {label: {'RECEIVED': 0, 'MISSED': 0, 'RETURNED': 0} for label in labels}
    for stat in call_stats:
        label = stat['period_start'].strftime(date_format)
        if label in data_map:
            data_map[label][stat['call_status__name']] = stat['count']
    
    received_data = [data_map[label]['RECEIVED'] for label in labels]
    missed_data = [data_map[label]['MISSED'] for label in labels]
    returned_data = [data_map[label]['RETURNED'] for label in labels]

    return JsonResponse({
        'labels': labels, 'received': received_data,
        'missed': missed_data, 'returned': returned_data,
    })

def recharge_credit_view(request):
    if request.method == 'POST':
        # Buscamos el saldo, lo reseteamos a 3000 y lo guardamos
        balance = CreditBalance.objects.first()
        if balance:
            balance.remaining_minutes += 3000 
            balance.save()
    # Redirigimos siempre al dashboard
    return redirect('core:dashboard')