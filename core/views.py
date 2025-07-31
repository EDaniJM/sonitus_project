import json
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.db.models import Count, Sum
from django.db.models.functions import TruncYear, TruncMonth, TruncDay, TruncHour
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, permission_required  # Para proteger vistas
from django.utils import timezone
from django.template.loader import render_to_string
from django.http import HttpResponse

from .forms import SupportForm, ClientForm, CompanyForm
from .models import Client, Support, SupportChannel, Country, CreditBalance

from datetime import date, datetime, timedelta
import calendar

from .utils.ranges import get_period_range, build_filename
from .utils.pdf import render_to_pdf


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


@login_required
def dashboard_view(request):
    # --- Estadísticas que ya teníamos ---
    total_tickets = Support.objects.count()
    total_clients = Client.objects.count()
    tickets_today = Support.objects.filter(
        created_at__date=date.today()).count()

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
    line_chart_labels = [calendar.month_abbr[i]
                         for i in range(1, 13)]  # ["Jan", "Feb", ...]
    received_calls_data = [0] * 12  # [0, 0, 0, ...]
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


    country_stats = Support.objects.values(
        'client__country__name'  # Agrupamos por el nombre del país del cliente
    ).annotate(
        count=Count('id')        # Contamos los soportes en cada grupo
    ).order_by('-count')

    country_stats_list = list(country_stats)


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
        'consumed_minutes': consumed_minutes,
        'country_stats': country_stats_list,
    }
    return render(request, 'dashboard.html', context)

# El formulario solo debe ser accesible para quienes pueden "añadir" soportes.
# Esto bloqueará el acceso a los Supervisores.
@login_required
@permission_required('core.add_support', raise_exception=True)
def support_form_view(request):
    # Preparamos los datos para el JavaScript
    channel_call_data = {
        channel.id: channel.is_call for channel in SupportChannel.objects.all()}
    country_codes_data = {
        country.id: country.phone_code for country in Country.objects.all()}

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
                return redirect('core:dashboard')

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
                # La variable 'company' se crea y usa aquí dentro
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

# APIS


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

        # --- Creamos el diccionario con el nuevo 'text' ---
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
@login_required
@permission_required('core.can_recharge_credit', raise_exception=True)
def recharge_credit_view(request):
    if request.method == 'POST':
        # Buscamos el saldo, lo reseteamos a 3000 y lo guardamos
        balance = CreditBalance.objects.first()
        if balance:
            balance.remaining_minutes += 3000
            balance.save()
    # Redirigimos siempre al dashboard
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
def download_report_pdf(request):
    period = request.GET.get("period", "daily")
    date = request.GET.get("date")

    if not date:
        # fallback por si alguien llama directo
        date = timezone.now().strftime("%Y-%m-%d")

    start_dt, end_dt = get_period_range(period, date)

    # Traemos TODOS los soportes del rango, ordenados cronológicamente
    qs = (Support.objects
            .filter(created_at__gte=start_dt, created_at__lt=end_dt)
            .select_related('client__company', 'support_channel')
            .order_by('created_at'))

    total = qs.count()

    filename = build_filename(period, start_dt, end_dt)

    context = {
        "period": period,
        "start": start_dt,
        "end": end_dt,
        "supports": qs,
        "total": total,
    }
    return render_to_pdf("report_pdf.html", context, filename)
