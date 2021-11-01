"""bidcruit URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from django.conf.urls import url
from django.conf import settings
from candidate import views
from accounts import views as account_views
from candidate import views as candidate_views
from company import views as company_view
handler404 = 'accounts.views.handler404'
handler500 = 'accounts.views.handler500'


urlpatterns = [
    path('admin/', admin.site.urls),
    path('candidate/', include('candidate.urls')),
    path('agency/', include('agency.urls')),
    path('', account_views.bidcruit_home, name='bidcruit_home'),
    path('company/', include('company.urls')),
    path('accounts/', include('accounts.urls')),
    path('chat/', include('chat.urls')),
    path("password_reset", auth_views.PasswordResetView.as_view(template_name='candidate/password/password_reset.html',
                                                                html_email_template_name='candidate/password/password_reset_email.html'),
         name="password_reset"),
    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='candidate/password/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name="candidate/password/password_reset_confirm.html"),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='candidate/password/password_reset_complete.html'),
         name='password_reset_complete'),
    path('tinymce/', include('tinymce.urls')),
    path('<str:url>/', candidate_views.timeline, name="timeline"),
    path('view_job/<int:id>',company_view.view_job,name="view_job"),
    path('apply_job/<int:id>/',candidate_views.apply_job,name='apply_job'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
