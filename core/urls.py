from django.urls import path
from . import views

# Este es el nombre del conjunto de URLs de nuestra app
app_name = 'core'

urlpatterns = [
    # Cuando un usuario visite la raíz del sitio (''),
    # se ejecutará la vista dashboard_view
    path('', views.dashboard_view, name='dashboard'),
    path('forms/', views.support_form_view, name='forms'),
    path('reports/', views.reports_view, name='reports'),
    path('test/', views.test_page_view, name='test_page'),
    path('api/search/clients/', views.client_search_view, name='client_search'),
    path('api/call-stats-chart/', views.call_stats_chart_view, name='call_stats_chart'),
    path('recharge-credit/', views.recharge_credit_view, name='recharge_credit'),
]
