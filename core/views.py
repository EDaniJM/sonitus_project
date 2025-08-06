import json
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.db.models import Count, Sum
from django.db.models.functions import TruncYear, TruncMonth, TruncDay, TruncHour
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
# Para proteger vistas
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from django.template.loader import render_to_string
from django.http import HttpResponse

from .forms import SupportForm, ClientForm, CompanyForm
from .models import Client, Support, SupportChannel, Country, CreditBalance

from datetime import date, datetime, timedelta
import calendar

from .utils.ranges import get_period_range, build_filename
from .utils.pdf import render_to_pdf

import json
import requests
import base64
from urllib.parse import urlencode

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .dashboard_utils import get_dashboard_data

# Error 403
def permission_denied_view(request, exception):
    """
    Vista personalizada para manejar los errores 403 (Forbidden).
    """
    return render(request, '403.html', status=403)

# Autenticación

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirige al dashboard si el login es exitoso
                return redirect('core:dashboard')
    else:
        form = AuthenticationForm()

    # Si es GET o el form es inválido, muestra la página de login
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    # Redirige a la página de login tras cerrar sesión
    return redirect('core:login')

# Vistas de la aplicación


# @login_required
# def dashboard_view(request):
#     # --- Estadísticas que ya teníamos ---
#     total_tickets = Support.objects.count()
#     total_clients = Client.objects.count()
#     tickets_today = Support.objects.filter(
#         created_at__date=date.today()).count()

#     # --- Datos para el gráfico de dona (sin cambios) ---
#     channel_stats_queryset = Support.objects.values('support_channel__name').annotate(
#         count=Count('id')
#     ).order_by('-count')
#     channel_stats_list = list(channel_stats_queryset)

#     # --- LÓGICA PARA EL GRÁFICO DE LÍNEAS ---
#     # 1. Obtenemos los datos de la BD: contamos las llamadas por mes y por estado
#     call_stats = Support.objects \
#         .filter(call_status__name__in=['RECEIVED', 'MISSED', 'RETURNED']) \
#         .annotate(month=TruncMonth('created_at')) \
#         .values('month', 'call_status__name') \
#         .annotate(count=Count('id')) \
#         .order_by('month')

#     # 2. Procesamos los datos para que Chart.js los entienda
#     line_chart_labels = [calendar.month_abbr[i]
#                         for i in range(1, 13)]  # ["Jan", "Feb", ...]
#     received_calls_data = [0] * 12  # [0, 0, 0, ...]
#     missed_calls_data = [0] * 12   # [0, 0, 0, ...]
#     returned_calls_data = [0] * 12

#     for stat in call_stats:
#         # El mes es un objeto datetime, obtenemos el número del mes (1-12)
#         month_index = stat['month'].month - 1
#         if stat['call_status__name'] == 'RECEIVED':
#             received_calls_data[month_index] = stat['count']
#         elif stat['call_status__name'] == 'MISSED':
#             missed_calls_data[month_index] = stat['count']
#         elif stat['call_status__name'] == 'RETURNED':
#             returned_calls_data[month_index] = stat['count']

#     total_credit_minutes = 3000
#     balance = CreditBalance.objects.first()
#     remaining_credit = balance.remaining_minutes if balance else 0
#     consumed_minutes = total_credit_minutes - remaining_credit

#     country_stats = Support.objects.values(
#         'client__country__name'  # Agrupamos por el nombre del país del cliente
#     ).annotate(
#         count=Count('id')        # Contamos los soportes en cada grupo
#     ).order_by('-count')

#     country_stats_list = list(country_stats)

#     # --- Contexto Final ---
#     context = {
#         'total_tickets': total_tickets,
#         'total_clients': total_clients,
#         'tickets_today': tickets_today,
#         'channel_stats': channel_stats_list,
#         'line_chart_data': {
#             'labels': line_chart_labels,
#             'received': received_calls_data,
#             'missed': missed_calls_data,
#             'returned': returned_calls_data,
#         },
#         'remaining_credit': remaining_credit,
#         'consumed_minutes': consumed_minutes,
#         'country_stats': country_stats_list,
#     }
#     return render(request, 'dashboard.html', context)
@login_required
def dashboard_view(request):
    """
    Prepara los datos iniciales para la carga del dashboard.
    Las actualizaciones posteriores se manejan vía WebSocket.
    """
    # Usamos la función centralizada para obtener todos los datos necesarios
    initial_data = get_dashboard_data()
    
    # El gráfico de líneas ahora se carga dinámicamente desde su propia API,
    # por lo que no necesitamos calcular sus datos aquí.
    context = {
        'total_tickets': initial_data.get('total_tickets'),
        'total_clients': initial_data.get('total_clients'),
        'tickets_today': initial_data.get('tickets_today'),
        'channel_stats': initial_data.get('channel_stats'),
        'remaining_credit': initial_data.get('remaining_credit'),
        'consumed_minutes': initial_data.get('consumed_minutes'),
        'country_stats': initial_data.get('country_stats'),
        'missed_calls_today' : initial_data.get('missed_calls_today'),
        'avg_wait_time' : initial_data.get('avg_wait_time'),
    }
    return render(request, 'dashboard.html', context)


# El formulario solo debe ser accesible para quienes pueden "añadir" soportes.
# Esto bloqueará el acceso a los Supervisores.
# @login_required
# @permission_required('core.add_support', raise_exception=True)
# def support_form_view(request):
#     if request.method == 'POST':
#         if 'submit_support_form' in request.POST:
#             support_form = SupportForm(request.POST)
#             if support_form.is_valid():
#                 support_form.save()
                
#                 # --- INICIO: NOTIFICACIÓN EN TIEMPO REAL ---
#                 channel_layer = get_channel_layer()
#                 async_to_sync(channel_layer.group_send)(
#                     "dashboard",
#                     {
#                         "type": "dashboard.update",
#                         "data": get_dashboard_data(),
#                     }
#                 )
#                 # --- FIN: NOTIFICACIÓN ---
                
#                 return redirect('core:dashboard')
#     # Preparamos los datos para el JavaScript
#     channel_call_data = {
#         channel.id: channel.is_call for channel in SupportChannel.objects.all()}
#     country_codes_data = {
#         country.id: country.phone_code for country in Country.objects.all()}

#     # Banderas para los errores de los modales
#     client_form_invalid = False
#     company_form_invalid = False

#     # Instanciamos los formularios. Estarán vacíos a menos que sea un POST.
#     support_form = SupportForm()
#     client_form = ClientForm()
#     company_form = CompanyForm()

#     if request.method == 'POST':
#         if 'submit_support_form' in request.POST:
#             support_form = SupportForm(request.POST)
#             if support_form.is_valid():
#                 support_form.save()
#                 return redirect('core:dashboard')

#         elif 'submit_client_form' in request.POST:
#             client_form = ClientForm(request.POST)
#             if client_form.is_valid():
#                 client_form.save()
#                 return redirect('core:forms')
#             else:
#                 client_form_invalid = True

#         elif 'submit_company_form' in request.POST:
#             company_form = CompanyForm(request.POST)
#             if company_form.is_valid():
#                 # La variable 'company' se crea y usa aquí dentro
#                 company = company_form.save()
#                 if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#                     return JsonResponse({'id': company.id, 'name': company.name})
#                 return redirect('core:forms')
#             else:
#                 company_form_invalid = True

#     context = {
#         'support_form': support_form,
#         'client_form': client_form,
#         'company_form': company_form,
#         'client_form_invalid': client_form_invalid,
#         'company_form_invalid': company_form_invalid,
#         'channel_call_data_json': json.dumps(channel_call_data),
#         'country_codes_json': json.dumps(country_codes_data),
#     }
#     return render(request, 'forms.html', context)

@login_required
@permission_required('core.add_support', raise_exception=True)
def support_form_view(request):
    # Preparamos los datos para el JavaScript que se usarán tanto en GET como en POST
    channel_call_data = {channel.id: channel.is_call for channel in SupportChannel.objects.all()}
    country_codes_data = {country.id: country.phone_code for country in Country.objects.all()}
    
    # Banderas para los errores de los modales
    client_form_invalid = False
    company_form_invalid = False

    # Instanciamos los formularios. Estarán vacíos a menos que sea un POST.
    support_form = SupportForm()
    client_form = ClientForm()
    company_form = CompanyForm()

    if request.method == 'POST':
        if 'submit_support_form' in request.POST:
            support_form = SupportForm(request.POST)
            if support_form.is_valid():
                support_form.save()
                
                # Disparador: Se creó un nuevo soporte
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)("dashboard", {"type": "dashboard.update", "data": get_dashboard_data()})
                
                return redirect('core:dashboard')
        
        elif 'submit_client_form' in request.POST:
            client_form = ClientForm(request.POST)
            if client_form.is_valid():
                client_form.save()

                # Disparador: Se creó un nuevo cliente
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)("dashboard", {"type": "dashboard.update", "data": get_dashboard_data()})

                return redirect('core:forms')
            else:
                client_form_invalid = True
        
        elif 'submit_company_form' in request.POST:
            company_form = CompanyForm(request.POST)
            if company_form.is_valid():
                company = company_form.save()
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'id': company.id, 'name': company.name})
                return redirect('core:forms')
            else:
                company_form_invalid = True
        
        elif 'submit_client_form' in request.POST:
            client_form = ClientForm(request.POST)
            if client_form.is_valid():
                client_form.save()
                return redirect('core:forms')
            else:
                client_form_invalid = True
        
        elif 'submit_company_form' in request.POST:
            company_form = CompanyForm(request.POST)
            if company_form.is_valid():
                company = company_form.save()
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'id': company.id, 'name': company.name})
                return redirect('core:forms')
            else:
                company_form_invalid = True
    
    context = {
        'support_form': support_form,
        'client_form': client_form,
        'company_form': company_form,
        'client_form_invalid': client_form_invalid,
        'company_form_invalid': company_form_invalid,
        'channel_call_data_json': json.dumps(channel_call_data),
        'country_codes_json': json.dumps(country_codes_data),
    }
    return render(request, 'forms.html', context)


@login_required
@permission_required('core.view_support', raise_exception=True)
def reports_view(request):
    context = {}
    return render(request, 'reports.html', context)


@login_required
def report_page(request):
    return render(request, "report_pdf.html")


@login_required
def test_page_view(request):
    return render(request, 'test_page.html')




# -------------------APIS

@login_required
def client_search_view(request):
    term = request.GET.get('term', '')
    # Usamos select_related para optimizar la consulta y traer los datos de las tablas relacionadas
    clients = Client.objects.select_related('company', 'client_type', 'country').filter(
        name__icontains=term
    )[:10]

    results = []
    for client in clients:
        # --- LÓGICA PARA CONSTRUIR EL TEXTO PRINCIPAL ---
        display_parts = [client.name]
        if client.lastname:
            display_parts.append(client.lastname)

        display_text = " ".join(display_parts)

        if client.company:
            display_text += f" - {client.company.name}"

        results.append({
            'id': client.id,
            'text': display_text,
            'full_label': display_text,
            'email': client.email,
            'client_type': client.client_type.name if client.client_type else 'N/A',
            'phone': client.phone,
            'country': client.country.name if client.country else 'N/A'
        })

    return JsonResponse({'results': results})


@login_required
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

    base_query = Support.objects.filter(
        call_status__name__in=['RECEIVED', 'MISSED', 'RETURNED'])

    # --- LÓGICA PARA EL PERÍODO 'day' (CORREGIDA Y AISLADA) ---
    if period == 'day':
        daily_query = base_query.filter(created_at__date=target_date.date())

        labels = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]
        data_map = {label: {'RECEIVED': 0, 'MISSED': 0, 'RETURNED': 0}
                    for label in labels}

        for call in daily_query:
            local_time = timezone.localtime(call.created_at)

            if call.call_status:  # Asegurarse de que el estado no sea nulo
                minute_bucket = "00" if local_time.minute < 30 else "30"
                hour_bucket = f"{local_time.hour:02d}:{minute_bucket}"
                if hour_bucket in data_map:
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
    else:  # 'month'
        trunc_func = TruncDay('created_at')
        date_format = "%b %d"
        first_day = target_date.replace(day=1)
        _, num_days = calendar.monthrange(target_date.year, target_date.month)
        last_day = target_date.replace(day=num_days)
        base_query = base_query.filter(created_at__range=[first_day, last_day])
        labels = [(first_day + timedelta(days=i)).strftime(date_format)
                for i in range(num_days)]

    call_stats = base_query \
        .annotate(period_start=trunc_func) \
        .values('period_start', 'call_status__name') \
        .annotate(count=Count('id')) \
        .order_by('period_start')

    data_map = {label: {'RECEIVED': 0, 'MISSED': 0, 'RETURNED': 0}
                for label in labels}
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


# La recarga de crédito solo debe ser accesible para quienes tengan el permiso personalizado.
# Esto bloqueará a Agents y Supervisores
# @login_required
# @permission_required('core.can_recharge_credit', raise_exception=True)
# def recharge_credit_view(request):
#     if request.method == 'POST':
#         # Buscamos el saldo, lo reseteamos a 3000 y lo guardamos
#         balance = CreditBalance.objects.first()
#         if balance:
#             balance.remaining_minutes += 3000
#             balance.save()
#     # Redirigimos siempre al dashboard
#     return redirect('core:dashboard')

@login_required
@permission_required('core.can_recharge_credit', raise_exception=True)
def recharge_credit_view(request):
    if request.method == 'POST':
        balance = CreditBalance.objects.first()
        if balance:
            balance.remaining_minutes += 3000
            balance.save()
            
            # --- INICIO: NOTIFICACIÓN EN TIEMPO REAL ---
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "dashboard",
                {
                    "type": "dashboard.update",
                    "data": get_dashboard_data(),
                }
            )
            # --- FIN: NOTIFICACIÓN ---
            
    return redirect('core:dashboard')


@login_required
def report_summary_api(request):
    period = request.GET.get("period")
    date = request.GET.get("date")

    total = 0
    channels = []

    if period and date:
        start_dt, end_dt = get_period_range(period, date)
        qs = Support.objects.filter(
            created_at__gte=start_dt, created_at__lt=end_dt)
        total = qs.count()
        channels = list(
            qs.values("support_channel__name")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

    return JsonResponse({
        "total": total,
        "channels": [
            {"channel": c["support_channel__name"], "total": c["total"]}
            for c in channels
        ]
    })



@login_required
@permission_required('core.view_support', raise_exception=True)
def download_report_pdf(request):
    period = request.GET.get("period", "daily")
    date_str = request.GET.get("date")

    if not date_str:
        date_str = timezone.now().strftime("%Y-%m-%d")

    start_dt, end_dt = get_period_range(period, date_str)

    # Queryset base para todos los cálculos
    qs = (Support.objects
        .filter(created_at__gte=start_dt, created_at__lt=end_dt)
        .select_related('client__company', 'support_channel', 'client__country')
        .order_by('created_at'))

    for s in qs:
        if s.duration:
            total_seconds = int(s.duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            s.duration_str = f"{hours:02}:{minutes:02}:{seconds:02}"
        else:
            s.duration_str = "—"
    # --- LÓGICA PARA GENERAR GRÁFICOS ---

    # 1. Cálculo de datos para los gráficos
    channel_stats = list(qs.values('support_channel__name').annotate(count=Count('id')).order_by('-count'))
    channel_labels = [item['support_channel__name'] for item in channel_stats]
    channel_data = [item['count'] for item in channel_stats]
    
    country_stats = list(qs.values('client__country__name').annotate(count=Count('id')).order_by('-count'))
    country_labels = [item['client__country__name'] for item in country_stats if item['client__country__name']]
    country_data = [item['count'] for item in country_stats if item['client__country__name']]

    # 2. Configuración de los gráficos de Chart.js
    doughnut_chart_config = {
        'type': 'doughnut',
        'data': {
            'labels': channel_labels,
            'datasets': [{'data': channel_data, 'backgroundColor': ['#4e73df', '#f6c23e', '#e74a3b', '#1cc88a', '#36b9cc', '#6f42c1','#e0e0e0','#ff9f40']}]
        },
        'options': { 'plugins': { 'legend': { 'position': 'right' } } }
    }

    bar_chart_config = {
        'type': 'horizontalBar',
        'data': {
            'labels': country_labels,
            'datasets': [{'label': 'Total Supports', 'data': country_data, 'backgroundColor': '#4e73df'}]
        },
        'options': {
            'legend': { 'display': False },
            'scales': { 'xAxes': [{ 'ticks': { 'beginAtZero': True, 'stepSize': 1 } }] }
        }
    }

    # 3. Generación de las URLs de las imágenes desde QuickChart.io
    base_url = "https://quickchart.io/chart"
    doughnut_chart_url = f"{base_url}?{urlencode({'c': json.dumps(doughnut_chart_config), 'format': 'png', 'width': 600, 'height': 400})}"
    bar_chart_url = f"{base_url}?{urlencode({'c': json.dumps(bar_chart_config), 'format': 'png', 'width': 600, 'height': 400})}"

    # --- DESCARGAR Y CODIFICAR LAS IMÁGENES ---
    try:
        doughnut_response = requests.get(doughnut_chart_url)
        doughnut_response.raise_for_status() # Lanza un error si la petición falla
        doughnut_chart_base64 = base64.b64encode(doughnut_response.content).decode('utf-8')
    except requests.exceptions.RequestException:
        doughnut_chart_base64 = None # Fallback si no se puede conectar

    try:
        bar_response = requests.get(bar_chart_url)
        bar_response.raise_for_status()
        bar_chart_base64 = base64.b64encode(bar_response.content).decode('utf-8')
    except requests.exceptions.RequestException:
        bar_chart_base64 = None

    # --- FIN: LÓGICA PARA GENERAR GRÁFICOS ---

    filename = build_filename(period, start_dt, end_dt)

    if doughnut_chart_base64:
        print("Doughnut base64 OK:", doughnut_chart_base64[:100])
    else:
        print("❌ Doughnut chart failed to generate.")
    if bar_chart_base64:
        print("Bar base64 OK:", bar_chart_base64[:100])
    else:
        print("❌ Bar chart failed to generate.")

    print("Chart URL:", doughnut_chart_url)
    try:
        doughnut_response = requests.get(doughnut_chart_url)
        doughnut_response.raise_for_status()
        doughnut_chart_base64 = base64.b64encode(doughnut_response.content).decode('utf-8')
    except requests.exceptions.RequestException as e:
        print("❌ Doughnut chart request error:", e)
        doughnut_chart_base64 = None

    context = {
        "period": period,
        "start": start_dt,
        "end": end_dt,
        "supports": qs,
        "total": qs.count(),
        "doughnut_chart_base64": doughnut_chart_base64, # Pasamos la imagen codificada
        "bar_chart_base64": bar_chart_base64,          # Pasamos la imagen codificada
        "channel_stats": channel_stats,
    }
    return render_to_pdf("report_pdf.html", context, filename)