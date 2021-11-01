from django.urls import path
from django.conf.urls import url
from . import views
app_name= 'accounts'

urlpatterns = [
    path('resend_otp/', views.resend_otp, name="resend_otp"),
    url(r'^user_login_password/$', views.user_login_password, name='user_login_password'),
    url(r'^$', views.user_login_email, name='signin'),
    url(r'^verify_otp/$', views.verify_otp, name='verify_otp'),
    url(r'^user_logout/$', views.user_logout, name='user_logout'),
    path('check_email_is_valid', views.check_email_is_valid, name="check_email_is_valid"),
    url(r'^activate/('
        r'?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.activate, name='activate'),
    # url(r'^activate_account_confirmation/$', views.activate_account_confirmation, name='activate_account_confirmation'),
    path('back_to_home',views.back_to_home,name='back_to_home'),

    #ATS
    path('apply_job_cadidate_sendotp',views.apply_job_cadidate_sendotp,name='apply_job_cadidate_sendotp'),
    path('job_apply_verify_otp',views.job_apply_verify_otp,name='job_apply_verify_otp'),

    
]

