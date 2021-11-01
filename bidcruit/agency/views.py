from bidcruit import settings
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from accounts.tokens import account_activation_token
from django.core.mail import EmailMessage, BadHeaderError, EmailMultiAlternatives
from . import models
from accounts.views import activate_account_confirmation
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse, request
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.encoding import force_bytes
from company.models import CandidateHire, CompanyProfile
from django.shortcuts import (
    render,
    get_object_or_404,
    redirect,
)
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
)
User = get_user_model()
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from smtplib import SMTPException

# Create your views here.


def agency_registration(request):
    if not request.user.is_authenticated:
        if request.method == 'POST':
            fname = request.POST.get('fname')
            lname = request.POST.get('lname')
            email = request.POST.get('email')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            checkbox = request.POST.get('checkbox')
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            device_type = ""
            if request.user_agent.is_mobile:
                device_type = "Mobile"
            if request.user_agent.is_tablet:
                device_type = "Tablet"
            if request.user_agent.is_pc:
                device_type = "PC"
            browser_type = request.user_agent.browser.family
            browser_version = request.user_agent.browser.version_string
            os_type = request.user_agent.os.family
            os_version = request.user_agent.os.version_string
            if User.objects.filter(email=request.POST['email']).exists():
                messages.error(request, 'User Already Exists.')
                return render(request, 'agency/agency_registration.html')
            else:
                usr = User.objects.create_agency(first_name=fname, last_name=lname,email=email,password=password,
                                                 ip=ip, device_type=device_type,browser_type=browser_type,
                                                 browser_version=browser_version, os_type=os_type,os_version=os_version)
                mail_subject = 'Activate your account.'
                current_site = get_current_site(request)
                html_content = render_to_string('accounts/acc_active_email.html', {'user': usr,
                                                                                   'name': fname + ' ' + lname,
                                                                                   'email': email,
                                                                                   'domain': current_site.domain,
                                                                                   'uid': urlsafe_base64_encode(
                                                                                       force_bytes(usr.pk)),
                                                                                   'token': account_activation_token.make_token(
                                                                                       usr), })
                to_email = usr.email
                from_email = settings.EMAIL_HOST_USER
                msg = EmailMultiAlternatives(mail_subject, mail_subject, from_email, to=[to_email])
                msg.attach_alternative(html_content, "text/html")
                try:
                    msg.send()
                except BadHeaderError:
                    User.objects.get(email__exact=email).delete()
                    messages.error(request, 'Invalid header found.')
                    return render(request, 'agency/agency_registration.html')
                except SMTPException as e:
                    User.objects.get(email__exact=email).delete()
                    messages.error(request, e)
                    return render(request, 'agency/agency_registration.html')
                except:
                    User.objects.get(email__exact=email).delete()
                    messages.error(request, 'Mail sending failed, Please check your internet connection !!')
                    return render(request, 'agency/agency_registration.html')
                return activate_account_confirmation(request, fname + ' ' + lname, email)
    else:
        if request.user.is_authenticated:
            if request.user.is_candidate:
                return redirect('candidate:home')
            if request.user.is_company:
                profile = CompanyProfile.objects.filter(company_id=request.user.id)
                if profile:
                    return redirect('company:company_profile')
                else:
                    return redirect('company:add_edit_profile')
    return render(request, 'agency/agency_registration.html')


@login_required(login_url="/")
def agency_home(request):
    return render(request, 'agency/agency_home.html')