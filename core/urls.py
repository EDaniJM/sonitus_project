from django.urls import path
from . import views

# Este es el nombre del conjunto de URLs de nuestra app
app_name = 'core'

urlpatterns = [
    # Vistas de autenticación
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # Vistas de la aplicación 
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('forms/', views.support_form_view, name='forms'),
    path('reports/', views.reports_view, name='reports'),
    path("reports/", views.report_page, name="report_page"),
    
    # Vistas de la API JS
    path('api/search/clients/', views.client_search_view, name='client_search'),
    path('api/call-stats-chart/', views.call_stats_chart_view, name='call_stats_chart'),
    path('recharge-credit/', views.recharge_credit_view, name='recharge_credit'),
    path("api/report-summary", views.report_summary_api, name="report_summary_api"),
    path("download-report-pdf", views.download_report_pdf, name="download_report_pdf"),
    
]

handler403 = 'core.views.permission_denied_view'
