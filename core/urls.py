# pyrefly: ignore [missing-import]
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search_companies, name='search_companies'),
    path('company/<uuid:company_id>/', views.company_detail, name='company_detail'),
    path('company/<uuid:company_id>/complaint/new/', views.create_complaint, name='create_complaint'),
    path('complaint/<uuid:complaint_id>/', views.complaint_detail, name='complaint_detail'),
    path('complaint/<uuid:complaint_id>/respond/', views.company_respond, name='company_respond'),
    path('complaint/<uuid:complaint_id>/rejoinder/', views.consumer_rejoinder, name='consumer_rejoinder'),
    path('complaint/<uuid:complaint_id>/evaluate/', views.evaluate_complaint, name='evaluate_complaint'),
    path('api/companies/autocomplete/', views.autocomplete_companies, name='autocomplete_companies'),
    path('complaint/<uuid:complaint_id>/report/', views.report_complaint, name='report_complaint'),
    path('complaint/<uuid:complaint_id>/takedown/', views.request_takedown, name='request_takedown'),
    path('signup/', views.user_signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('verify-2fa/', views.verify_2fa, name='verify_2fa'),
    path('logout/', views.user_logout, name='logout'),
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),
    path('safety-tips/', views.safety_tips, name='safety_tips'),
    path('news/', views.news, name='news'),
    path('support/', views.support, name='support'),
    path('dashboard/', views.consumer_dashboard, name='consumer_dashboard'),
    path('export-my-data/', views.export_my_data, name='export_my_data'),
    path('anonymize-my-data/', views.anonymize_my_data, name='anonymize_my_data'),
    path('api/ai-mediation-assistant/', views.ai_mediation_api, name='ai_mediation_api'),
    path('complaint/<uuid:complaint_id>/certificate/', views.view_digital_certificate, name='view_digital_certificate'),
    path('sso/<str:provider>/', views.sso_login, name='sso_login'),
    path('api/companies/globe-data/', views.globe_data, name='globe_data'),
    path('api/notifications/', views.notifications_api, name='notifications_api'),
]
