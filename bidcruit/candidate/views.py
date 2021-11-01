import os
import shutil
from django.contrib.auth.forms import PasswordResetForm
from bidcruit import settings
import re
from elasticsearch_dsl import Q as Elastic_Q
from company.documents import CandidateDocument
import json
import random
import string
from datetime import datetime
from dateutil.relativedelta import relativedelta
import datetime
from rest_framework.response import Response
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from accounts.tokens import account_activation_token
from django.core.mail import EmailMessage, BadHeaderError, EmailMultiAlternatives
from django.contrib.auth.decorators import login_required
from . import models
import pyotp
import re
from accounts.views import activate_account_confirmation
import socket
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse, request
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from .utils.charts import months, colorPrimary, colorSuccess, colorDanger, generate_color_palette, get_year_dict
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
from rest_framework.decorators import api_view
from django.http.response import JsonResponse
import pyqrcode
from company.models import CandidateHire, CompanyProfile, JCR, JobCreation, AppliedCandidate,JobWorkflow,WorkflowStages,PreRequisites,Template_creation
import png
from pyqrcode import QRCode
import qrcode
from io import BytesIO
from django.core.files import File
import pandas as pd
from chat.models import Messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
import candidate
from io import BytesIO
import zipfile

User = get_user_model()
cureent_user = False
from django.core import serializers


def bidcruit_home(request):
    return render(request, 'candidate/landing-index.html')


def state_view(request, id):
    states = models.State.objects.filter(country_code_id=id)
    context = {"states": states}
    return render(request, "candidate/state.html", context)


#  to populate city dropdown when state is selected.
def city_view(request, id):
    cities = models.City.objects.filter(state_code_id=id)
    if cities:
        context = {"cities": cities}
    else:
        context = {"cities": ["", 0]}
    return render(request, "candidate/city.html", context)


# get all cities of selected country
def cities_by_country(request, id):
    states = models.State.objects.filter(country_code=id).values_list('id')
    cities = models.City.objects.filter(state_code_id__in=states)
    if cities:
        context = {"cities": cities}
    else:
        context = {"cities": ["", 0]}
    return render(request, "candidate/city.html", context)


def preference_cities_by_country(request, id):
    states = models.State.objects.filter(country_code=id).values_list('id')
    cities = models.City.objects.filter(state_code_id__in=states)
    if cities:
        context = {"cities": cities}
    else:
        context = {"cities": ["", 0]}
    return render(request, "candidate/preference_city.html", context)


@login_required(login_url="/")
def get_active_profile(userid):
    profiles = models.Profile.objects.filter(candidate_id=User.objects.get(id=userid))
    for i in profiles:
        if i.active == True:
            # candidate_profile = models.CandidateProfile.objects.get(profile_id=i)
            return i


def get_present_year():
    return int(datetime.datetime.now().year)


def get_present_month():
    return datetime.datetime.now().strftime('%B')


@login_required(login_url="/")
def index(request):
    if request.user.is_candidate:
        context = {}
        if models.CandidateSEO.objects.filter(candidate_id=request.user.id).exists():
            context['seo'] = models.CandidateSEO.objects.get(candidate_id=request.user.id)
        current_user = models.CandidateProfile.objects.filter(candidate_id=request.user.id).first()
        get_all_profile = models.CandidateProfile.objects.filter(candidate_id=request.user.id)
        get_profile_list = [i.profile_id.id for i in get_all_profile]
        models.Profile.objects.filter(candidate_id=request.user.id).exclude(id__in=get_profile_list).delete()
        referral_list = models.ReferralDetails.objects.filter(referred_by=User.objects.get(id=request.user.id))
        count = 0
        profiles = models.Profile.objects.filter(candidate_id=request.user.id)
        profile_count = len(profiles)
        for i in profiles:
            if i.active == True:
                # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>",i.id)
                request.session['active_profile_id'] = i.id
                context['active_profile_hide_fields'] = models.Candidate_Hide_Fields.objects.get(
                    candidate_id=request.user, profile_id=i)
                context['active_profile'] = i
                context['userdata'] = models.CandidateProfile.objects.get(candidate_id=request.user, profile_id=i)
                break
        for i in referral_list:
            if i.referred_to.is_active:
                count += 1
        if models.CandidateSEO.objects.filter(candidate_id=request.user.id).exists():
            context['seo'] = models.CandidateSEO.objects.get(candidate_id=request.user.id)
        context['profile'] = current_user
        context['get_all_profile'] = get_all_profile
        context['referral_list'] = referral_list
        context['count'] = count
        context['profiles'] = profiles
        context['profile_count'] = profile_count
    else:
        return redirect('accounts:user_logout')
    return render(request, 'candidate/Dashbord-profile.html', context)


def generate_referral_code():
    num = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(12)])
    return num


def ragister(request):
    alert = {}
    if not request.user.is_authenticated:
        if request.method == 'POST':
            fname = request.POST.get('fname')
            lname = request.POST.get('lname')
            email = request.POST.get('email')
            referred_by = request.POST.get('referral_code')
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
            context1 = {
                "ip": ip,
                "device_type": device_type,
                "browser_type": browser_type,
                "browser_version": browser_version,
                "os_type": os_type,
                "os_version": os_version
            }
            if User.objects.filter(email=request.POST['email']).exists():
                alert['message'] = "email already exists"
            else:
                usr = User.objects.create_candidate(email=email, first_name=fname, last_name=lname,
                                                    password=password, ip=ip, device_type=device_type,
                                                    browser_type=browser_type,
                                                    browser_version=browser_version, os_type=os_type,
                                                    os_version=os_version,
                                                    referral_number=generate_referral_code(), referred_by=referred_by)
                try:
                    mail_subject = 'Activate your account.'
                    current_site = get_current_site(request)
                    # print('domain----===========',current_site.domain)
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
                    msg.send()
                    if models.User.objects.filter(referral_number=referred_by).exists():
                        referred_by_user = User.objects.get(referral_number=referred_by)
                        referred_to_user = User.objects.get(email__exact=email)
                        models.ReferralDetails.objects.create(referred_by=referred_by_user,
                                                              referred_to=referred_to_user)
                except BadHeaderError:
                    new_registered_usr = User.objects.get(email__exact=email).delete()
                    models.ReferralDetails.objects.get(referred_to=new_registered_usr).delete()
                    alert['message'] = "email not send"
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
    return render(request, 'candidate/candidate_signup.html', alert)


# def upload_resume(request,**kargs):
#     # if request.method == "POST":
#     #   request_file = request.FILES['resume'] if 'resume' in request.FILES else None
#     print('\n\n\nrequest_file', kargs)
#     personal = models.CandidateProfile.objects.filter(candidate_id=User.objects.get(email=request.user.email))
#     country = models.Country.objects.all()
#     state = models.State.objects.all()
#     city = models.City.objects.all()
#     language = models.Languages.objects.all()
#     fluency = models.Fluency.objects.all()
#     gender = models.Gender.objects.all()
#     maritial_type = models.MaritalType.objects.all()
#     notice_period = models.NoticePeriod.objects.all()
#     #  uploaded_cv = models.UploadCv.objects.create(candidate_id=User.objects.get(email=request.user.email),
#     #                                               resume=request_file)
#     fileurl = models.UploadCv.objects.filter(candidate_id=User.objects.get(email=request.user.email)).order_by(
#         '-id').first()
#     resume_data = False
#     exp_years = [str(yearrange) if yearrange <= 30 else '30+' for yearrange in range(32)]
#     exp_months = [str(i) for i in range(12)]
#     kargs['add']= 'add'
#     models.Profile.objects.get(id=request.session['profile_id'])=None
#     if kargs['add'] != 'add':    
#         if personal:
#             for profile in personal:
#                 total_experience_years = str(profile.total_experience).split('.')[0]
#                 total_experience_months = str(profile.total_experience).split('.')[1]
#                 candidate_preferred_cities = []
#                 for city_id in profile.preferred_cities.split(","):
#                     city_obj = models.City.objects.get(id=city_id)
#                     candidate_preferred_cities.append({'id': city_obj.id, 'city_name': city_obj.city_name})
#                 state = models.State.objects.filter(country_code=profile.country.id)
#                 city = models.City.objects.filter(state_code=profile.state.id)
#             education_reload = models.CandidateEducation.objects.filter(
#                 candidate_id=User.objects.get(email=request.user.email)).order_by('record_id')
#             if education_reload:
#                 experience_reload = models.CandidateExperience.objects.filter(
#                     candidate_id=User.objects.get(email=request.user.email)).order_by('record_id')
#                 if experience_reload:
#                     certification_reload = models.CandidateCertificationAttachment.objects.filter(
#                         candidate_id=User.objects.get(email=request.user.email)).order_by('record_id')
#                     if certification_reload:
#                         skillusermap_reload = models.CandidateSkillUserMap.objects.filter(
#                             candidate_id=User.objects.get(email=request.user.email)).order_by('record_id')
#                         if skillusermap_reload:
#                             portfolio_reload = models.CandidatePortfolio.objects.filter(
#                                 candidate_id=User.objects.get(email=request.user.email)).order_by('record_id')
#                             if portfolio_reload:
#                                 summa_reload = models.CandidateSummary.objects.filter(
#                                     candidate_id=User.objects.get(email=request.user.email))
#                                 if summa_reload:
#                                     socialnetwork_reload = models.CandidateSocialNetwork.objects.filter(
#                                         candidate_id=User.objects.get(email=request.user.email)).order_by('record_id')
#                                     if socialnetwork_reload:
#                                         awards_reload = models.CandidateAward.objects.filter(
#                                             candidate_id=User.objects.get(email=request.user.email)).order_by('record_id')
#                                         if awards_reload:
#                                             language_reload = models.CandidateLanguage.objects.filter(candidate_id=
#                                             User.objects.get(
#                                                 email=request.user.email)).order_by('record_id')
#                                             if language_reload:
#                                                 otherfield_reload = models.CandidateOtherField.objects.filter(
#                                                     candidate_id=User.objects.get(email=request.user.email)).order_by(
#                                                     'record_id')
#                                                 if otherfield_reload:
#                                                     return render(request, "candidate/candidate_wizard_form.html",
#                                                                 {'fileurl': fileurl, 'personal': personal,
#                                                                 'education_get': education_reload,
#                                                                 'experience_get': experience_reload,
#                                                                 'certification_get': certification_reload,
#                                                                 'skillusermap_get': skillusermap_reload,
#                                                                 'portfolio_get': portfolio_reload,
#                                                                 'resume_data': resume_data,
#                                                                 'summa_get': summa_reload,
#                                                                 'otherfield_get': otherfield_reload,
#                                                                 'country': country, 'fluency': fluency,
#                                                                 'language': language,
#                                                                 'language_reload': language_reload,
#                                                                 'socialnetwork_reload': socialnetwork_reload,
#                                                                 'awards_get': awards_reload,
#                                                                 'notice_period':notice_period,'city':city,'state':state,
#                                                                 'maritial_type': maritial_type,
#                                                                 'gender': gender,
#                                                                 'exp_years':exp_years,'exp_months':exp_months,
#                                                                 'total_experience_years':total_experience_years,'total_experience_months':total_experience_months
#                                                                 ,'candidate_preferred_cities':candidate_preferred_cities})
#                                                 return render(request, "candidate/candidate_wizard_form.html",
#                                                             {'fileurl': fileurl, 'personal': personal,
#                                                             'education_get': education_reload,
#                                                             'experience_get': experience_reload,
#                                                             'certification_get': certification_reload,
#                                                             'skillusermap_get': skillusermap_reload,
#                                                             'portfolio_get': portfolio_reload,
#                                                             'resume_data': resume_data,
#                                                             'summa_get': summa_reload,
#                                                             'country': country, 'fluency': fluency, 'language': language,
#                                                             'language_reload': language_reload,
#                                                             'socialnetwork_reload': socialnetwork_reload,
#                                                             'awards_get': awards_reload,'notice_period':notice_period,
#                                                             'maritial_type': maritial_type,
#                                                             'gender': gender,
#                                                             'city':city,'state':state,'exp_years':exp_years,'exp_months':exp_months,
#                                                             'total_experience_years':total_experience_years,'total_experience_months':total_experience_months
#                                                             ,'candidate_preferred_cities':candidate_preferred_cities})
#                                             return render(request, "candidate/candidate_wizard_form.html",
#                                                         {'fileurl': fileurl, 'personal': personal,
#                                                         'education_get': education_reload,
#                                                         'experience_get': experience_reload,
#                                                         'certification_get': certification_reload,
#                                                         'skillusermap_get': skillusermap_reload,
#                                                         'portfolio_get': portfolio_reload, 'resume_data': resume_data,
#                                                         'summa_get': summa_reload, 'country': country,
#                                                         'fluency': fluency,
#                                                         'language': language,
#                                                         'maritial_type': maritial_type,
#                                                         'gender': gender,
#                                                         'socialnetwork_reload': socialnetwork_reload,
#                                                         'awards_get': awards_reload,'notice_period':notice_period,
#                                                         'city':city,'state':state,'exp_years':exp_years,'exp_months':exp_months,
#                                                         'total_experience_years':total_experience_years,'total_experience_months':total_experience_months
#                                                         ,'candidate_preferred_cities':candidate_preferred_cities})
#                                         return render(request, "candidate/candidate_wizard_form.html",
#                                                     {'fileurl': fileurl, 'personal': personal,
#                                                     'education_get': education_reload,
#                                                     'experience_get': experience_reload,
#                                                     'certification_get': certification_reload,
#                                                     'skillusermap_get': skillusermap_reload,
#                                                     'portfolio_get': portfolio_reload, 'resume_data': resume_data,
#                                                     'country': country, 'fluency': fluency, 'language': language,'maritial_type':maritial_type,
#                         'gender':gender,
#                                                     'notice_period':notice_period,'city':city,'state':state,
#                                                     'exp_years':exp_years,'exp_months':exp_months,
#                                                     'total_experience_years':total_experience_years,'total_experience_months':total_experience_months
#                                                     ,'candidate_preferred_cities':candidate_preferred_cities})
#                                     return render(request, "candidate/candidate_wizard_form.html",
#                                                 {'fileurl': fileurl, 'personal': personal,
#                                                 'education_get': education_reload,
#                                                 'experience_get': experience_reload,
#                                                 'certification_get': certification_reload, 'resume_data': resume_data,
#                                                 'skillusermap_get': skillusermap_reload, 'country': country,
#                                                 'fluency': fluency, 'language': language,'maritial_type':maritial_type,
#                         'gender':gender,'notice_period':notice_period,
#                                                 'city':city,'state':state,'exp_years':exp_years,'exp_months':exp_months,
#                                                 'total_experience_years':total_experience_years,'total_experience_months':total_experience_months
#                                                 ,'candidate_preferred_cities':candidate_preferred_cities})
#                                 return render(request, "candidate/candidate_wizard_form.html",
#                                             {'fileurl': fileurl, 'personal': personal, 'education_get': education_reload,
#                                             'resume_data': resume_data,
#                                             'experience_get': experience_reload,
#                                             'certification_get': certification_reload,
#                                             'country': country, 'fluency': fluency, 'language': language,'maritial_type':maritial_type,
#                         'gender':gender,'notice_period':notice_period,
#                                             'city':city,'state':state,'exp_years':exp_years,'exp_months':exp_months,
#                                             'total_experience_years':total_experience_years,'total_experience_months':total_experience_months
#                                             ,'candidate_preferred_cities':candidate_preferred_cities})
#                             return render(request, "candidate/candidate_wizard_form.html",
#                                         {'fileurl': fileurl, 'personal': personal, 'certification_get': certification_reload,'education_get': education_reload,
#                                         'resume_data': resume_data,
#                                         'experience_get': experience_reload, 'country': country, 'fluency': fluency,
#                                         'language': language,'maritial_type':maritial_type,
#                         'gender':gender,'notice_period':notice_period,'city':city,'state':state,
#                                         'exp_years':exp_years,'exp_months':exp_months,
#                                         'total_experience_years':total_experience_years,'total_experience_months':total_experience_months
#                                         ,'candidate_preferred_cities':candidate_preferred_cities})
#                         return render(request, "candidate/candidate_wizard_form.html",
#                                     {'fileurl': fileurl, 'personal': personal, 'resume_data': resume_data,
#                                     'education_get': education_reload, 'experience_get': experience_reload, 'country': country, 'fluency': fluency,
#                                     'language': language,'maritial_type':maritial_type,
#                         'gender':gender,'notice_period':notice_period,'city':city,'state':state,
#                                     'exp_years':exp_years,'exp_months':exp_months,
#                                     'total_experience_years':total_experience_years,'total_experience_months':total_experience_months
#                                     ,'candidate_preferred_cities':candidate_preferred_cities})
#                     return render(request, "candidate/candidate_wizard_form.html",
#                                 {'fileurl': fileurl, 'personal': personal, 'resume_data': resume_data, 'country': country,
#                                 'fluency': fluency, 'language': language,'maritial_type':maritial_type,
#                         'gender':gender,'notice_period':notice_period,
#                                 'city':city,'state':state,'exp_years':exp_years,'exp_months':exp_months,
#                                 'total_experience_years':total_experience_years,'total_experience_months':total_experience_months
#                                 ,'candidate_preferred_cities':candidate_preferred_cities})
#                 return render(request, "candidate/candidate_wizard_form.html",
#                             {'fileurl': fileurl, 'personal': personal, 'resume_data': resume_data, 'country': country,
#                             'fluency': fluency, 'language': language,'maritial_type':maritial_type,
#                         'gender':gender,'notice_period':notice_period,'city':city,
#                             'state':state,'exp_years':exp_years,'exp_months':exp_months,
#                             'total_experience_years':total_experience_years,'total_experience_months':total_experience_months
#                             ,'candidate_preferred_cities':candidate_preferred_cities})
#             return render(request, "candidate/candidate_wizard_form.html",
#                         {'fileurl': fileurl, 'personal': personal, 'resume_data': resume_data, 'country': country,
#                         'fluency': fluency, 'language': language,'maritial_type':maritial_type,
#                         'gender':gender,'notice_period':notice_period,
#                         'city':city,'state':state,'exp_years':exp_years,'exp_months':exp_months,
#                         'total_experience_years':total_experience_years,'total_experience_months':total_experience_months,
#                         'candidate_preferred_cities':candidate_preferred_cities})
#         else:
#             return render(request, "candidate/candidate_wizard_form.html",
#                         {'fileurl': fileurl, 'resume_data': resume_data, 'country': country, 'fluency': fluency,'maritial_type':maritial_type,
#                         'gender':gender,'language': language,'notice_period':notice_period,'exp_years':exp_years,'exp_months':exp_months})
#     else:
#         if models.Profile.objects.get(id=request.session['profile_id']):
#             personal = models.CandidateProfile.objects.filter(candidate_id=User.objects.get(email=request.user.email),profile_id=models.Profile.objects.get(id=models.Profile.objects.get(id=request.session['profile_id'])))
#             if personal:
#                 for profile in personal:
#                     total_experience_years = str(profile.total_experience).split('.')[0]
#                     total_experience_months = str(profile.total_experience).split('.')[1]
#                     candidate_preferred_cities = []
#                     for city_id in profile.preferred_cities.split(","):
#                         city_obj = models.City.objects.get(id=city_id)
#                         candidate_preferred_cities.append({'id': city_obj.id, 'city_name': city_obj.city_name})
#                     state = models.State.objects.filter(country_code=profile.country.id)
#                     city = models.City.objects.filter(state_code=profile.state.id)
#                 education_reload = models.CandidateEducation.objects.filter(profile_id=models.Profile.objects.get(id=models.Profile.objects.get(id=request.session['profile_id'])),
#                     candidate_id=User.objects.get(email=request.user.email)).order_by('record_id')
#                 if education_reload:
#                     experience_reload = models.CandidateExperience.objects.filter(profile_id=models.Profile.objects.get(id=models.Profile.objects.get(id=request.session['profile_id'])),
#                     candidate_id=User.objects.get(email=request.user.email)).order_by('record_id')
#                     if experience_reload:
#                         certification_reload = models.CandidateCertificationAttachment.objects.filter(profile_id=models.Profile.objects.get(id=models.Profile.objects.get(id=request.session['profile_id'])),
#                             candidate_id=User.objects.get(email=request.user.email)).order_by('record_id')
#                         skillusermap_reload = models.CandidateSkillUserMap.objects.filter(profile_id=models.Profile.objects.get(id=models.Profile.objects.get(id=request.session['profile_id'])),
#                             candidate_id=User.objects.get(email=request.user.email)).order_by('record_id')
#                         portfolio_reload = models.CandidatePortfolio.objects.filter(profile_id=models.Profile.objects.get(id=models.Profile.objects.get(id=request.session['profile_id'])),
#                             candidate_id=User.objects.get(email=request.user.email)).order_by('record_id')
#                         summa_reload = models.CandidateSummary.objects.filter(profile_id=models.Profile.objects.get(id=models.Profile.objects.get(id=request.session['profile_id'])),
#                             candidate_id=User.objects.get(email=request.user.email))
#                         socialnetwork_reload = models.CandidateSocialNetwork.objects.filter(profile_id=models.Profile.objects.get(id=models.Profile.objects.get(id=request.session['profile_id'])),
#                             candidate_id=User.objects.get(email=request.user.email)).order_by('record_id')
#                         awards_reload = models.CandidateAward.objects.filter(profile_id=models.Profile.objects.get(id=models.Profile.objects.get(id=request.session['profile_id'])),
#                             candidate_id=User.objects.get(email=request.user.email)).order_by('record_id')
#                         language_reload = models.CandidateLanguage.objects.filter(profile_id=models.Profile.objects.get(id=models.Profile.objects.get(id=request.session['profile_id'])),
#                             candidate_id=User.objects.get(email=request.user.email)).order_by('record_id')
#                         otherfield_reload = models.CandidateOtherField.objects.filter(profile_id=models.Profile.objects.get(id=models.Profile.objects.get(id=request.session['profile_id'])),
#                             candidate_id=User.objects.get(email=request.user.email)).order_by('record_id')
#                         return render(request, "candidate/candidate_wizard_form.html",
#                                                                 {'fileurl': fileurl, 'personal': personal,
#                                                                 'education_get': education_reload,
#                                                                 'experience_get': experience_reload,
#                                                                 'certification_get': certification_reload,
#                                                                 'skillusermap_get': skillusermap_reload,
#                                                                 'portfolio_get': portfolio_reload,
#                                                                 'resume_data': resume_data,
#                                                                 'summa_get': summa_reload,
#                                                                 'otherfield_get': otherfield_reload,
#                                                                 'country': country, 'fluency': fluency,
#                                                                 'language': language,
#                                                                 'language_reload': language_reload,
#                                                                 'socialnetwork_reload': socialnetwork_reload,
#                                                                 'awards_get': awards_reload,
#                                                                 'notice_period':notice_period,'city':city,'state':state,
#                                                                 'maritial_type': maritial_type,
#                                                                 'gender': gender,
#                                                                 'exp_years':exp_years,'exp_months':exp_months,
#                                                                 'total_experience_years':total_experience_years,'total_experience_months':total_experience_months
#                                                                 ,'candidate_preferred_cities':candidate_preferred_cities})
#                     else:
#                         return render(request, "candidate/candidate_wizard_form.html",
#                                                                 {'fileurl': fileurl, 'personal': personal,
#                                                                 'education_get': education_reload,
#                                                                 'experience_get': experience_reload,
#                                                                 'notice_period':notice_period,'city':city,'state':state,
#                                                                 'maritial_type': maritial_type,
#                                                                 'gender': gender,
#                                                                 'exp_years':exp_years,'exp_months':exp_months,
#                                                                 'total_experience_years':total_experience_years,'total_experience_months':total_experience_months
#                                                                 ,'candidate_preferred_cities':candidate_preferred_cities})
#                 else:
#                     return render(request, "candidate/candidate_wizard_form.html",
#                                                             {'fileurl': fileurl, 'personal': personal,
#                                                             'education_get': education_reload,
#                                                             'notice_period':notice_period,'city':city,'state':state,
#                                                             'maritial_type': maritial_type,
#                                                             'gender': gender,
#                                                             'exp_years':exp_years,'exp_months':exp_months,
#                                                             'total_experience_years':total_experience_years,'total_experience_months':total_experience_months
#                                                             ,'candidate_preferred_cities':candidate_preferred_cities})
#             else:
#                 return render(request, "candidate/candidate_wizard_form.html",
#                                                         {'fileurl': fileurl, 'personal': personal,
#                                                         'notice_period':notice_period,'city':city,'state':state,
#                                                         'maritial_type': maritial_type,
#                                                         'gender': gender,
#                                                         'exp_years':exp_years,'exp_months':exp_months,
#                                                         'total_experience_years':total_experience_years,'total_experience_months':total_experience_months
#                                                         ,'candidate_preferred_cities':candidate_preferred_cities})
#         return render(request, "candidate/candidate_wizard_form.html",
#                         {'fileurl': fileurl, 'resume_data': resume_data, 'country': country, 'fluency': fluency,'maritial_type':maritial_type,
#                         'gender':gender,'language': language,'notice_period':notice_period,'exp_years':exp_years,'exp_months':exp_months})

@login_required(login_url="/")
def upload_resume(request, **kargs):
    country = models.Country.objects.all()
    state = models.State.objects.all()
    city = models.City.objects.all()
    language = models.Languages.objects.all()
    fluency = models.Fluency.objects.all()
    gender = models.Gender.objects.all()
    maritial_type = models.MaritalType.objects.all()
    notice_period = models.NoticePeriod.objects.all()
    industry_type = models.IndustryType.objects.all()
    months = models.Month.objects.all()
    profile_themes = models.CandidateProfileTheme.objects.all()
    exp_years = [str(yearrange) if yearrange <= 30 else '30+' for yearrange in range(32)]
    exp_months = [str(i) for i in range(12)]
    if kargs['url']:
        return render(request, "candidate/candidate_wizard_form.html", {'country': country,
                                                                        'fluency': fluency, 'language': language,
                                                                        'maritial_type': maritial_type,
                                                                        'gender': gender,
                                                                        'notice_period': notice_period, 'city': city,
                                                                        'state': state, 'exp_years': exp_years,
                                                                        'exp_months': exp_months,
                                                                        'industry_type': industry_type,
                                                                        'profile_themes': profile_themes,
                                                                        'months': months})


def check_email_is_valid(request):
    email = request.POST.get("email")
    regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'
    if (re.search(regex, email)):
        user_obj = models.User.objects.filter(email=email).exists()
        if user_obj:
            return HttpResponse(True)
        else:
            return HttpResponse(False)
    else:
        return HttpResponse('Invalid')


@login_required(login_url="/")
def personal_detail_temp(request):
    if request.method == 'POST':
        if request.POST.get('emailAddress') == request.user.email:
            user_id = User.objects.get(email=request.POST.get('emailAddress'))
        else:
            return HttpResponse(False)
        if user_id:
            gender = models.Gender.objects.get(id=request.POST.get('gender'))
            notice_period_obj = models.NoticePeriod.objects.get(id=request.POST.get('notice_period'))
            marital_status = models.MaritalType.objects.get(id=request.POST.get('marital_status'))
            if request.POST.get('salary_checkbox') == '1':
                expected_salary_min = 'As Per Company'
                expected_salary_max = 'As Per Company'
            else:
                expected_salary_min = request.POST.get('expected_salary_min')
                expected_salary_max = request.POST.get('expected_salary_max')
            random_no = random.randint(1000, 99999)
            url_name = request.user.first_name + '_' + request.user.last_name + '_' + str(random_no)
            custom_url=url_name
            current_site = get_current_site(request)
            qr_share_link = "https://bidcruit.com/" + url_name + "/"
            # qr_share_link = "https://www.google.com/"
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=6,
                border=4,
            )
            qr.add_data(qr_share_link)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            blob = BytesIO()
            img.save(blob, 'JPEG')
            preferred_cities = ','.join(map(str, request.POST.getlist('preferred_cities')))
            total_experience = request.POST.get('total_experience_year') + '.' + request.POST.get(
                'total_experience_month')

            about = request.POST.get('about-me')
            about = re.sub('\s+style="(.*?)"', "", about)
            technical = request.POST.get('technical-knowledge')
            technical = re.sub('\s+style="(.*?)"', "", technical)
            print('\n\n\n=========== session',request.session['profile_id'])
            candidate_profile_obj, obj_created = models.CandidateProfile.objects.update_or_create(candidate_id=user_id,
                                                                                                  profile_id=models.Profile.objects.get(
                                                                                                      id=
                                                                                                      request.session[
                                                                                                          'profile_id']),
                                                                                                  defaults={
                                                                                                      'contact_no': request.POST.get(
                                                                                                          'phone'),
                                                                                                      'address': request.POST.get(
                                                                                                          'address'),
                                                                                                      'dob': request.POST.get(
                                                                                                          'dob') or None,
                                                                                                      'country': models.Country.objects.get(
                                                                                                          id=int(
                                                                                                              request.POST.get(
                                                                                                                  'country'))),
                                                                                                      'state': models.State.objects.get(
                                                                                                          id=int(
                                                                                                              request.POST.get(
                                                                                                                  'state'))),
                                                                                                      'city': models.City.objects.get(
                                                                                                          id=int(
                                                                                                              request.POST.get(
                                                                                                                  'city'))),
                                                                                                      'gender': gender,
                                                                                                      'marital_status': marital_status,
                                                                                                      'user_image': request.FILES.get(
                                                                                                          'user_image'),
                                                                                                      'current_salary': int(
                                                                                                          request.POST.get(
                                                                                                              'current_salary')),
                                                                                                      'notice_period': notice_period_obj,
                                                                                                      'expected_salary_min': expected_salary_min,
                                                                                                      'expected_salary_max': expected_salary_max,
                                                                                                      'url_name': url_name,
                                                                                                      'designation': request.POST.get(
                                                                                                          'designation'),
                                                                                                      'preferred_cities': preferred_cities,
                                                                                                      'total_experience': float(
                                                                                                          total_experience),
                                                                                                      'technical_knowledge': technical,
                                                                                                      'about_me': about,
                                                                                                      'custom_url':custom_url
                                                                                                  })
            candidate_profile_obj.qr_code.save(request.user.first_name + '.jpg', File(blob), save=True)
            return HttpResponse(True)
        else:
            return HttpResponse(False)
    else:
        print('fail')


@login_required(login_url="/")
def education_temp(request):
    if request.method == 'POST':
        updatedData = json.loads(request.POST.get('education_data'))
        user_id = models.User.objects.get(email=request.user.email)
        for i in updatedData:
            for j in updatedData[i]:
                education_data = updatedData[i][j]

                edu_start_month = models.Month.objects.get(id=education_data['edu_start_month'])
                edu_end_month = models.Month.objects.get(id=education_data['edu_end_month'])
                edu_start_date = edu_start_month.name + "," + " " + education_data['edu_start_year']
                edu_end_date = edu_end_month.name + "," + " " + education_data['edu_end_year']

                attached_file = request.FILES.get('edu_file' + education_data['record_id'], None)
                university_board, uni_created = models.UniversityBoard.objects.update_or_create(
                    name=education_data['c_university'], defaults={'name': education_data['c_university']})
                degree, deg_created = models.Degree.objects.update_or_create(name=education_data['c_degree'])
                summary = education_data['e_summary']
                summary = re.sub('\s+style="(.*?)"', "", summary)
                temp_education, created = models.CandidateEducation.objects.update_or_create(
                    record_id=education_data['record_id'], candidate_id=user_id,
                    profile_id=models.Profile.objects.get(id=int(request.session['profile_id'])),
                    defaults={'university_board': university_board,
                              'degree': degree, 'candidate_id': user_id, 'certificate': attached_file,
                              'start_date': edu_start_date, 'end_date': edu_end_date,
                              'grade': education_data['c_grade'],
                              'summary': summary,
                              })
                if created:
                    pass
                else:
                    temp_education.update_at = datetime.datetime.now()
        # print("\n\n\n\n\n\n////////////////", request.POST.get('gap_checkbox'))
        if request.POST.get('gap_checkbox') == 'true':
            gapData = json.loads(request.POST.get('gap_data'))
            for i in gapData:
                for j in gapData[i]:
                    gap_data = gapData[i][j]

                    edu_gap_start_month = models.Month.objects.get(id=gap_data['edu_gap_start_month'])
                    edu_gap_end_month = models.Month.objects.get(id=gap_data['edu_gap_end_month'])
                    gap_start_date = edu_gap_start_month.name + "," + " " + gap_data['edu_gap_start_year']
                    gap_end_date = edu_gap_end_month.name + "," + " " + gap_data['edu_gap_end_year']

                    models.Gap.objects.update_or_create(candidate_id=user_id, profile_id=models.Profile.objects.get(
                        id=request.session['profile_id']),
                                                        record_id=gap_data['record_id'], type="education",
                                                        defaults={'start_date': gap_start_date,
                                                                  'end_date': gap_end_date,
                                                                  'reason': gap_data['gap_reason']})

        certiData = json.loads(request.POST.get('certi_data'))
        for i in certiData:
            for j in certiData[i]:
                certificate_data = certiData[i][j]
                attached_file = request.FILES.get('certi_file' + certificate_data['record_id'], None)
                summary = certificate_data['c_summary']
                summary = re.sub('\s+style="(.*?)"', "", summary)
                if certificate_data['c_certificate_name'] and certificate_data['c_certificate_organization'] and \
                        certificate_data['c_certificate_year']:
                    TempCertificationAttachment, created = models.CandidateCertificationAttachment.objects.update_or_create(
                        candidate_id=user_id, record_id=certificate_data['record_id'],
                        profile_id=models.Profile.objects.get(id=request.session['profile_id']),
                        defaults={'name_of_certificate': certificate_data['c_certificate_name'],
                                  'institute_organisation': certificate_data['c_certificate_organization'],
                                  'summary': summary,
                                  'attached_certificate': attached_file,
                                  'year': certificate_data['c_certificate_year']})
        return HttpResponse(True)
    else:
        return HttpResponse(False)


@login_required(login_url="/")
def work_experience_temp(request):
    if request.method == 'POST':
        updatedData = json.loads(request.POST.get('exp_data'))
        user_id = User.objects.get(email=request.user.email)
        for i in updatedData:
            for j in updatedData[i]:
                work_experience = updatedData[i][j]
                exp_start_month = models.Month.objects.get(id=work_experience['exp_start_month'])
                # print('\n\n\n\n\n',work_experience['exp_current_checkbox'])
                exp_start_date = exp_start_month.name + "," + " " + work_experience['exp_start_year']
                if work_experience['exp_current_checkbox']:
                    exp_end_date = 'present'
                    end_salary = 'present'
                else:
                    exp_end_month = models.Month.objects.get(id=work_experience['exp_end_month'])
                    exp_end_date = exp_end_month.name + "," + " " + work_experience['exp_end_year']
                    end_salary = work_experience['w_end_salary']
                w_job_description = work_experience['w_job_description']
                w_job_description = re.sub('\s+style="(.*?)"', "", w_job_description)
                company, com_created = models.Company.objects.update_or_create(
                    company_name=work_experience['c_company_name'])
                temp_experience, created = models.CandidateExperience.objects.update_or_create(
                    record_id=work_experience['record_id'], candidate_id=user_id,
                    profile_id=models.Profile.objects.get(id=request.session['profile_id']),
                    defaults={'job_profile_name': work_experience['c_job_profile'], 'company': company,
                              'start_date': exp_start_date, 'end_date': exp_end_date,
                              'start_salary': work_experience['w_start_salary'],
                              'end_salary': end_salary,
                              'job_description_responsibility': w_job_description})
                attached_file = request.FILES.getlist('file' + work_experience['record_id'], None)
                attached_file_name = request.POST.getlist('file_name' + work_experience['record_id'], None)
                for (file_name, file) in zip(attached_file_name, attached_file):
                    models.CandidateExpDocuments.objects.create(candidate_id=user_id, candidate_exp_id=temp_experience,
                                                                record_id=work_experience['record_id'],
                                                                document_name=file_name,
                                                                exp_document=file)

        if request.POST.get('gap_checkbox') == 'true':
            gapData = json.loads(request.POST.get('gap_data'))
            for i in gapData:
                for j in gapData[i]:
                    gap_data = gapData[i][j]

                    exp_gap_start_month = models.Month.objects.get(id=gap_data['exp_gap_start_month'])
                    exp_gap_end_month = models.Month.objects.get(id=gap_data['exp_gap_end_month'])
                    gap_start_date = exp_gap_start_month.name + "," + " " + gap_data['exp_gap_start_year']
                    gap_end_date = exp_gap_end_month.name + "," + " " + gap_data['exp_gap_end_year']

                    models.Gap.objects.update_or_create(candidate_id=user_id, profile_id=models.Profile.objects.get(
                        id=request.session['profile_id']),
                                                        record_id=gap_data['record_id'], type="experience",
                                                        defaults={'start_date': gap_start_date,
                                                                  'end_date': gap_end_date,
                                                                  'reason': gap_data['gap_reason']})

        portfolioData = json.loads(request.POST.get('portfolio_data'))
        for i in portfolioData:
            for j in portfolioData[i]:
                portfolio = portfolioData[i][j]
                attached_file = request.FILES.get('portfolio_file' + portfolio['record_id'], None)
                project_learning = portfolio['project_learning']
                project_learning = re.sub('\s+style="(.*?)"', "", w_job_description)
                if portfolio['project_year'] and portfolio['project_title'] and portfolio['project_description']:
                    portfolio_id, created = models.CandidatePortfolio.objects.update_or_create(candidate_id=user_id,
                                                                                               profile_id=
                                                                                               models.Profile.objects.get(
                                                                                                   id=request.session[
                                                                                                       'profile_id']),
                                                                                               record_id=portfolio[
                                                                                                   'record_id'],
                                                                                               defaults={
                                                                                                   'year': portfolio[
                                                                                                       'project_year'],
                                                                                                   'project_title':
                                                                                                       portfolio[
                                                                                                           'project_title'],
                                                                                                   'description':
                                                                                                       portfolio[
                                                                                                           'project_description'],
                                                                                                   'link': portfolio[
                                                                                                       'project_website'],
                                                                                                   'project_document': attached_file,
                                                                                                   'learning_from_project':
                                                                                                       project_learning})
        return HttpResponse(True)
    else:
        return HttpResponse(False)


@login_required(login_url="/")
def skill_temp(request):
    if request.method == 'POST':
        updatedData = json.loads(request.body.decode('UTF-8'))
        user_id = models.User.objects.get(email=request.user.email)
        for i in updatedData['total_skills']:
            for j in updatedData['total_skills'][i]:
                skill = updatedData['total_skills'][i][j]
                skill_id, created = models.Skill.objects.get_or_create(name=skill['skill_name'])
                models.CandidateSkillUserMap.objects.update_or_create(candidate_id=user_id,
                                                                      profile_id=models.Profile.objects.get(
                                                                          id=request.session['profile_id']),
                                                                      record_id=skill['record_id'],
                                                                      defaults={'skill': skill_id,
                                                                                'total_exp': skill[
                                                                                    'skill_total_experience'],
                                                                                'last_used': skill['last_used']})
        return HttpResponse(True)
    else:
        return HttpResponse(False)


@login_required(login_url="/")
def other_temp(request):
    if request.method == 'POST':
        user_id = models.User.objects.get(email=request.user.email)
        languageData = json.loads(request.POST.get('languages_data'))
        for i in languageData:
            for j in languageData[i]:
                language_data = languageData[i][j]
                language = models.Languages.objects.get(id=language_data['c_language'])
                fluency = models.Fluency.objects.get(id=language_data['c_fluency'])
                candidate_language, created = models.CandidateLanguage.objects.update_or_create(
                    record_id=language_data['record_id'], candidate_id=user_id,
                    profile_id=models.Profile.objects.get(id=request.session['profile_id']),
                    defaults={
                        'language_id': language,
                        'fluency_id': fluency})
        awardData = json.loads(request.POST.get('awards_data'))
        for i in awardData:
            for j in awardData[i]:
                award_data = awardData[i][j]
                if award_data['award_title'] and award_data['award_date'] and award_data['awarder']:
                    award, created = models.CandidateAward.objects.update_or_create(candidate_id=user_id,
                                                                                    profile_id=models.Profile.objects.get(
                                                                                        id=request.session[
                                                                                            'profile_id']),
                                                                                    record_id=award_data['record_id'],
                                                                                    defaults={
                                                                                        'title': award_data[
                                                                                            'award_title'],
                                                                                        'year': award_data[
                                                                                            'award_date'],
                                                                                        'awarder': award_data[
                                                                                            'awarder']})
        socialData = json.loads(request.POST.get('social_data'))
        for i in socialData:
            for j in socialData[i]:
                social_data = socialData[i][j]
                # print(social_data)
                social, created = models.CandidateSocialNetwork.objects.update_or_create(candidate_id=user_id,
                                                                                         profile_id=models.Profile.objects.get(
                                                                                             id=request.session[
                                                                                                 'profile_id']),
                                                                                         record_id=social_data[
                                                                                             'record_id'], defaults={

                        'url': social_data['network_url'], 'network_name': social_data['network_name']})
        # models.CandidateSEO.objects.create(candidate_id=user_id)
        models.CandidateProfile.objects.filter(candidate_id=user_id).update(final_status=True)
        models.CandidateEducation.objects.filter(candidate_id=user_id).update(final_status=True)
        models.CandidateExperience.objects.filter(candidate_id=user_id).update(final_status=True)
        models.CandidateCertificationAttachment.objects.filter(candidate_id=user_id).update(final_status=True)
        models.CandidateSkillUserMap.objects.filter(candidate_id=user_id).update(final_status=True)
        models.CandidatePortfolio.objects.filter(candidate_id=user_id).update(final_status=True)
        all_profiles = models.Profile.objects.filter(candidate_id=User.objects.get(id=request.user.id))
        for m in all_profiles:
            m.active = False
            m.update_at = datetime.datetime.now()
            m.save()
        current_page = request.POST.get('profile_url')
        # print('\n\n\n\ncurrent_page >>>>>>>>>>>>', current_page)
        profile_url = current_page.split('/')[-1]
        profile = models.Profile.objects.get(url=profile_url)
        profile.active = True
        profile.save()
        return HttpResponse(True)
    else:
        return HttpResponse(False)


@login_required(login_url="/")
def remove_record(request):
    if request.method == 'POST':
        if request.POST.get('step') == 'education':
            models.CandidateEducation.objects.filter(record_id=request.POST.get('record_id'),
                                                     profile_id=models.Profile.objects.get(
                                                         id=request.session['profile_id']), candidate_id=(
                    models.User.objects.get(email=request.user.email))).delete()
        if request.POST.get('step') == 'work_experience':
            # print("WOOOOOOOOOOOOORK EXPERIENCE DEETELEDEDE")
            models.CandidateExperience.objects.filter(record_id=request.POST.get('record_id'),
                                                      profile_id=models.Profile.objects.get(
                                                          id=request.session['profile_id']), candidate_id=(
                    models.User.objects.get(email=request.user.email))).delete()
            models.CandidateExpDocuments.objects.filter(record_id=request.POST.get('record_id'),
                                                        profile_id=models.Profile.objects.get(
                                                            id=request.session['profile_id']), candidate_id=(
                    models.User.objects.get(email=request.user.email))).delete()
        if request.POST.get('step') == 'certificate':
            models.CandidateCertificationAttachment.objects.filter(record_id=request.POST.get('record_id'),
                                                                   profile_id=models.Profile.objects.get(
                                                                       id=request.session['profile_id']),
                                                                   candidate_id=(
                                                                       models.User.objects.get(
                                                                           email=request.user.email))).delete()
        if request.POST.get('step') == 'skill':
            models.CandidateSkillUserMap.objects.filter(record_id=request.POST.get('record_id'),
                                                        profile_id=models.Profile.objects.get(
                                                            id=request.session['profile_id']), candidate_id=(
                    models.User.objects.get(email=request.user.email))).delete()
        if request.POST.get('step') == 'portfolio':
            models.CandidatePortfolio.objects.filter(record_id=request.POST.get('record_id'),
                                                     profile_id=models.Profile.objects.get(
                                                         id=request.session['profile_id']), candidate_id=(
                    models.User.objects.get(email=request.user.email))).delete()
        if request.POST.get('step') == 'social':
            models.CandidateSocialNetwork.objects.filter(record_id=request.POST.get('record_id'),
                                                         profile_id=models.Profile.objects.get(
                                                             id=request.session['profile_id']), candidate_id=(
                    models.User.objects.get(email=request.user.email))).delete()
        if request.POST.get('step') == 'award':
            models.CandidateAward.objects.filter(record_id=request.POST.get('record_id'),
                                                 profile_id=models.Profile.objects.get(
                                                     id=request.session['profile_id']),
                                                 candidate_id=(
                                                     models.User.objects.get(email=request.user.email))).delete()
        if request.POST.get('step') == 'language':
            models.CandidateLanguage.objects.filter(record_id=request.POST.get('record_id'),
                                                    profile_id=models.Profile.objects.get(
                                                        id=request.session['profile_id']), candidate_id=(
                    models.User.objects.get(email=request.user.email))).delete()
        if request.POST.get('step') == 'other':
            models.CandidateOtherField.objects.filter(record_id=request.POST.get('record_id'),
                                                      profile_id=models.Profile.objects.get(
                                                          id=request.session['profile_id']), candidate_id=(
                    models.User.objects.get(email=request.user.email))).delete()
        if request.POST.get('step') == 'experience_gap':
            models.Gap.objects.filter(record_id=request.POST.get('record_id'),
                                      profile_id=models.Profile.objects.get(
                                          id=request.session['profile_id']),
                                      type="experience",
                                      candidate_id=(models.User.objects.get(email=request.user.email))).delete()
        if request.POST.get('step') == 'education_gap':
            models.Gap.objects.filter(record_id=request.POST.get('record_id'),
                                      profile_id=models.Profile.objects.get(
                                          id=request.session['profile_id']),
                                      type="education",
                                      candidate_id=(models.User.objects.get(email=request.user.email))).delete()

        return HttpResponse(True)
    else:
        return HttpResponse(False)


# def timeline(request,url):
#     # dictonary to convert month to number
#     month = {'January':1,
#         'February':2,
#         'March':3,
#         'April':4,
#         'May':5,
#         'June':6,
#         'July':7,
#         'August':8,
#         'September':9,
#         'October':10,
#         'November':11,
#         'December':12
#         }
#     profile_id_get=models.CandidateProfile.objects.get(url_name=url)
#     activeprofile=models.Profile.objects.get(candidate_id=profile_id_get.candidate_id,active=True)
#     hire={}
#     looking_job=models.CandidateSEO.objects.get(candidate_id=activeprofile.candidate_id)
#     company_data_status={}
#     # activeprofile=models.Profile.objects.get(id=profile_id_get.profile_id)
#     if activeprofile.active:
#         profile=profile_id_get.profile_id
#         candidate_id=''
#         if request.user.is_authenticated:
#             print('asdddasddas')
#             if request.user.is_company:
#                 candidate_id=profile_id_get.candidate_id_id
#                 hire=CandidateHire.objects.filter(profile_id=activeprofile.id,candidate_id=candidate_id,company_id=User.objects.get(id=request.user.id))
#                 company_data_status=models.company_data_request.objects.filter(profile_id=activeprofile.id,candidate_id=candidate_id,company_id=User.objects.get(id=request.user.id))
#             elif request.user.is_candidate:
#                 candidate_id=request.user.id
#         else:
#             candidate_id=profile_id_get.candidate_id.id
#         user = User.objects.get(id=activeprofile.candidate_id.id)
#         print()
#         count= 0
#         year_title_pairs={}
#         print("before hide field")
#         print("user is ",user)
#         print("profile is ",profile)
#         hidefield=models.Candidate_Hide_Fields.objects.get(candidate_id=user,profile_id=profile)
#         profile_show=models.CandidateProfile.objects.get(candidate_id=user,profile_id=profile)
#         skills = models.CandidateSkillUserMap.objects.filter(candidate_id =user,profile_id=profile)
#         start_years =[]
#         end_years =[]
#         skill_names = ''
#         last_used=0
#         if skills:
#             for i in skills:
#                 if i.last_used=='present':
#                     last_used=int(get_present_year())
#
#                 skill_names += i.skill.name +','
#                 start_year = int(last_used) - int(i.total_exp)
#                 start_years.append(start_year)
#                 end_years.append(last_used)
#         year_salary_pair =[]
#         company_names =[]
#         experiences = models.CandidateExperience.objects.filter(candidate_id=user,profile_id=activeprofile.id)
#         if experiences:
#             for i in experiences:
#                 company_names.append(i.company.company_name)
#                 end_salary=0
#                 end_date=0
#                 if i.end_date:
#                     salary_start_year  =int(i.start_date.split(',')[1])
#                     salary_start_year += month[i.start_date.split(',')[0]] /12
#                     salary_end_year=0
#                     if i.end_date=='present':
#                         end_date=int(get_present_year())
#                         salary_end_year = int(get_present_year())
#                         salary_end_year += month[get_present_month()] /12
#                     else:
#                         end_date=int(i.end_date.split(',')[1])
#                     if i.end_salary=='present':
#                         end_salary=i.start_salary
#                     year_salary_pair.append([salary_start_year,i.start_salary])
#                     year_salary_pair.append([salary_end_year,end_salary])
#                     if int(end_date) not in list(year_title_pairs.keys()):
#                         year_title_pairs[end_date] =[]
#                         year_title_pairs[end_date].append(i)
#                     else:
#                         year_title_pairs[end_date].append(i)
#                 # year_title_pairs.add(i.end_date.split(',')[1],i.job_profile_name)
#         company_names = ','.join(company_names)
#         educations = models.CandidateEducation.objects.filter(candidate_id = user,profile_id=activeprofile.id)
#         if educations:
#             for i in educations:
#                 count += 1
#                 if i.end_date:
#                     if int(i.end_date.split(',')[1]) not in list(year_title_pairs.keys()):
#                         year_title_pairs[int(i.end_date.split(',')[1])] =[]
#                         year_title_pairs[int(i.end_date.split(',')[1])].append(i)
#                     else:
#                         year_title_pairs[int(i.end_date.split(',')[1])].append(i)
#         certificates = models.CandidateCertificationAttachment.objects.filter(candidate_id=user,profile_id=activeprofile.id)
#         if certificates:
#             for i in certificates:
#                 count += 1
#                 if i.year:
#                     if int(i.year) not in list(year_title_pairs.keys()):
#                         year_title_pairs[int(i.year)] =[]
#                         year_title_pairs[int(i.year)].append(i)
#                     else:
#                         year_title_pairs[int(i.year)].append(i)
#         awards = models.CandidateAward.objects.filter(candidate_id=user,profile_id=activeprofile.id)
#         if awards:
#             for i in awards:
#                 count += 1
#                 if i.year:
#                     if int(i.year) not in list(year_title_pairs.keys()):
#                         year_title_pairs[int(i.year)] =[]
#                         year_title_pairs[int(i.year)].append(i)
#                     else:
#                         year_title_pairs[int(i.year)].append(i)
#         print(hidefield.edu_document)
#         portfolio = models.CandidatePortfolio.objects.filter(candidate_id=user,profile_id=activeprofile.id)
#         if portfolio:
#             for i in portfolio:
#                 count += 1
#                 if i.year:
#                     if int(i.year) not in list(year_title_pairs.keys()):
#                         year_title_pairs[int(i.year)] =[]
#                         year_title_pairs[int(i.year)].append(i)
#                     else:
#                         year_title_pairs[int(i.year)].append(i)
#         print(hidefield.edu_document)
#         gaps = models.Gap.objects.filter(candidate_id=user,profile_id = activeprofile.id)
#         print(gaps)
#         if gaps:
#             print("gaaaaaaaaaps ",gaps)
#             for i in gaps:
#                 print("enterrred for loop for jgaps")
#                 if i.end_date:
#                     if int(i.end_date.split(',')[1]) not in list(year_title_pairs.keys()):
#                         print("ifffffffffffffffffffffffffffffffffffffffffffffff")
#                         year_title_pairs[int(i.end_date.split(',')[1])] =[]
#                         year_title_pairs[int(i.end_date.split(',')[1])].append(i)
#                     else:
#                         year_title_pairs[int(i.end_date.split(',')[1])].append(i)
#
#         print(year_title_pairs)
#     sorted_key_list = sorted(year_title_pairs)
#     sorted_key_list.reverse()
#     job_preference=models.CandidateJobPreference.objects.filter(candidate_id=user)
#
#
#
#     return render(request,'candidate/candidate_resume.html',
#                   {'company_data_status':company_data_status,'looking_job':looking_job,'hire':hire,'profile':profile_id_get,'hidefield':hidefield,'profile_show':profile_show,'user':user,'experiences':experiences,'portfolios':portfolio,'educations':educations,'certificates':certificates,'awards':awards,'sorted_keys':sorted_key_list,'year_title_pairs':year_title_pairs,'start_years':start_years,'end_years':end_years,'skills':skill_names,'year_salary_pair':year_salary_pair,'company_names':company_names,'job_preference':job_preference})
@login_required(login_url="/")
def candidate_profile(request):
    existing_user = models.CandidateProfile.objects.filter(candidate_id=request.user.id).count()
    # context['existing_user'] = existing_user
    profile = models.CandidateProfile.objects.get(
        candidate_id=(models.User.objects.get(email=request.user.email)))
    education = models.CandidateEducation.objects.filter(
        candidate_id=(models.User.objects.get(email=request.user.email)))
    experience = models.CandidateExperience.objects.filter(
        candidate_id=(models.User.objects.get(email=request.user.email)))
    skills = models.CandidateSkillUserMap.objects.filter(
        candidate_id=(models.User.objects.get(email=request.user.email)))
    summary = models.CandidateSummary.objects.filter(
        candidate_id=(models.User.objects.get(email=request.user.email)))
    certificates = models.CandidateCertificationAttachment.objects.filter(
        candidate_id=(models.User.objects.get(email=request.user.email)))
    portfolio = models.CandidatePortfolio.objects.filter(
        candidate_id=(models.User.objects.get(email=request.user.email)))
    languages = models.CandidateLanguage.objects.filter(
        candidate_id=(models.User.objects.get(email=request.user.email)))
    return render(request, 'candidate/candidate_profile.html',
                  {'existing_user': 0, 'profile': profile, 'education': education,
                   'experience': experience, 'skills': skills, 'summary': summary,
                   'certificates': certificates, 'portfolio': portfolio, 'languages': languages})


def statistics_view(request):
    dict1 = {'a1': 1, 'a2': 2, 'a3': 3}
    sample_data = json.dumps(dict1)
    profile = models.CandidateProfile.objects.get(
        candidate_id=(models.User.objects.get(email=request.user.email)))
    return render(request, 'candidate/statistics.html', {'sample_data': sample_data, 'profile': profile})


def get_filter_options(request):
    # grouped_purchases = Purchase.objects.annotate(year=ExtractYear('time')).values('year').order_by('-year').distinct()
    # options = [purchase['year'] for purchase in grouped_purchases]

    return JsonResponse({
        'options': {'2020': 2020},
    })


def payment_method_chart(request):
    skills = models.CandidateSkillUserMap.objects.filter(
        candidate_id=(models.User.objects.get(email=request.user.email)))
    skill = []
    exp = []
    level = []
    for i in skills:
        skill.append(i.skill.name)
        exp.append(int(i.end_year) - int(i.start_year))
        level.append(i.level.fluency)
    # print("==================",skill)
    return JsonResponse({
        'title': 'Skills With Experience(years)',
        'data': {
            'labels': skill,
            'datasets': [
                {
                    'label': 'Skills',
                    'backgroundColor': generate_color_palette(len(skill)),
                    'borderColor': generate_color_palette(len(skill)),
                    'data': exp,
                },
            ]
        },
    })


def job_exp_Chart(request):
    c_experience = models.CandidateExperience.objects.filter(
        candidate_id=(models.User.objects.get(email=request.user.email)))
    experience = []
    exp = []
    for i in c_experience:
        experience.append(i.company.company_name)
        start_date = datetime.datetime.strptime(i.start_date, '%B, %Y')
        end_date = datetime.datetime.strptime(i.end_date, '%B, %Y')
        difference = relativedelta(end_date, start_date)
        final_dif = str(difference.years) + '.' + str(difference.months)
        exp.append(final_dif)

    return JsonResponse({
        'title': 'Experience in Years',
        'data': {
            'labels': experience,
            'datasets': [{
                'label': '',
                'backgroundColor': generate_color_palette(len(experience)),
                'borderColor': generate_color_palette(len(experience)),
                'data': exp,
            }]
        },
    })


def edu_per_chart(request):
    c_education = models.CandidateEducation.objects.filter(
        candidate_id=(models.User.objects.get(email=request.user.email)))
    degree = []
    grade = []
    exp = []
    for i in c_education:
        degree.append(i.degree.name)
        grade.append(i.grade)
        start_date = datetime.datetime.strptime(i.start_date, '%B, %Y')
        end_date = datetime.datetime.strptime(i.end_date, '%B, %Y')
        difference = relativedelta(end_date, start_date)
        final_dif = str(difference.years) + '.' + str(difference.months)
        exp.append(final_dif)
    return JsonResponse({
        'title': 'Education',
        'data': {
            'labels': degree,
            'datasets': [{
                'label': '',
                'backgroundColor': ["#3e95cd", "#8e5ea2", "#3cba9f", "#e8c3b9", "#c45850"],
                'borderColor': generate_color_palette(len(grade)),
                'data': exp,
            }]
        },
    })


# def candidate_web_profile(request,url_name):
#     profile = models.CandidateProfile.objects.get(url_name=url_name)
#     if request.user.id == profile.candidate_id.id:
#         is_self = True
#     else:
#         is_self = False
#     if profile:
#         education = models.CandidateEducation.objects.filter(candidate_id=profile.candidate_id)
#         experience = models.CandidateExperience.objects.filter(candidate_id=profile.candidate_id)
#         skills = models.CandidateSkillUserMap.objects.filter(candidate_id=profile.candidate_id)
#         summary = models.CandidateSummary.objects.filter(candidate_id=profile.candidate_id)
#         certificates = models.CandidateCertificationAttachment.objects.filter(candidate_id=profile.candidate_id)
#         portfolio = models.CandidatePortfolio.objects.filter(candidate_id=profile.candidate_id)
#         languages = models.CandidateLanguage.objects.filter(candidate_id=profile.candidate_id)
#         job_preference = models.CandidateJobPreference.objects.filter(candidate_id=profile.candidate_id)
#         job_preference_other = models.CandidateJobPreferenceOther.objects.filter(candidate_id=profile.candidate_id)
#         return render(request, 'candidate/candidate_web_profile.html',
#                       {'existing_user': 0, 'profile': profile, 'education': education,
#                        'experience': experience, 'skills': skills, 'summary': summary,
#                        'certificates': certificates, 'portfolio': portfolio, 'languages': languages,'is_self': is_self,
#                        'job_preference': job_preference,'job_preference_other': job_preference_other})
#     else:
#         return HttpResponse('Requested User Not Found')

# def get_city(request):
#     term = request.GET.get('term')
#     print('\n\nterm >>>>>>', term)
#     cities = models.City.objects.all().filter(city_name__icontains=term)
#     return JsonResponse(list(cities.values()), safe=False)


from django.db.models import Count, Sum


@login_required(login_url="/")
def toggle_field_state(request):
    element_tag = request.GET.get('name')
    # print("taaaaaag", element_tag)
    # print(request.user)
    active_profile = models.Profile.objects.get(id=request.session['active_profile_id'])
    candidatehidefields = models.Candidate_Hide_Fields.objects.get(candidate_id=request.user, profile_id=active_profile)
    if element_tag == 'email':
        if candidatehidefields.email == 0:
            candidatehidefields.email = 1
        elif candidatehidefields.email == 1:
            candidatehidefields.email = 0
        candidatehidefields.save()
        return HttpResponse(candidatehidefields.email)

    elif element_tag == 'exp_document':
        if candidatehidefields.exp_document == 0:
            candidatehidefields.exp_document = 1
        elif candidatehidefields.exp_document == 1:
            candidatehidefields.exp_document = 0
        candidatehidefields.save()
        return HttpResponse(candidatehidefields.edu_document)

    elif element_tag == 'edu_document':
        if candidatehidefields.edu_document == 0:
            candidatehidefields.edu_document = 1
        elif candidatehidefields.edu_document == 1:
            candidatehidefields.edu_document = 0
        candidatehidefields.save()
        return HttpResponse(candidatehidefields.edu_document)

    elif element_tag == 'certificate_document':
        if candidatehidefields.certificate_document == 0:
            candidatehidefields.certificate_document = 1
        elif candidatehidefields.certificate_document == 1:
            candidatehidefields.certificate_document = 0
        candidatehidefields.save()
        return HttpResponse(candidatehidefields.certificate_document)

    elif element_tag == 'portfolio_document':
        if candidatehidefields.portfolio_document == 0:
            candidatehidefields.portfolio_document = 1
        elif candidatehidefields.portfolio_document == 1:
            candidatehidefields.portfolio_document = 0
        candidatehidefields.save()
        return HttpResponse(candidatehidefields.portfolio_document)

    elif element_tag == 'contact':
        if candidatehidefields.contact == 0:
            candidatehidefields.contact = 1
        elif candidatehidefields.contact == 1:
            candidatehidefields.contact = 0
        candidatehidefields.save()
        return HttpResponse(candidatehidefields.contact)

        # candidatehidefields.save()
    # print("emaiiiiiiillllllll",candidatehidefields.email)
    # print("iddd",request.user.id)
    # print(candidatehidefields)
    # return HttpResponse(candidatehidefields.email)    


@login_required(login_url="/")
def add_profile(request):
    # print("heeeeeeelllllasdaslo")

    random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=15))
    # print(random_string)
    #    all_profiles = models.Profile.objects.filter(candidate_id=User.objects.get(id=request.user.id))
    #    for m in all_profiles:
    #       m.active = False
    #      m.update_at=datetime.datetime.now()
    #     m.save()
    profile = models.Profile.objects.create(candidate_id=User.objects.get(id=request.user.id), url=random_string)
    print('\n\n\nprofile obj', profile)
    candidatehidefield = models.Candidate_Hide_Fields.objects.create(candidate_id=User.objects.get(id=request.user.id),
                                                                     profile_id=profile)
    request.session['profile_id'] = profile.id
    return redirect('candidate:upload_resume_add', url=random_string)


@login_required(login_url="/")
def add_profile_detail(request, url):
    return redirect('candidate:home')


@login_required(login_url="/")
def toggle_profile(request):
    profile_id = request.GET.get('id')
    # print("profille  iddddddddddddddddddddddddd", profile_id)
    profiles = models.Profile.objects.filter(candidate_id=request.user)
    # print(profiles)
    for i in profiles:
        if int(i.id) == int(profile_id):
            i.active = True
            i.update_at = datetime.datetime.now()
            del request.session['active_profile_id']
            request.session['active_profile_id'] = i.id

        else:
            i.active = False
            i.update_at = datetime.datetime.now()
        i.save()
    active_p = models.Profile.objects.get(candidate_id=request.user, active=True)
    q = Elastic_Q('multi_match', query=active_p.candidate_id.email, fields=['email'])
    s = CandidateDocument.search().query(q).extra(size=10000)
    for hit in s:
        # print("emaioil", hit.email)
        if User.objects.filter(email=hit.email).exists():
            user = User.objects.get(email=hit.email)
            try:
                hit.delete()
                user.indexing()
            except:
                print("indexing was not called ")
    return JsonResponse(list(profiles.values()), safe=False)


@login_required(login_url="/")
def edit_profile(request, profile_id):
    context = {}
    profile_obj = models.Profile.objects.get(id=profile_id)
    user_id = User.objects.get(id=request.user.id)
    context['profile_id'] = profile_id
    request.session['profile_id'] = profile_id
    context['cities'] = models.City.objects.all()
    context['states'] = models.State.objects.all()
    context['country'] = models.Country.objects.all()
    context['months'] = models.Month.objects.all()
    context['Languages'] = models.Languages.objects.all()
    context['fluency'] = models.Fluency.objects.all()
    context['profile'] = models.CandidateProfile.objects.get(candidate_id=user_id, profile_id=profile_id)

    context['experience'] = models.CandidateExperience.objects.filter(candidate_id=user_id,
                                                                      profile_id=profile_id).order_by('record_id')
    context['education'] = models.CandidateEducation.objects.filter(candidate_id=user_id,
                                                                    profile_id=profile_id).order_by('record_id')
    context['portfolios'] = models.CandidatePortfolio.objects.filter(candidate_id=user_id,
                                                                     profile_id=profile_id).order_by('record_id')
    context['certificates'] = models.CandidateCertificationAttachment.objects.filter(candidate_id=user_id,
                                                                                     profile_id=profile_id).order_by(
        'record_id')
    context['awards'] = models.CandidateAward.objects.filter(candidate_id=user_id, profile_id=profile_id).order_by(
        'record_id')
    context['c_language'] = models.CandidateLanguage.objects.filter(candidate_id=user_id,
                                                                    profile_id=profile_id).order_by('record_id')
    context['skills'] = models.CandidateSkillUserMap.objects.filter(candidate_id=user_id,
                                                                    profile_id=profile_id).order_by('record_id')
    context['social_network'] = models.CandidateSocialNetwork.objects.filter(candidate_id=user_id,
                                                                             profile_id=profile_id).order_by(
        'record_id')
    context['exp_years'] = [str(yearrange) if yearrange <= 30 else '30+' for yearrange in range(32)]
    context['exp_months'] = [str(i) for i in range(12)]
    context['industry_type'] = models.IndustryType.objects.all()
    context['notice_period'] = models.NoticePeriod.objects.all()
    context['maritial_type'] = models.MaritalType.objects.all()
    context['gender'] = models.Gender.objects.all()
    context['preferred_cities'] = []
    context['education_gaps'] = models.Gap.objects.filter(type="education", profile_id=profile_obj)
    context['experience_gaps'] = models.Gap.objects.filter(type="experience", profile_id=profile_obj)

    if context['profile'].preferred_cities:
        for city_id in context['profile'].preferred_cities.split(","):
            city_obj = models.City.objects.get(id=city_id)
            context['preferred_cities'].append({'id': city_obj.id, 'city_name': city_obj.city_name})
            # context['candidate_selected_cities'] = candidate_selected_cities

    if request.method == 'POST':
        if request.POST.get('model_name') == 'personal_details':
            # print(request.POST)
            user_id.first_name = request.POST.get('firstname')
            user_id.last_name = request.POST.get('lastname')
            user_id.save()
            candidate_profile = models.CandidateProfile.objects.filter(candidate_id=user_id, profile_id=profile_obj)
            candidate_profile.update(dob=request.POST.get('dob'),
                                     contact_no=request.POST.get('number'),
                                     gender=models.Gender.objects.get(id=request.POST.get('gender')),
                                     marital_status=models.MaritalType.objects.get(
                                         id=request.POST.get('marital_status')),
                                     designation=request.POST.get('designation'),
                                     total_experience=float(
                                         request.POST.get('total_experience_year') + '.' + request.POST.get(
                                             'total_experience_month')),
                                     notice_period=models.NoticePeriod.objects.get(
                                         id=request.POST.get('notice_period')),
                                     technical_knowledge=request.POST.get('technical-knowledge'),
                                     about_me=request.POST.get('about-me'),
                                     current_salary=request.POST.get('current_salary'))
            if request.POST.get('country'):
                candidate_profile.update(country=models.Country.objects.get(id=request.POST.get('country')))

            try:
                candidate_profile.update(state=models.State.objects.get(id=request.POST.get('state')))

            except:
                candidate_profile.update(state=None)

            try:
                candidate_profile.update(city=models.City.objects.get(id=request.POST.get('city')))

            except:
                candidate_profile.update(city=None)

            # print(candidate_profile)

            if request.POST.get('salary_checkbox'):
                models.CandidateProfile.objects.filter(candidate_id=user_id, profile_id=profile_obj).update(
                    expected_salary_min='As Per Company',
                    expected_salary_max='As Per Company')
            else:
                models.CandidateProfile.objects.filter(candidate_id=user_id, profile_id=profile_obj).update(
                    expected_salary_min=request.POST.get('expected_salary_min'),
                    expected_salary_max=request.POST.get('expected_salary_max'))

            candidate_profile = models.CandidateProfile.objects.get(candidate_id=user_id, profile_id=profile_obj)
            # print("final candidate profile is",candidate_profile)
            context['profile'] = candidate_profile
            # print("context profile is",context['profile'])
            if request.FILES.get('user_image'):
                # for i in candidate_profile:
                candidate_profile.user_image = request.FILES.get('user_image')
                candidate_profile.save()
                context['profile'] = candidate_profile
                # print("context in file is",context['profile'])

        if request.POST.get('model_name') == 'experience':
            # print("\n\nrequuuuuuuuuuuuuest\n\n\n",request.POST)

            exp_start_month = models.Month.objects.get(id=request.POST.get('exp_start_month'))
            # print("============================>",exp_start_month)
            exp_start_date = exp_start_month.name + "," + " " + request.POST.get('exp_start_year')
            if request.POST.get('exp_current_checkbox1'):
                exp_end_date = 'present'
                end_salary = 'present'
            else:
                end_salary = request.POST.get('endSalary')
                exp_end_month = models.Month.objects.get(id=request.POST.get('exp_end_month'))
                exp_end_date = exp_end_month.name + "," + " " + request.POST.get('exp_end_year')

            company, created = models.Company.objects.get_or_create(
                company_name=request.POST.get('company-name'),
                defaults={'company_name': request.POST.get('company-name')},
            )
            try:
                experience = models.CandidateExperience.objects.get(candidate_id=user_id, profile_id=profile_id,
                                                                    record_id=request.POST.get('record_id'))
            except:
                experience = None

            # print("expereince is ",experience)
            # print("created value is",created)
            if experience:
                old_company = experience.company.company_name
                if created:
                    # print("something was created")
                    # print("media root is ",settings.MEDIA_ROOT)
                    path = settings.MEDIA_ROOT + "{}/Candidate_Experience/{}".format(experience.candidate_id.id,
                                                                                     company.company_name)
                    # print("paaaaaath",path,os.path.exists(path))
                    # print("does folder exist")
                    if not os.path.exists(path):
                        os.makedirs(path)
                    exp_docs = models.CandidateExpDocuments.objects.filter(candidate_exp_id=experience)
                    for i in exp_docs:
                        file_path = i.exp_document.name
                        file_name = file_path.split('/')
                        file_name = file_name[-1]

                        abs_path = i.exp_document.name

                        # print("\n\n\nabs path>>>>>>>>>>>>>>>>>>>.",abs_path)
                        # print("path",path)
                        shutil.move(abs_path, path)
                        i.exp_document.name = path + '/{}'.format(file_name)
                        i.save()
                        abs_path = abs_path[:len(abs_path) - len(file_name)]

                    try:
                        os.rmdir(abs_path)
                    except:
                        print("there were some files in the folder")

                else:
                    if experience.company.company_name != request.POST.get('company-name'):
                        path = settings.MEDIA_ROOT + "{}/Candidate_Experience/{}".format(experience.candidate_id.id,
                                                                                         request.POST.get(
                                                                                             'company-name'))

                        if not os.path.exists(path):
                            os.makedirs(path)
                        exp_docs = models.CandidateExpDocuments.objects.filter(candidate_exp_id=experience)
                        for i in exp_docs:
                            file_path = i.exp_document.name
                            file_name = file_path.split('/')
                            file_name = file_name[-1]

                            abs_path = i.exp_document.name
                            # print("\n\n\nabs path",abs_path)
                            # print("path",path)
                            shutil.move(abs_path, path)

                            i.exp_document.name = path + '/{}'.format(file_name)
                            i.save()
                            abs_path = abs_path[:len(abs_path) - len(file_name)]
                        try:
                            os.rmdir(abs_path)
                        except:
                            print("there were some files in the folder")

                models.CandidateExperience.objects.filter(candidate_id=user_id, profile_id=profile_id,
                                                          record_id=request.POST.get('record_id')).update(
                    job_profile_name=request.POST.get('job-name'), company=company,
                    start_date=exp_start_date,
                    end_date=exp_end_date, start_salary=request.POST.get('startSalary'),
                    end_salary=end_salary, job_description_responsibility=request.POST.get('job_desc'),
                    website=request.POST.get('website-name'), update_at=datetime.datetime.now())

                exp_documents = models.CandidateExpDocuments.objects.filter(candidate_id=user_id, profile_id=profile_id,
                                                                            record_id=request.POST.get('record_id'))

                # print("experience is ",experience)
                # print(exp_documents)
                for i in range(exp_documents.count()):
                    temp = exp_documents[i]

                    file_name = 'exp_docs_' + str(temp.id)
                    file = request.FILES.get(file_name)
                    # print("FILE IS ",file)
                    if file:
                        temp.exp_document.delete(save=True)
                        temp.exp_document = file
                        temp.save()
            else:

                experience = models.CandidateExperience.objects.create(candidate_id=user_id, profile_id=profile_obj,
                                                                       record_id=request.POST.get('record_id'),
                                                                       job_profile_name=request.POST.get('job-name'),
                                                                       company=company,
                                                                       start_date=exp_start_date,
                                                                       end_date=exp_end_date,
                                                                       start_salary=request.POST.get('startSalary'),
                                                                       end_salary=request.POST.get('endSalary'),
                                                                       job_description_responsibility=request.POST.get(
                                                                           'job_desc'),
                                                                       website=request.POST.get('website-name'),
                                                                       update_at=datetime.datetime.now(),
                                                                       create_at=datetime.datetime.now(),
                                                                       final_status=True
                                                                       )

            files = request.FILES.getlist('exp_docs_new')
            names = request.POST.getlist('exp_docs_name')
            # print('names',names)
            # print("files ",files)
            # print("==================>",experience)
            record_ids = models.CandidateExpDocuments.objects.filter(candidate_exp_id=experience).values_list(
                'record_id', flat=True)
            # print("record ids",record_ids)

            if record_ids:
                max_record_id = int(max(record_ids))
            else:
                max_record_id = 0
            # print("max ")
            count = 0
            for (file_name, file) in zip(names, files):
                count += 1
                models.CandidateExpDocuments.objects.create(candidate_id=user_id,
                                                            profile_id=profile_obj,
                                                            record_id=max_record_id + count,
                                                            candidate_exp_id=experience,
                                                            exp_document=file,
                                                            document_name=file_name
                                                            )

        if request.POST.get('model_name') == 'portfolio':
            # print(request.POST)
            try:
                portfolio = models.CandidatePortfolio.objects.get(candidate_id=user_id, profile_id=profile_id,
                                                                  record_id=request.POST.get('record_id'))
            except:
                portfolio = None

            if portfolio:
                # print('\n\n\nproject_year', request.POST.get('project_year'))
                old_project_title = portfolio.project_title
                if portfolio.project_title != request.POST.get('project-title'):
                    # portfolio.project_title = request.POST.get('project-title')
                    # portfolio.save()
                    path = settings.MEDIA_ROOT + "{}/Candidate_Portfolio/{}".format(portfolio.candidate_id.id,
                                                                                    request.POST.get('project-title'))
                    if not os.path.exists(path):
                        os.makedirs(path)

                    file_path = portfolio.project_document.name
                    file_name = file_path.split('/')
                    file_name = file_name[-1]

                    abs_path = portfolio.project_document.name
                    # print("abs path ",abs_path)
                    # print("path ",path)
                    shutil.move(abs_path, path)
                    portfolio.project_document.name = path + '/{}'.format(file_name)
                    portfolio.save()
                    abs_path = abs_path[:len(abs_path) - len(file_name)]
                    # print("updated path is ",abs_path)
                    os.rmdir(abs_path)
                # print("update was callllleed")
                portfolios = models.CandidatePortfolio.objects.filter(candidate_id=user_id, profile_id=profile_id,
                                                                      record_id=request.POST.get('record_id'))
                # print("the queryset is ",portfolios)
                portfolios.update(
                    project_title=request.POST.get('project-title'), link=request.POST.get('project_website1'),
                    year=request.POST.get('project_year'), description=request.POST.get('project_description'),
                    learning_from_project=request.POST.get('learning_from_project'), update_at=datetime.datetime.now())

                file_name = "portfolio_docs_" + str(portfolio.id)
                # print("file_name is ",file_name)
                file = request.FILES.get(file_name)
                # print("the file in request post portfolio is",file)
                for i in portfolios:
                    if file:
                        i.project_document.delete(save=True)
                        i.project_document = file
                        i.save()
            else:
                models.CandidatePortfolio.objects.create(candidate_id=user_id,
                                                         profile_id=profile_obj,
                                                         record_id=request.POST.get('record_id'),
                                                         project_title=request.POST.get('project-title'),
                                                         link=request.POST.get('project_website1'),
                                                         year=request.POST.get('project_year'),
                                                         description=request.POST.get('project_description'),
                                                         learning_from_project=request.POST.get(
                                                             'learning_from_project'),
                                                         create_at=datetime.datetime.now(),
                                                         update_at=datetime.datetime.now(),
                                                         project_document=request.FILES.get('portfolio_docs_new'))

        if request.POST.get('model_name') == 'education':
            # print("MEEEEEEEEEEEEEEEEEEEEEDIAAAAAAAAAA",settings.MEDIA_ROOT)
            university, created = models.UniversityBoard.objects.get_or_create(
                name=request.POST.get('university_board'),
                defaults={'name': request.POST.get('university_board')},
            )
            degree, created = models.Degree.objects.get_or_create(
                name=request.POST.get('degree-name'), defaults={'name': request.POST.get('degree-name')})

            try:
                education = models.CandidateEducation.objects.get(candidate_id=user_id, profile_id=profile_id,
                                                                  record_id=request.POST.get('record_id'))
            except:
                education = None

            edu_start_month = models.Month.objects.get(id=request.POST.get('edu_start_month'))
            edu_end_month = models.Month.objects.get(id=request.POST.get('edu_end_month'))
            edu_start_date = edu_start_month.name + "," + " " + request.POST.get('edu_start_year')
            edu_end_date = edu_end_month.name + "," + " " + request.POST.get('edu_end_year')

            if education:

                old_degree = education.degree.name
                if created:

                    # print("something was created")
                    # print("media root is ",settings.MEDIA_ROOT)
                    path = settings.MEDIA_ROOT + "{}/Candidate_Education/{}".format(education.candidate_id.id,
                                                                                    degree.name)
                    # print("paaaaaath",path,os.path.exists(path))
                    # print("does folder exist")
                    if not os.path.exists(path):
                        os.makedirs(path)
                    file_path = education.certificate.name
                    file_name = file_path.split('/')
                    file_name = file_name[-1]

                    abs_path = education.certificate.name

                    # print("abs path",abs_path)
                    # print("path",path)
                    shutil.move(abs_path, path)
                    education.certificate.name = path + '/{}'.format(file_name)
                    education.save()
                    abs_path = abs_path[:len(abs_path) - len(file_name)]
                    os.rmdir(abs_path)
                else:
                    if education.degree.name != request.POST.get('degree-name'):
                        path = settings.MEDIA_ROOT + "{}/Candidate_Education/{}".format(education.candidate_id.id,
                                                                                        request.POST.get('degree-name'))

                        if not os.path.exists(path):
                            os.makedirs(path)
                        file_path = education.certificate.name
                        file_name = file_path.split('/')
                        file_name = file_name[-1]

                        abs_path = education.certificate.name

                        # print("abs path",abs_path)
                        # print("path",path)
                        shutil.move(abs_path, path)
                        education.certificate.name = path + '/{}'.format(file_name)
                        education.save()
                        abs_path = abs_path[:len(abs_path) - len(file_name)]
                        os.rmdir(abs_path)

                educations = models.CandidateEducation.objects.filter(candidate_id=user_id, profile_id=profile_id,
                                                                      record_id=request.POST.get('record_id'))
                educations.update(
                    university_board=university, degree=degree, start_date=edu_start_date,
                    end_date=edu_end_date, summary=request.POST.get('summary'),
                    update_at=datetime.datetime.now(), grade=request.POST.get('edu_grade'))

                # educations = models.CandidateEducation.objects.filter(candidate_id=user_id, profile_id=profile_id,
                #                                          record_id=request.POST.get('record_id'))

                file_name = 'edu_docs_' + str(education.id)
                file = request.FILES.get(file_name)

                for i in educations:
                    if file:
                        i.certificate.delete(save=True)
                        i.certificate = file
                        i.save()
                # for i in educations:
                #     file_name = 'edu_docs_'+str(i.id)
                #     print("file_name",file_name)
                #     file = request.FILES.get(file_name)
                #     print("file",file)
                #     if file:
                #         i.certificate = file
                #         i.save()
            else:
                models.CandidateEducation.objects.create(candidate_id=user_id, profile_id=profile_obj,
                                                         record_id=request.POST.get('record_id'),
                                                         university_board=university,
                                                         degree=degree,
                                                         start_date=edu_start_date,
                                                         end_date=edu_end_date,
                                                         summary=request.POST.get('summary'),
                                                         create_at=datetime.datetime.now(),
                                                         update_at=datetime.datetime.now(),
                                                         grade=request.POST.get('edu_grade'),
                                                         certificate=request.FILES.get('edu_docs_new'),
                                                         final_status=True)

        if request.POST.get('model_name') == 'certificate':
            # print("POOOOOST ",request.POST)
            # print("fiiiiiiiiiiiles",request.FILES)
            certificate_obj = models.CandidateCertificationAttachment.objects.filter(candidate_id=user_id,
                                                                                     profile_id=profile_id,
                                                                                     record_id=request.POST.get(
                                                                                         'record_id'))
            if certificate_obj.exists():

                for i in certificate_obj:
                    if i.name_of_certificate != request.POST.get('certificate-name'):
                        old_certificate_name = i.name_of_certificate
                        path = settings.MEDIA_ROOT + '{}/Candidate_Certificate/{}'.format(i.candidate_id.id,
                                                                                          request.POST.get(
                                                                                              'certificate-name'))

                        if not os.path.exists(path):
                            os.makedirs(path)

                        file_path = i.attached_certificate.name
                        file_name = file_path.split('/')
                        file_name = file_name[-1]

                        abs_path = i.attached_certificate.name
                        # print("abs path ",abs_path)
                        # print("path ",path)
                        shutil.move(abs_path, path)
                        i.attached_certificate.name = path + '/{}'.format(file_name)
                        i.save()
                        abs_path = abs_path[:len(abs_path) - len(file_name)]
                        # print("updated path is ",abs_path)
                        os.rmdir(abs_path)

                certificates = models.CandidateCertificationAttachment.objects.filter(candidate_id=user_id,
                                                                                      profile_id=profile_id,
                                                                                      record_id=request.POST.get(
                                                                                          'record_id'))
                certificates.update(name_of_certificate=request.POST.get('certificate-name'),
                                    institute_organisation=request.POST.get('certificate-organization'),
                                    year=request.POST.get('certificate-year'),
                                    summary=request.POST.get('certificate-summary'),
                                    update_at=datetime.datetime.now())

                if request.FILES.get('certificate-file'):
                    for i in certificates:
                        i.attached_certificate.delete(save=True)
                        i.attached_certificate = request.FILES.get('certificate-file')
                        i.save()
            else:
                certificate_obj.create(candidate_id=user_id, profile_id=profile_obj,
                                       record_id=request.POST.get('record_id'),
                                       name_of_certificate=request.POST.get('certificate-name'),
                                       institute_organisation=request.POST.get('certificate-organization'),
                                       year=request.POST.get('certificate-year'),
                                       attached_certificate=request.FILES.get('certificate-file'),
                                       summary=request.POST.get('certificate-summary'))
        if request.POST.get('model_name') == 'award':
            award_obj = models.CandidateAward.objects.filter(candidate_id=user_id, profile_id=profile_id,
                                                             record_id=request.POST.get('record_id'))
            if award_obj.exists():
                award_obj.update(title=request.POST.get('award-name'), year=request.POST.get('award-year'),
                                 awarder=request.POST.get('award-awarder'), update_at=datetime.datetime.now())
            else:
                models.CandidateAward.objects.create(candidate_id=user_id, profile_id=profile_obj,
                                                     record_id=request.POST.get('record_id'),
                                                     title=request.POST.get('award-name'),
                                                     year=request.POST.get('award-year'),
                                                     awarder=request.POST.get('award-awarder'))
        if request.POST.get('model_name') == 'language':
            language_id = models.Languages.objects.get(id=request.POST.get('language'))
            fluency_id = models.Fluency.objects.get(id=request.POST.get('fluency'))
            language_obj = models.CandidateLanguage.objects.filter(candidate_id=user_id, profile_id=profile_id,
                                                                   record_id=request.POST.get('record_id'))
            if language_obj.exists():
                language_obj.update(language_id=language_id, fluency_id=fluency_id)
            else:
                models.CandidateLanguage.objects.create(candidate_id=user_id, profile_id=profile_obj,
                                                        record_id=request.POST.get('record_id'),
                                                        language_id=language_id, fluency_id=fluency_id)
        if request.POST.get('model_name') == 'skill':
            skill_id, created = models.Skill.objects.get_or_create(name=request.POST.get('skill-name'))
            skill_obj = models.CandidateSkillUserMap.objects.filter(candidate_id=user_id, profile_id=profile_id,
                                                                    record_id=request.POST.get('record_id'))
            if skill_obj.exists():
                skill_obj.update(skill=skill_id, total_exp=request.POST.get('skill_total_experience'),
                                 last_used=request.POST.get('skill-last-used'))
            else:
                models.CandidateSkillUserMap.objects.create(candidate_id=user_id, profile_id=profile_obj,
                                                            record_id=request.POST.get('record_id'), skill=skill_id,
                                                            total_exp=request.POST.get('skill_total_experience'),
                                                            last_used=request.POST.get('skill-last-used'))
        if request.POST.get('model_name') == 'social':
            print("\n\n\n\npoooost", request.POST)
            social_obj = models.CandidateSocialNetwork.objects.filter(candidate_id=user_id, profile_id=profile_id,
                                                                      record_id=request.POST.get('record_id'))
            if social_obj.exists():
                social_obj.update(
                    network_name=request.POST.get('network_name'),
                    url=request.POST.get('network-url'), update_at=datetime.datetime.now())
            else:
                models.CandidateSocialNetwork.objects.create(candidate_id=user_id, profile_id=profile_obj,
                                                             record_id=request.POST.get('record_id'),
                                                             network_name=request.POST.get('network_name'),
                                                             url=request.POST.get('network-url'),
                                                             update_at=datetime.datetime.now())
        if request.POST.get('model_name') == 'education_gap':
            print("\n\n\n\npoooost", request.POST)
            gap_obj = models.Gap.objects.filter(candidate_id=user_id, profile_id=profile_id,
                                                record_id=request.POST.get('record_id'), type="education")
            print("asasdasdasd", gap_obj)
            # social_obj = models.CandidateSocialNetwork.objects.filter(candidate_id=user_id, profile_id=profile_id,record_id=request.POST.get('record_id'))

            if gap_obj.exists():
                gap_obj.update(
                    start_date=models.Month.objects.get(
                        id=request.POST.get('edu_gap_start_month')).name + ", " + request.POST.get(
                        'edu_gap_start_year'),
                    end_date=models.Month.objects.get(
                        id=request.POST.get('edu_gap_end_month')).name + ", " + request.POST.get('edu_gap_end_year'),
                    reason=request.POST.get('edu_gap_reason'))
            else:
                models.Gap.objects.create(candidate_id=user_id, profile_id=profile_obj,
                                          record_id=request.POST.get('record_id'),
                                          start_date=models.Month.objects.get(id=request.POST.get(
                                              'edu_gap_start_month')).name + ", " + request.POST.get(
                                              'edu_gap_start_year'),
                                          end_date=models.Month.objects.get(
                                              id=request.POST.get('edu_gap_end_month')).name + ", " + request.POST.get(
                                              'edu_gap_end_year'),
                                          reason=request.POST.get('edu_gap_reason'),
                                          type="education")
        if request.POST.get('model_name') == 'experience_gap':
            print("\n\n\n\npoooost", request.POST)
            gap_obj = models.Gap.objects.filter(candidate_id=user_id, profile_id=profile_id,
                                                record_id=request.POST.get('record_id'), type="experience")
            print("asasdasdasd", gap_obj)
            # social_obj = models.CandidateSocialNetwork.objects.filter(candidate_id=user_id, profile_id=profile_id,record_id=request.POST.get('record_id'))

            if gap_obj.exists():
                gap_obj.update(
                    start_date=models.Month.objects.get(
                        id=request.POST.get('exp_gap_start_month')).name + ", " + request.POST.get(
                        'exp_gap_start_year'),
                    end_date=models.Month.objects.get(
                        id=request.POST.get('exp_gap_end_month')).name + ", " + request.POST.get('exp_gap_end_year'),
                    reason=request.POST.get('exp_gap_reason'))
            else:
                models.Gap.objects.create(candidate_id=user_id, profile_id=profile_obj,
                                          record_id=request.POST.get('record_id'),
                                          start_date=models.Month.objects.get(id=request.POST.get(
                                              'exp_gap_start_month')).name + ", " + request.POST.get(
                                              'exp_gap_start_year'),
                                          end_date=models.Month.objects.get(
                                              id=request.POST.get('exp_gap_end_month')).name + ", " + request.POST.get(
                                              'exp_gap_end_year'),
                                          reason=request.POST.get('exp_gap_reason'),
                                          type="experience")
    return render(request, 'candidate/candidate_profile_edit.html', context)


@login_required(login_url="/")
def candidate_job_preference(request):
    if request.is_ajax():
        term = request.GET.get('term')
        cities = models.City.objects.all().filter(city_name__icontains=term)
        return JsonResponse(list(cities.values()), safe=False)
    candidate_id = models.User.objects.get(id=request.user.id)
    context = {}
    context['seo'] = models.CandidateSEO.objects.get(candidate_id=request.user.id)
    if models.CandidateJobPreference.objects.filter(candidate_id=candidate_id).exists():
        context['candidate_preference_exist'] = True
        context['candidate_preference_get'] = models.CandidateJobPreference.objects.get(candidate_id=candidate_id)
        context['candidate_preference_other_get'] = models.CandidateJobPreferenceOther.objects.filter(
            candidate_id=candidate_id)
        candidate_selected_cities = []
        if context['candidate_preference_get'].relocation_cities:
            for city_id in context['candidate_preference_get'].relocation_cities.split(","):
                city_obj = models.City.objects.get(id=city_id)
                candidate_selected_cities.append({'id': city_obj.id, 'city_name': city_obj.city_name})
            context['candidate_selected_cities'] = candidate_selected_cities
    else:
        context['candidate_preference_exist'] = False
    context['job_types'] = models.CandidateJobPreference.job_type_choices
    context['number_of_employee'] = models.CandidateJobPreference.number_of_employee_choices
    context['working_day_types'] = models.CandidateJobPreference.working_day_choices
    context['preferred_shift_types'] = models.CandidateJobPreference.preferred_shift_choices
    if request.method == 'POST':
        print('================')
        print('================', request.POST.get('no-of-employee'))
        if request.POST.get('relocate') == 'on':
            relocation = True
        else:
            relocation = False
        relocation_cities = ','.join(map(str, request.POST.getlist('relocation_cities')))
        models.CandidateJobPreference.objects.update_or_create(candidate_id=candidate_id,
                                                               defaults={'job_type': request.POST.get('job-type'),
                                                                         'number_of_employee': request.POST.get(
                                                                             'no-of-employee'),
                                                                         'working_days': request.POST.get(
                                                                             'working-day'),
                                                                         'preferred_shift': request.POST.get(
                                                                             'shift-type'), 'relocation': relocation,
                                                                         'relocation_cities': relocation_cities
                                                                         })
        models.CandidateJobPreferenceOther.objects.all().delete()
        for (label, value) in zip(request.POST.getlist('label'), request.POST.getlist('value')):
            models.CandidateJobPreferenceOther.objects.update_or_create(candidate_id=candidate_id, label=label,
                                                                        value=value,
                                                                        defaults={
                                                                            'label': label,
                                                                            'value': value,
                                                                        })
        return redirect('candidate:home')
    return render(request, 'candidate/Dashbord-preference.html', context)


from django.db.models import Count, Sum


@login_required(login_url="/")
def hire_request(request):
    seo = models.CandidateSEO.objects.get(candidate_id=request.user.id)
    active = CandidateHire.objects.filter(candidate_id=request.user.id, request_status=1).values('id', 'message',
                                                                                                 'company_id',
                                                                                                 'candidate_id',
                                                                                                 'profile_id')
    new_request = CandidateHire.objects.filter(candidate_id=request.user.id, request_status=0).values('id', 'message',
                                                                                                      'company_id',
                                                                                                      'candidate_id',
                                                                                                      'profile_id')
    archive = CandidateHire.objects.filter(candidate_id=request.user.id, request_status=-1).values('id', 'message',
                                                                                                   'company_id',
                                                                                                   'candidate_id',
                                                                                                   'profile_id')
    print('========================', new_request)
    data_active = models.company_data_request.objects.filter(candidate_id=request.user.id, status=1).values('id',
                                                                                                            'message',
                                                                                                            'company_id',
                                                                                                            'candidate_id',
                                                                                                            'profile_id')
    data_new_request = models.company_data_request.objects.filter(candidate_id=request.user.id, status=0).values('id',
                                                                                                                 'message',
                                                                                                                 'company_id',
                                                                                                                 'candidate_id',
                                                                                                                 'profile_id')
    data_archive = models.company_data_request.objects.filter(candidate_id=request.user.id, status=-2).values('id',
                                                                                                              'message',
                                                                                                              'company_id',
                                                                                                              'candidate_id',
                                                                                                              'profile_id')
    print('========================', data_new_request)
    profile_get = models.Profile.objects.get(candidate_id=request.user.id, active=True)
    userdata = models.CandidateProfile.objects.get(candidate_id=request.user.id, profile_id=profile_get.id)
    return render(request, 'candidate/Dashbord-request.html',
                  {'userdata': userdata, 'seo': seo, 'active': active, 'new_request': new_request, 'archive': archive,
                   'data_active': data_active, 'data_new_request': data_new_request, 'data_archive': data_archive})


@login_required(login_url="/")
def accept_request(request, profile_id, company_id, hire_id):
    if request.method == "POST":
        # MessageModel.objects.create(user=User.objects.get(id=request.user.id),recipient=User.objects.get(id=company_id),body=request.POST.get('accept_message'),request_status=1)
        status_true = Messages.objects.filter(
            Q(sender_name=User.objects.get(id=company_id), receiver_name=User.objects.get(id=request.user.id),
              status=False) | Q(sender_name=User.objects.get(id=request.user.id),
                                receiver_name=User.objects.get(id=company_id), status=False))
        for i in status_true:
            i.status = True
            i.save()
        Messages.objects.create(sender_name=User.objects.get(id=request.user.id),
                                receiver_name=User.objects.get(id=company_id),
                                description=request.POST.get('accept_message'), status=True)
        CandidateHire.objects.filter(id=hire_id, candidate_id=request.user.id, company_id=company_id,
                                     profile_id=profile_id).update(request_status=1,
                                                                   message=request.POST.get('accept_message'))
        try:
            mail_subject = 'Accept Hire Request'
            html_content = render_to_string('accounts/candidate_hire_email.html',
                                            {'message': request.POST.get('accept_message')})
            to_email = User.objects.filter(id=company_id).values('email')[0]['email']
            from_email = settings.EMAIL_HOST_USER
            msg = EmailMultiAlternatives(mail_subject, mail_subject, from_email, to=[to_email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            # messages.sucess(request, 'Your account was inactive.')
            return redirect('candidate:hire_request')
        except BadHeaderError:
            print("email not send")
            messages.erroe(request, 'mail dose not send.')
            return redirect('candidate:hire_request')

    return redirect('candidate:hire_request')


@login_required(login_url="/")
def reject_request(request, profile_id, company_id, hire_id):
    if request.method == "POST":
        status_false = Messages.objects.filter(
            Q(sender_name=User.objects.get(id=company_id), receiver_name=User.objects.get(id=request.user.id),
              status=True) | Q(sender_name=User.objects.get(id=request.user.id),
                               receiver_name=User.objects.get(id=company_id), status=True))
        for i in status_false:
            i.status = False
            i.save()
        Messages.objects.create(sender_name=User.objects.get(id=request.user.id),
                                receiver_name=User.objects.get(id=company_id),
                                description=request.POST.get('reject_message'), status=False)
        CandidateHire.objects.filter(id=hire_id, candidate_id=request.user.id, company_id=company_id,
                                     profile_id=profile_id).update(request_status=-1,
                                                                   message=request.POST.get('reject_message'))
        try:
            mail_subject = 'Reject Hire Request'
            html_content = render_to_string('accounts/candidate_hire_email.html',
                                            {'message': request.POST.get('reject_message')})
            to_email = User.objects.filter(id=company_id).values('email')[0]['email']
            from_email = settings.EMAIL_HOST_USER
            msg = EmailMultiAlternatives(mail_subject, mail_subject, from_email, to=[to_email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            # messages.sucess(request, 'Your account was inactive.')
            return redirect('candidate:hire_request')
        except BadHeaderError:
            print("email not send")
            messages.erroe(request, 'mail dose not send.')
            return redirect('candidate:hire_request')

    return redirect('candidate:hire_request')


@login_required(login_url="/")
def data_accept_request(request, profile_id, company_id, data_id):
    if request.method == "POST":
        # MessageModel.objects.create(user=User.objects.get(id=request.user.id),recipient=User.objects.get(id=company_id),body=request.POST.get('accept_message'),request_status=1)
        models.company_data_request.objects.filter(id=data_id, candidate_id=request.user.id, company_id=company_id,
                                                   profile_id=profile_id).update(status=1, message=request.POST.get(
            'accept_message'))
    return redirect('candidate:hire_request')


@login_required(login_url="/")
def data_reject_request(request, profile_id, company_id, data_id):
    if request.method == "POST":
        # MessageModel.objects.create(user=User.objects.get(id=request.user.id),recipient=User.objects.get(id=company_id),body=request.POST.get('reject_message'),request_status=-1)
        models.company_data_request.objects.filter(id=data_id, candidate_id=request.user.id, company_id=company_id,
                                                   profile_id=profile_id).update(status=-2, message=request.POST.get(
            'reject_message'))
    return redirect('candidate:hire_request')


@login_required(login_url="/")
def charts(request):
    data = pd.read_csv("media/bar-chart.csv")
    json_data = data.to_json()

    print(data)

    print("json data", json_data)
    return render(request, 'candidate/chart-chartjs.html', {'json_data': json_data})


@login_required(login_url="/")
def save_resume(request):
    if request.method == 'POST':
        print('\n\n\ncandidate_resume', request.session['profile_id'])
        user_id = models.User.objects.get(email=request.user.email)
        profile = models.CandidateProfile.objects.get(candidate_id=user_id, profile_id=models.Profile.objects.get(
            id=request.session['profile_id']))
        profile.resume = request.FILES.get('candidate_resume')
        profile.save()
        return HttpResponse(True)
    else:
        return HttpResponse(False)


@login_required(login_url="/")
def create_resume_pass(request):
    if request.method == 'POST':
        # print('\n\n\ncreate_resume_pass', request.POST.get('resume-pass'), request.session['profile_id'])
        user_id = models.User.objects.get(email=request.user.email)
        password = make_password(request.POST.get('resume-pass'))
        profile = models.CandidateProfile.objects.get(candidate_id=user_id, profile_id=models.Profile.objects.get(
            id=request.session['profile_id']))
        profile.resume_password = password
        profile.save()
        return HttpResponse(True)


@login_required(login_url="/")
def update_resume_pass(request):
    if request.method == 'POST':
        # del request.session['active_profile_id']
        print('===============create_resume_pass', request.POST.get('resume-pass'),
              request.session['active_profile_id'])
        user_id = models.User.objects.get(email=request.user.email)
        password = make_password(request.POST.get('resume-pass'))
        profile = models.CandidateProfile.objects.get(candidate_id=user_id, profile_id=models.Profile.objects.get(
            id=request.session['active_profile_id']))
        profile.resume_password = password
        profile.save()
        return HttpResponse(True)


def update_share_url(request):
    print('\n\n\ncreate_url', request.POST.get('share-url'))
    user_id = models.User.objects.get(email=request.user.email)
    url_name = request.POST.get('share-url')
    profile = models.CandidateProfile.objects.get(candidate_id=user_id, profile_id=models.Profile.objects.get(
        id=request.session['active_profile_id']))
    profile.custom_url = url_name
    profile.save()
    qr_share_link = "https://bidcruit.com/" + url_name + "/"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=6,
        border=4,
    )
    qr.add_data(qr_share_link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    blob = BytesIO()
    img.save(blob, 'JPEG')
    profile.qr_code.save(request.user.first_name + '.jpg', File(blob), save=True)
    return HttpResponse(True)


def check_sharing_url_is_valid(request):
    url = request.POST.get("url")
    print('===============', url)
    regex = re.compile('[@!#$%^&*()<>?/\|}{~:]')
    if (regex.search(url) == None):
        user_obj = models.CandidateProfile.objects.filter(custom_url=url).exists()
        print('===============', user_obj)
        if user_obj:
            print('exit')
            return HttpResponse(True)
        else:
            print('not exit')
            return HttpResponse(False)
    else:
        return HttpResponse('Invalid')


def file_download(request):
    data = json.loads(request.body.decode('UTF-8'))

    if request.method == 'POST':
        print("#####", data)
        recored_id = data['id']
        candidate_id = data['candidate_id']
        profile_id = data['profile_id']
        password_12 = data['password']
        file_password_get = models.CandidateProfile.objects.get(id=recored_id,
                                                                candidate_id=User.objects.get(id=candidate_id),
                                                                profile_id=models.Profile.objects.get(id=profile_id))

        check_file_password = check_password(password_12, file_password_get.resume_password)

        if check_file_password:
            return HttpResponse(True)
        else:
            return HttpResponse(False)
    else:
        return HttpResponse(False)


def look_for_job_check(request):
    print('==============-----------=====================')
    seo_obj, created = models.CandidateSEO.objects.get_or_create(candidate_id=User.objects.get(id=request.user.id))
    seo_obj.looking_for_job = True if request.GET.get('look_for_job_check') == 'on' else False
    seo_obj.google_search = True if request.GET.get('google_search_check') == 'on' else False
    seo_obj.save()
    return HttpResponse(True)


# def timeline(request, url):
#     # get_url=models.CandidateProfile.objects.filter(url_name=url)
#     # if len(get_url)!=0:
#     #     return redirect('timeline',get_url[0].custom_url)
#     # else:
#     #     return redirect('timeline',url)
#     # dictonary to convert month to number
#     month = {'January': 1,
#              'February': 2,
#              'March': 3,
#              'April': 4,
#              'May': 5,
#              'June': 6,
#              'July': 7,
#              'August': 8,
#              'September': 9,
#              'October': 10,
#              'November': 11,
#              'December': 12
#              }
#     profile_id_get = models.CandidateProfile.objects.filter(Q(url_name=url)|Q(custom_url=url))[0]
#     activeprofile = models.Profile.objects.get(candidate_id=profile_id_get.candidate_id, active=True)
#     x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#     ip=''
#     if x_forwarded_for:
#         ip = x_forwarded_for.split(',')[0]
#     else:
#         ip = request.META.get('REMOTE_ADDR')
#     try:
#         socket.inet_aton(ip)
#         ip_valid = True
#     except socket.error:
#         ip_valid = False
#     #----- check if ip adress is valid -----#
#     if ip_valid:
#         if not models.CandidateCounter.objects.filter(ip_address=ip).exists():
#             models.CandidateCounter.objects.create(candidate_id=profile_id_get.candidate_id,profile_id=models.Profile.objects.get(id=activeprofile.id),ip_address=ip)
#     hire = {}
#     looking_job = models.CandidateSEO.objects.get(candidate_id=activeprofile.candidate_id)
#     company_data_status = {}
#     # activeprofile=models.Profile.objects.get(id=profile_id_get.profile_id)
#     if activeprofile.active:
#         profile = profile_id_get.profile_id
#         candidate_id = ''
#         if request.user.is_authenticated:
#             print('asdddasddas')
#             if request.user.is_company:
#                 candidate_id = profile_id_get.candidate_id_id
#                 hire = CandidateHire.objects.filter(profile_id=activeprofile.id, candidate_id=candidate_id,
#                                                     company_id=User.objects.get(id=request.user.id))
#                 company_data_status = models.company_data_request.objects.filter(profile_id=activeprofile.id,
#                                                                                  candidate_id=candidate_id,
#                                                                                  company_id=User.objects.get(
#                                                                                      id=request.user.id))
#             elif request.user.is_candidate:
#                 candidate_id = request.user.id
#         else:
#             candidate_id = profile_id_get.candidate_id.id
#         user = User.objects.get(id=activeprofile.candidate_id.id)
#         count = 0
#         year_title_pairs = {}
#         print("before hide field")
#         print("user is ", user)
#         print("profile is ", profile)
#         hidefield = models.Candidate_Hide_Fields.objects.get(candidate_id=user, profile_id=profile)
#         profile_show = models.CandidateProfile.objects.get(candidate_id=user, profile_id=profile)
#         skills = models.CandidateSkillUserMap.objects.filter(candidate_id=user, profile_id=profile)
#         start_years = []
#         end_years = []
#         skill_names = ''
#         last_used = 0
#         if skills:
#             for i in skills:
#                 if i.last_used == 'present':
#                     last_used = int(get_present_year())

#                 skill_names += i.skill.name + ','
#                 start_year = int(last_used) - int(i.total_exp)
#                 start_years.append(start_year)
#                 end_years.append(last_used)
#         year_salary_pair = []
#         company_names = []
#         exp_seq={}
#         experiences = models.CandidateExperience.objects.filter(candidate_id=user, profile_id=activeprofile.id)
#         if experiences:
#             for i in experiences:
#                 company_names.append(i.company.company_name)
#                 end_salary = 0
#                 end_date = 0
#                 if i.end_date:
#                     salary_start_year = int(i.start_date.split(',')[1])
#                     salary_start_year += month[i.start_date.split(',')[0]] / 12
#                     salary_end_year = 0
#                     if i.end_date == 'present':
#                         end_date = int(get_present_year())
#                         salary_end_year = int(get_present_year())
#                         salary_end_year += month[get_present_month()] / 12
#                     else:
#                         end_date = int(i.end_date.split(',')[1])
#                     if i.end_salary == 'present':
#                         end_salary = i.start_salary
#                     year_salary_pair.append([salary_start_year, i.start_salary])
#                     year_salary_pair.append([salary_end_year, end_salary])
#                     if int(end_date) not in list(year_title_pairs.keys()):
#                         year_title_pairs[end_date] = []
#                         year_title_pairs[end_date].append(i)
#                         exp_seq[end_date] = []
#                         exp_seq[end_date].append(i)
#                     else:
#                         year_title_pairs[end_date].append(i)
#                         exp_seq[end_date].append(i)
#                 # year_title_pairs.add(i.end_date.split(',')[1],i.job_profile_name)
#         company_names = ','.join(company_names)
#         exp=dict(sorted(exp_seq.items(),reverse=True))
#         experiences =exp
#         educations = models.CandidateEducation.objects.filter(candidate_id=user, profile_id=activeprofile.id)
#         edu_seq={}
#         if educations:
#             for i in educations:
#                 count += 1
#                 if i.end_date:
#                     if int(i.end_date.split(',')[1]) not in list(year_title_pairs.keys()):
#                         year_title_pairs[int(i.end_date.split(',')[1])] = []
#                         year_title_pairs[int(i.end_date.split(',')[1])].append(i)
#                         edu_seq[int(i.end_date.split(',')[1])] = []
#                         edu_seq[int(i.end_date.split(',')[1])].append(i)
#                     else:
#                         year_title_pairs[int(i.end_date.split(',')[1])].append(i)
#                         edu_seq[int(i.end_date.split(',')[1])] = []
#                         edu_seq[int(i.end_date.split(',')[1])].append(i)
#         edu=dict(sorted(edu_seq.items(),reverse=True))
#         educations =edu
#         certificates = models.CandidateCertificationAttachment.objects.filter(candidate_id=user,
#                                                                               profile_id=activeprofile.id)
#         # cer_seq={}
#         # if certificates:
#         #     for i in certificates:
#         #         count += 1
#         #         if i.year:
#         #             if int(i.year) not in list(year_title_pairs.keys()):
#         #                 year_title_pairs[int(i.year)] = []
#         #                 year_title_pairs[int(i.year)].append(i)
#         #                 cer_seq[int(i.year)] = []
#         #                 cer_seq[int(i.year)].append(i)
#         #             else:
#         #                 year_title_pairs[int(i.year)].append(i)
#         #                 cer_seq[int(i.year)] = []
#         #                 cer_seq[int(i.year)].append(i)
#         # cer=dict(sorted(cer_seq.items(),reverse=True))
#         # certificates =cer
#         awards = models.CandidateAward.objects.filter(candidate_id=user, profile_id=activeprofile.id)
#         # awrd_seq={}
#         # if awards:
#         #     for i in awards:
#         #         count += 1
#         #         if i.year:
#         #             if int(i.year) not in list(year_title_pairs.keys()):
#         #                 year_title_pairs[int(i.year)] = []
#         #                 year_title_pairs[int(i.year)].append(i)
#         #                 awrd_seq[int(i.year)] = []
#         #                 awrd_seq[int(i.year)].append(i)
#         #             else:
#         #                 year_title_pairs[int(i.year)].append(i)
#         #                 awrd_seq[int(i.year)] = []
#         #                 awrd_seq[int(i.year)].append(i)
#         # awad=dict(sorted(awrd_seq.items(),reverse=True))
#         # awards =awad
#         # print(hidefield.edu_document)
#         portfolio = models.CandidatePortfolio.objects.filter(candidate_id=user, profile_id=activeprofile.id)
#         # port_seq={}
#         # if portfolio:
#         #     for i in portfolio:
#         #         count += 1
#         #         if i.year:
#         #             if int(i.year) not in list(year_title_pairs.keys()):
#         #                 year_title_pairs[int(i.year)] = []
#         #                 year_title_pairs[int(i.year)].append(i)
#         #                 port_seq[int(i.year)] = []
#         #                 port_seq[int(i.year)].append(i)
#         #             else:
#         #                 year_title_pairs[int(i.year)].append(i)
#         #                 port_seq[int(i.year)] = []
#         #                 port_seq[int(i.year)].append(i)
#         # port=dict(sorted(port_seq.items(),reverse=True))
#         # portfolio =port
#         gaps = models.Gap.objects.filter(candidate_id=user, profile_id=activeprofile.id)
#         print(gaps)
#         if gaps:
#             print("gaaaaaaaaaps ", gaps)
#             for i in gaps:
#                 print("enterrred for loop for jgaps")
#                 if i.end_date:
#                     if int(i.end_date.split(',')[1]) not in list(year_title_pairs.keys()):
#                         print("ifffffffffffffffffffffffffffffffffffffffffffffff")
#                         year_title_pairs[int(i.end_date.split(',')[1])] = []
#                         year_title_pairs[int(i.end_date.split(',')[1])].append(i)
#                     else:
#                         year_title_pairs[int(i.end_date.split(',')[1])].append(i)

#         print(year_title_pairs)
#         skills_show = models.CandidateSkillUserMap.objects.filter(candidate_id=user, profile_id=activeprofile.id)
#     sorted_key_list = sorted(year_title_pairs)
#     sorted_key_list.reverse()
#     job_preference = models.CandidateJobPreference.objects.filter(candidate_id=user)
#     skills_keywoard = models.CandidateSkillUserMap.objects.filter(candidate_id=user, profile_id=activeprofile.id)
#     keywoard=[]
#     for i in skills_show:
#         keywoard.append(i.skill.name)
#     preferredcity=profile_show.preferred_cities.split(',')
#     preferredcity=list(filter(None,preferredcity))
#     # preferredcity=list(filter('0',preferredcity))
#     # preferredcity=list(filter(0,preferredcity))
#     for i in preferredcity:
#         city = models.City.objects.get(id=int(i))
#         keywoard.append(city.city_name)
#     keywoard = ",".join(keywoard)
#     share_url=""
#     if profile_show.url_name:
#         share_url=profile_show.url_name
#     about_me=''
#     if profile_show.about_me:
#         about_me=profile_show.about_me
#         clean = re.compile('<.*?>')
#         about_me=re.sub(clean, '', about_me)

#     return render(request,'candidate/profile-third.html',
#                   {'company_data_status':company_data_status,'about_me':about_me,'share_url':share_url,'keywoard':keywoard,'skills_show':skills_show,'looking_job':looking_job,'hire':hire,'profile':profile_id_get,'hidefield':hidefield,'profile_show':profile_show,'user':user,'experiences':experiences,'portfolios':portfolio,'educations':educations,'certificates':certificates,'awards':awards,'sorted_keys':sorted_key_list,'year_title_pairs':year_title_pairs,'start_years':start_years,'end_years':end_years,'skills':skill_names,'year_salary_pair':json.dumps(year_salary_pair),'company_names':company_names,'job_preference':job_preference})


def timeline(request, url):
    profile_id_get = models.CandidateProfile.objects.filter(Q(url_name=url)|Q(custom_url=url))[0]
    # dictonary to convert month to number
    month = {'January': 1,
             'February': 2,
             'March': 3,
             'April': 4,
             'May': 5,
             'June': 6,
             'July': 7,
             'August': 8,
             'September': 9,
             'October': 10,
             'November': 11,
             'December': 12
             }
    # profile_id_get = models.CandidateProfile.objects.filter(Q(url_name=url)|Q(custom_url=url))[0]
    activeprofile = models.Profile.objects.get(candidate_id=profile_id_get.candidate_id, active=True)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    ip=''
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    try:
        socket.inet_aton(ip)
        ip_valid = True
    except socket.error:
        ip_valid = False
    #----- check if ip adress is valid -----#
    if ip_valid:
        if not models.CandidateCounter.objects.filter(candidate_id=profile_id_get.candidate_id,profile_id=models.Profile.objects.get(id=activeprofile.id),ip_address=ip).exists():
            models.CandidateCounter.objects.create(candidate_id=profile_id_get.candidate_id,profile_id=models.Profile.objects.get(id=activeprofile.id),ip_address=ip)
    hire = {}
    looking_job = models.CandidateSEO.objects.get(candidate_id=activeprofile.candidate_id)
    company_data_status = {}
    # activeprofile=models.Profile.objects.get(id=profile_id_get.profile_id)
    if activeprofile.active:
        profile = profile_id_get.profile_id
        candidate_id = ''
        if request.user.is_authenticated:
            print('asdddasddas')
            if request.user.is_company:
                candidate_id = profile_id_get.candidate_id_id
                hire = CandidateHire.objects.filter(profile_id=activeprofile.id, candidate_id=candidate_id,
                                                    company_id=User.objects.get(id=request.user.id))
                company_data_status = models.company_data_request.objects.filter(profile_id=activeprofile.id,
                                                                                 candidate_id=candidate_id,
                                                                                 company_id=User.objects.get(
                                                                                     id=request.user.id))
            elif request.user.is_candidate:
                candidate_id = request.user.id
        else:
            candidate_id = profile_id_get.candidate_id.id
        user = User.objects.get(id=activeprofile.candidate_id.id)
        count = 0
        year_title_pairs = {}
        print("before hide field")
        print("user is ", user)
        print("profile is ", profile)
        hidefield = models.Candidate_Hide_Fields.objects.get(candidate_id=user, profile_id=profile)
        profile_show = models.CandidateProfile.objects.get(candidate_id=user, profile_id=profile)
        skills = models.CandidateSkillUserMap.objects.filter(candidate_id=user, profile_id=profile)
        start_years = []
        end_years = []
        skill_names = ''
        if skills:
            for i in skills:
                if i.last_used == 'present':
                    last_used = int(get_present_year())
                else:
                    last_used = int(i.last_used)
                skill_names += i.skill.name + ','
                print("last useddd---------",last_used)
                print("exxaasdasas[---------",i.total_exp)
                start_year =  last_used - int(i.total_exp)
                start_years.append(start_year)
                end_years.append(last_used)
        year_salary_pair = []
        company_names = []
        exp_seq={}
        exp_pie_chart_companies = []
        exp_pie_chart_total_exp = []
        experiences = models.CandidateExperience.objects.filter(candidate_id=user, profile_id=activeprofile.id)
        for i in experiences:
            exp_pie_chart_companies.append(i.company.company_name)
            start_date = datetime.datetime.strptime(i.start_date, '%B, %Y')
            if i.end_date == 'present':
                current_date = datetime.datetime.now().strftime('%B') + ', ' + datetime.datetime.now().strftime('%Y')
                end_date = datetime.datetime.strptime(current_date, '%B, %Y')
            else:
                end_date = datetime.datetime.strptime(i.end_date, '%B, %Y')
            difference = relativedelta(end_date, start_date)
            final_dif = str(difference.years) + '.' + str(difference.months)
            exp_pie_chart_total_exp.append(float(final_dif))

        exp_df=''
        if experiences:
            q = experiences.values('start_date', 'end_date')
            exp_df = pd.DataFrame.from_records(q)
            exp_df['start_date'] = pd.to_datetime(exp_df.start_date, format='%B, %Y')
            now = datetime.datetime.now()
            now_date=now.strftime('%B')+', '+now.strftime('%Y')
            exp_df['end_date'] = exp_df['end_date'].apply(lambda x: now_date if x == "present" else x)
            exp_df['start_date'] =  pd.to_datetime(exp_df.start_date, format='%B, %Y')
            exp_df['type']='experience'
            exp_df['end_date'] =  pd.to_datetime(exp_df.end_date, format='%B, %Y')
            exp_df['s_year'] = pd.DatetimeIndex(exp_df['start_date']).year
            exp_df['e_year'] = pd.DatetimeIndex(exp_df['end_date']).year
            exp_df['s_month'] = pd.DatetimeIndex(exp_df['start_date']).month
            exp_df['e_month'] = pd.DatetimeIndex(exp_df['end_date']).month
            exp_df = exp_df.sort_values(by="start_date")
            exp_df = exp_df.rename(columns = {'start_date': 'start', 'end_date': 'end'}, inplace = False)
            for i in experiences:
                company_names.append(i.company.company_name)
                end_salary = 0
                end_date = 0
                if i.end_date:
                    salary_start_year = int(i.start_date.split(',')[1])
                    salary_start_year += month[i.start_date.split(',')[0]] / 12
                    salary_end_year = 0
                    if i.end_date == 'present':
                        end_date = int(get_present_year())
                        salary_end_year = int(get_present_year())
                        salary_end_year += month[get_present_month()] / 12
                    else:
                        end_date = int(i.end_date.split(',')[1])
                        salary_end_year = int(end_date)
                        salary_end_year += month[i.end_date.split(',')[0]] / 12
                    if i.end_salary == 'present':
                        end_salary = i.start_salary
                    else:
                        end_salary = i.end_salary
                    year_salary_pair.append([salary_start_year, i.start_salary])
                    year_salary_pair.append([salary_end_year, end_salary])
                    if int(end_date) not in list(year_title_pairs.keys()):
                        year_title_pairs[end_date] = []
                        year_title_pairs[end_date].append(i)
                        exp_seq[end_date] = []
                        exp_seq[end_date].append(i)
                    else:
                        year_title_pairs[end_date].append(i)
                        exp_seq[end_date].append(i)
                # year_title_pairs.add(i.end_date.split(',')[1],i.job_profile_name)
        company_names = ','.join(company_names)
        exp=dict(sorted(exp_seq.items(),reverse=True))
        experiences =exp
        educations = models.CandidateEducation.objects.filter(candidate_id=user, profile_id=activeprofile.id)
        edu_df=''
        edu_seq={}
        if educations:
            q = educations.values('start_date', 'end_date')
            edu_df = pd.DataFrame.from_records(q)
            edu_df['start_date'] =  pd.to_datetime(edu_df.start_date, format='%B, %Y')
            now = datetime.datetime.now()
            now_date=now.strftime('%B')+', '+now.strftime('%Y')
            edu_df['end_date'] = edu_df['end_date'].apply(lambda x: now_date if x == "present" else x)
            edu_df['start_date'] =  pd.to_datetime(edu_df.start_date, format='%B, %Y')
            edu_df['type']='education'
            edu_df['end_date'] =  pd.to_datetime(edu_df.end_date, format='%B, %Y')
            edu_df['s_year'] = pd.DatetimeIndex(edu_df['start_date']).year
            edu_df['e_year'] = pd.DatetimeIndex(edu_df['end_date']).year
            edu_df['s_month'] = pd.DatetimeIndex(edu_df['start_date']).month
            edu_df['e_month'] = pd.DatetimeIndex(edu_df['end_date']).month
            edu_df = edu_df.sort_values(by="start_date")
            edu_df = edu_df.rename(columns = {'start_date': 'start', 'end_date': 'end'}, inplace = False)
            for i in educations:
                count += 1
                if i.end_date:
                    if int(i.end_date.split(',')[1]) not in list(year_title_pairs.keys()):
                        year_title_pairs[int(i.end_date.split(',')[1])] = []
                        year_title_pairs[int(i.end_date.split(',')[1])].append(i)
                        edu_seq[int(i.end_date.split(',')[1])] = []
                        edu_seq[int(i.end_date.split(',')[1])].append(i)
                    else:
                        year_title_pairs[int(i.end_date.split(',')[1])].append(i)
                        edu_seq[int(i.end_date.split(',')[1])] = []
                        edu_seq[int(i.end_date.split(',')[1])].append(i)
        edu=dict(sorted(edu_seq.items(),reverse=True))
        educations =edu
        certificates = models.CandidateCertificationAttachment.objects.filter(candidate_id=user,
                                                                              profile_id=activeprofile.id)
        # cer_seq={}
        # if certificates:
        #     for i in certificates:
        #         count += 1
        #         if i.year:
        #             if int(i.year) not in list(year_title_pairs.keys()):
        #                 year_title_pairs[int(i.year)] = []
        #                 year_title_pairs[int(i.year)].append(i)
        #                 cer_seq[int(i.year)] = []
        #                 cer_seq[int(i.year)].append(i)
        #             else:
        #                 year_title_pairs[int(i.year)].append(i)
        #                 cer_seq[int(i.year)] = []
        #                 cer_seq[int(i.year)].append(i)
        # cer=dict(sorted(cer_seq.items(),reverse=True))
        # certificates =cer
        awards = models.CandidateAward.objects.filter(candidate_id=user, profile_id=activeprofile.id)
        # awrd_seq={}
        # if awards:
        #     for i in awards:
        #         count += 1
        #         if i.year:
        #             if int(i.year) not in list(year_title_pairs.keys()):
        #                 year_title_pairs[int(i.year)] = []
        #                 year_title_pairs[int(i.year)].append(i)
        #                 awrd_seq[int(i.year)] = []
        #                 awrd_seq[int(i.year)].append(i)
        #             else:
        #                 year_title_pairs[int(i.year)].append(i)
        #                 awrd_seq[int(i.year)] = []
        #                 awrd_seq[int(i.year)].append(i)
        # awad=dict(sorted(awrd_seq.items(),reverse=True))
        # awards =awad
        # print(hidefield.edu_document)
        portfolio = models.CandidatePortfolio.objects.filter(candidate_id=user, profile_id=activeprofile.id)
        # port_seq={}
        # if portfolio:
        #     for i in portfolio:
        #         count += 1
        #         if i.year:
        #             if int(i.year) not in list(year_title_pairs.keys()):
        #                 year_title_pairs[int(i.year)] = []
        #                 year_title_pairs[int(i.year)].append(i)
        #                 port_seq[int(i.year)] = []
        #                 port_seq[int(i.year)].append(i)
        #             else:
        #                 year_title_pairs[int(i.year)].append(i)
        #                 port_seq[int(i.year)] = []
        #                 port_seq[int(i.year)].append(i)
        # port=dict(sorted(port_seq.items(),reverse=True))
        # portfolio =port
        gaps = models.Gap.objects.filter(candidate_id=user, profile_id=activeprofile.id)
        gap_df=''
        if gaps:
            q = gaps.values('start_date', 'end_date')
            gap_df = pd.DataFrame.from_records(q)
            gap_df['start_date'] =  pd.to_datetime(gap_df.start_date, format='%B, %Y')
            now = datetime.datetime.now()
            now_date=now.strftime('%B')+', '+now.strftime('%Y')
            gap_df['end_date'] = gap_df['end_date'].apply(lambda x: now_date if x == "present" else x)
            gap_df['start_date'] =  pd.to_datetime(gap_df.start_date, format='%B, %Y')
            gap_df['type']='gap'
            gap_df['end_date'] =  pd.to_datetime(gap_df.end_date, format='%B, %Y')
            gap_df['s_year'] = pd.DatetimeIndex(gap_df['start_date']).year
            gap_df['e_year'] = pd.DatetimeIndex(gap_df['end_date']).year
            gap_df['s_month'] = pd.DatetimeIndex(gap_df['start_date']).month
            gap_df['e_month'] = pd.DatetimeIndex(gap_df['end_date']).month
            gap_df = gap_df.sort_values(by="start_date")
            gap_df = gap_df.rename(columns = {'start_date': 'start', 'end_date': 'end'}, inplace = False)
            print("gaaaaaaaaaps ", gaps)
            for i in gaps:
                print("enterrred for loop for jgaps")
                if i.end_date:
                    if int(i.end_date.split(',')[1]) not in list(year_title_pairs.keys()):
                        print("ifffffffffffffffffffffffffffffffffffffffffffffff")
                        year_title_pairs[int(i.end_date.split(',')[1])] = []
                        year_title_pairs[int(i.end_date.split(',')[1])].append(i)
                    else:
                        year_title_pairs[int(i.end_date.split(',')[1])].append(i)
        df = [exp_df, edu_df, gap_df]
        print(year_title_pairs)
        skills_show = models.CandidateSkillUserMap.objects.filter(candidate_id=user, profile_id=activeprofile.id)
    sorted_key_list = sorted(year_title_pairs)
    sorted_key_list.reverse()
    job_preference = models.CandidateJobPreference.objects.filter(candidate_id=user)
    skills_keywoard = models.CandidateSkillUserMap.objects.filter(candidate_id=user, profile_id=activeprofile.id)
    keywoard=[]
    for i in skills_show:
        keywoard.append(i.skill.name)
    preferredcity=profile_show.preferred_cities.split(',')
    preferredcity=list(filter(None,preferredcity))
    # preferredcity=list(filter('0',preferredcity))
    # preferredcity=list(filter(0,preferredcity))
    for i in preferredcity:
        city = models.City.objects.get(id=int(i))
        keywoard.append(city.city_name)
    keywoard = ",".join(keywoard)
    share_url=""
    if profile_show.url_name:
        share_url=profile_show.url_name
    about_me=''
    if profile_show.about_me:
        about_me=profile_show.about_me
        clean = re.compile('<.*?>')
        about_me=re.sub(clean, '', about_me)

    return render(request,'candidate/profile-third.html',
                  {'df':df,'company_data_status':company_data_status,
                   'about_me':about_me,'share_url':share_url,'keywoard':keywoard,'skills_show':skills_show,
                   'looking_job':looking_job,'hire':hire,'profile':profile_id_get,'hidefield':hidefield,
                   'profile_show':profile_show,'user':user,'experiences':experiences,'portfolios':portfolio,
                   'educations':educations,'certificates':certificates,'awards':awards,'sorted_keys':sorted_key_list,
                   'year_title_pairs':year_title_pairs,'start_years':start_years,'end_years':end_years,
                   'skills':skill_names,'year_salary_pair':json.dumps(year_salary_pair),'company_names':company_names,
                   'job_preference':job_preference,'exp_pie_chart_companies':json.dumps(exp_pie_chart_companies),
                   'exp_pie_chart_total_exp': json.dumps(exp_pie_chart_total_exp)})


def delete_exp_doc(request):
    # print(request.POST)
    record_id = request.POST.get('record_id')
    print(request.POST.get('record_id'))
    experience_id = request.POST.get('experience_id')
    print(request.POST.get('experience_id'))
    experience = models.CandidateExperience.objects.get(id=experience_id)
    print("========================>", experience)

    exp_document = models.CandidateExpDocuments.objects.get(candidate_exp_id=experience.id, record_id=record_id)
    exp_document.delete()
    return HttpResponse(True)


def candidate_resume_update(request):
    if request.method == 'POST':
        print('\n\n\n\n\n\n===============candidate_resume_update', request.FILES.get('resume-file'),
              request.session['active_profile_id'])
        user_id = models.User.objects.get(email=request.user.email)
        file = request.FILES.get('resume-file')
        profile = models.CandidateProfile.objects.get(candidate_id=user_id, profile_id=models.Profile.objects.get(
            id=request.session['active_profile_id']))
        profile.resume = file
        profile.save()
        return HttpResponse(True)


def referral_signup(request, referral):
    print('refer number====================', referral)
    print('referral_signup', User.objects.filter(referral_number=referral))
    if User.objects.filter(referral_number=referral).exists():
        alert = {}
        if not request.user.is_authenticated:
            if request.method == 'POST':
                fname = request.POST.get('fname')
                lname = request.POST.get('lname')
                email = request.POST.get('email')
                referred_by = request.POST.get('referral_code')
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
                context1 = {
                    "ip": ip,
                    "device_type": device_type,
                    "browser_type": browser_type,
                    "browser_version": browser_version,
                    "os_type": os_type,
                    "os_version": os_version
                }
                if User.objects.filter(email=request.POST['email']).exists():
                    alert['message'] = "email already exists"
                else:
                    usr = User.objects.create_candidate(email=email, first_name=fname, last_name=lname,
                                                        password=password, ip=ip, device_type=device_type,
                                                        browser_type=browser_type,
                                                        browser_version=browser_version, os_type=os_type,
                                                        os_version=os_version,
                                                        referral_number=generate_referral_code(),
                                                        referred_by=referred_by)
                    try:
                        mail_subject = 'Activate your account.'
                        current_site = get_current_site(request)
                        print('domain----===========', current_site.domain)
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
                        msg.send()
                        if models.User.objects.filter(referral_number=referred_by).exists():
                            referred_by_user = User.objects.get(referral_number=referred_by)
                            referred_to_user = User.objects.get(email__exact=email)
                            models.ReferralDetails.objects.create(referred_by=referred_by_user,
                                                                  referred_to=referred_to_user)
                    except BadHeaderError:
                        new_registered_usr = User.objects.get(email__exact=email).delete()
                        models.ReferralDetails.objects.get(referred_to=new_registered_usr).delete()
                        alert['message'] = "email not send"
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
        return render(request, 'candidate/candidate_signup.html', {'referral_number': referral})
    else:
        return render(request, 'accounts/404.html')


import shutil
from django.conf import settings
from wsgiref.util import FileWrapper


def download_folder(request, candidate_id):
    path = settings.MEDIA_ROOT + str(candidate_id)
    path_to_zip = shutil.make_archive(path, "zip", path)
    name = User.objects.get(id=candidate_id)
    response = HttpResponse(FileWrapper(open(path_to_zip, 'rb')), content_type='application/x-zip-compressed')
    response['Content-Disposition'] = 'attachment; filename=' + name.first_name + ' ' + name.last_name + '.zip'
    # response['Content-Length'] = zip_io.tell()
    return response


def test_redirect(request):
    print('\n\n\n\ntest_redirect >>>>>>>>>>>>>>>>>>>')
    return redirect('candidate:home')


from django.utils.crypto import get_random_string


def apply_job(request,id):
    context = {'notice_period': models.NoticePeriod.objects.all()}
    job = JobCreation.objects.get(id=id)
    context['job_obj']= job
    return render(request, 'candidate/ATS/apply-jobs-form.html', context)


def add_apply_candidate(request):
    alert = {}
    # get_random_string(length=32, allowed_chars='ACTG')
    if not request.user.is_authenticated:
        print('not is_authenticated ')
        if request.method == 'POST':
            fname = request.POST.get('f-name')
            lname = request.POST.get('l-name')
            email = request.POST.get('email')
            gender = request.POST.get('gender')
            resume = request.FILES['resume']
            contact = request.POST.get('contact-num')
            skill = request.POST.get('skill-type')
            designation = request.POST.get('designation-input')
            notice = request.POST.get('notice-input')
            current_work = request.POST.get('current-work-name')
            ctc = request.POST.get('ctc-input')
            expectedctc = request.POST.get('expected-ctc')
            total_exper = request.POST.get('professional-experience-year') + request.POST.get('professional-experience-month')
            password = get_random_string(length=12)
            # checkbox = request.POST.get('checkbox')
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
            context1 = {
                "ip": ip,
                "device_type": device_type,
                "browser_type": browser_type,
                "browser_version": browser_version,
                "os_type": os_type,
                "os_version": os_version
            }
            if User.objects.filter(email=request.POST['email']).exists():
                alert['message'] = "email already exists"
            else:
                print('created')
                usr = User.objects.apply_candidate(email=email, first_name=fname, last_name=lname,
                                                   password=password, ip=ip, device_type=device_type,
                                                   browser_type=browser_type,
                                                   browser_version=browser_version, os_type=os_type,
                                                   os_version=os_version,
                                                   referral_number=generate_referral_code())
                try:
                    mail_subject = 'Activate your account.'
                    current_site = get_current_site(request)
                    # print('domain----===========',current_site.domain)
                    html_content = render_to_string('accounts/send_credentials.html', {'user': usr,
                                                                                       'name': fname + ' ' + lname,
                                                                                       'email': email,
                                                                                       'domain': current_site.domain,
                                                                                       'password': password, })
                    to_email = usr.email
                    from_email = settings.EMAIL_HOST_USER
                    msg = EmailMultiAlternatives(mail_subject, mail_subject, from_email, to=[to_email])
                    msg.attach_alternative(html_content, "text/html")
                    msg.send()
                    apply_data = models.candidate_job_apply_detail.objects.create(
                        candidate_id=User.objects.get(email=email), gender=gender, resume=resume, contact=contact,
                        skill=skill, designation=designation, notice=notice, current_work=current_work, ctc=ctc,
                        expectedctc=expectedctc, total_exper=total_exper, )
                    apply_data.save()

                    applicant_create=AppliedCandidate.objects.create(candidate=User.objects.get(email=email),job_id=JobCreation.objects.get(id=int(request.POST.get('job_id'))))
                    applicant_create.save()

                    return redirect('accounts:signin')
                except BadHeaderError:
                    new_registered_usr = User.objects.get(email__exact=email).delete()
                    models.ReferralDetails.objects.get(referred_to=new_registered_usr).delete()
                    alert['message'] = "email not send"
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
    return render(request, 'candidate/ATS/apply-jobs-form.html',alert)

import pdfkit

def candidate_jcr(request, id, job_id):
    context = {}
    job_obj = JobCreation.objects.get(id=job_id)
    context['job_obj'] = job_obj
    jcr_obj_temp = JCR.objects.filter(template=Template_creation.objects.get(id=id)).order_by('id')
    jcr_categories = jcr_obj_temp.filter(pid=None).order_by('id')
    context['getStoreData'] = []
    for category in jcr_categories:
        add_details_item=[]
        sub_categories = jcr_obj_temp.filter(pid=category)
        for sub_category in sub_categories:
            sub_type =[]
            leaf_nodes = jcr_obj_temp.filter(pid=sub_category)
            for node in leaf_nodes:
                detail=[]
                det_data=jcr_obj_temp.filter(pid=node.id)
                for detail_data in det_data:
                    detail.append({
                                    'id':detail_data.id,
                                    'title':detail_data.name,
                                    'percent':detail_data.ratio
                                })
                sub_type.append({'question':node.name,
                                'id':node.id,
                                'q_percent':node.ratio,
                                'matching':node.flag,
                                'details':detail
                                })
            add_details_item.append({'cat_type':sub_category.name,
                                     'id':sub_category.id,
                                     'cate_percent': sub_category.ratio,
                                     'cat_subtype':sub_type})
        context['getStoreData'].append({'cat_name':category.name,'cat_value':category.ratio,'id':category.id,'addDetailsItem':add_details_item})
    if len(context['getStoreData'])==0:
        context['getStoreData'] = None
    if request.method=='POST':
        final=[]
        main_cat=[]
        jcr=[]
        for i in context['getStoreData']:
            cat_per=0
            cat_type=[]
            for j in i['addDetailsItem']:
                qui=0
                question=[]
                for k in j['cat_subtype']:
                    option = []
                    if k['matching'] == 'multi':
                        detail=0
                        for l in k['details']:
                            if l['title'] in request.POST.getlist(str(k['id'])):
                                models.JcrFill.objects.update_or_create(candidate_id= User.objects.get(id=request.user.id),
                                                              job_id=JobCreation.objects.get(id=job_id),template=Template_creation.objects.get(id=id),
                                                              company_id=User.objects.get(id=int(job_obj.company_id.id)),
                                                                        defaults={
                                                                            'jcr_id': JCR.objects.get(id=int(l['id'])),
                                                                        })
                                option.append({'detail': l['title'], 'detail_per': l['percent']})
                                detail+=int(l['percent'])

                    if k['matching'] == 'single':
                        detail=0

                        for l in k['details']:
                            if l['title'] == request.POST.get(str(k['id'])):
                                models.JcrFill.objects.update_or_create(candidate_id=User.objects.get(id=request.user.id),
                                                              job_id=JobCreation.objects.get(id=job_id),template=Template_creation.objects.get(id=id),
                                                              company_id=User.objects.get(id=job_obj.company_id.id),
                                                                        defaults={
                                                                            'jcr_id': JCR.objects.get(id=int(l['id'])),
                                                                        })
                                option.append({'detail':l['title'],'detail_per':l['percent']})
                                detail+=int(l['percent'])

                    question.append({'question': k['question'], 'q_per': k['q_percent'],
                                     'obt_per': detail * int(k['q_percent']) / 100,'option':option})
                    qui+=detail*int(k['q_percent'])/100
                cat_type.append({'catagory':j['cat_type'],'cat_per':j['cate_percent'],'obt_cat':qui*int(j['cate_percent'])/100,'question':question})
                cat_per+=qui*int(j['cate_percent'])/100
            final.append({i['cat_name']:cat_per*int(i['cat_value'])/100})
            main_cat.append(
                {'main_cat': i['cat_name'], 'main_per': i['cat_value'], 'main_obt': cat_per * int(i['cat_value']) / 100,
                 'category_detail': cat_type})
        models.JcrRatio.objects.update_or_create(candidate_id=User.objects.get(id=request.user.id),
                                                              job_id=JobCreation.objects.get(id=job_id),template=Template_creation.objects.get(id=id),
                                                              company_id=User.objects.get(id=job_obj.company_id.id),defaults={
                                                                            'Primary': final[0]['primary-list'],
                                                                            'Secondary':final[1]['secondary-list'],
                                                                            'Objective' : final[2]['objective-list'],
                                                                            'Total' : final[0]['primary-list'] + final[1]['secondary-list'] + final[2]['objective-list']
                                                                        })
        # print(main_cat)
        a = """<div style="background: #fff;">
            <div style="width: 100%;display: inline-block;padding: 8px 15px;border-bottom: 2px solid #eef4fa;">
                <div style="float: left;width: 50%;font-size: 16px;font-weight: 700;color: #031b4e;">Skill Compatibility</div>
                <div style="float: left;width: 50%;text-align: right;font-size: 14px;font-weight: 500;color: #51bc25;line-height: 24px;">Obtained : """+str(final[0]['primary-list'] + final[1]['secondary-list'] + final[2]['objective-list'])+"""%</div>
            </div>
            <div style="margin: 15px;border: 2px solid #eef4fa;">
                <div style="font-size: 16px;font-weight: bold; text-transform: uppercase;color: #031b4e;border-bottom: 2px solid #eef4fa;padding: 6px 13px;">JCR -  <span style="color: #51bc25;">"""+str(final[0]['primary-list'] + final[1]['secondary-list'] + final[2]['objective-list'])+"""%</span> / 100%</div>"""
        for i in main_cat:
            a += """<div style="width: 100%;display: inline-block;color: #031b4e;">
                        <div style="width: 12%;float: left;font-size: 14px;color: #031b4e;padding: 10px 13px;">
                           <div>"""+str(i['main_cat'])+""" :-</div>
                           <div>("""+str(i['main_obt'])+"""% / """+str(i['main_per'])+"""%)</div>
                       </div>
                       <div style="width: 85%;float: left;border-left: 2px solid #eef4fa;">"""
            for j in i['category_detail']:
                a += """<div style="display: inline-block;width: 100%;border-bottom: 2px solid #eef4fa;">
                                   <div style="width: 100%;">
                                       <div style="width: 17%;float: left;padding: 10px 13px;">
                                           <div>"""+str(j['catagory'])+""" :-</div>
                                           <div>("""+str(j['obt_cat'])+"""% / """+str(j['cat_per'])+"""%)</div>
                                       </div>
                                       <div style="float: left;width: 75%;border-left: 2px solid #eef4fa;">"""
                for k in j['question']:
                    a += """              <div style="padding: 10px 13px;border-bottom: 2px solid #eef4fa;">
                                                   <div>"""+str(k['question'])+""".</div>
                                                   <div>("""+str(k['obt_per'])+"""% / """+str(k['q_per'])+"""%)</div>"""
                    for l in k['option']:
                        a += """               <div style="padding-top: 5px;"><svg id="SvgjsSvg1006" width="16" height="16" xmlns="http://www.w3.org/2000/svg" version="1.1" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:svgjs="http://svgjs.com/svgjs"><defs id="SvgjsDefs1007"></defs><g id="SvgjsG1008" transform="matrix(1,0,0,1,0,0)"><svg xmlns="http://www.w3.org/2000/svg" aria-hidden="true" class="svg-inline--fa fa-dot-circle fa-w-16" data-icon="dot-circle" data-prefix="fas" viewBox="0 0 512 512" width="16" height="16"><path fill="#0068ff" d="M256 8C119.033 8 8 119.033 8 256s111.033 248 248 248 248-111.033 248-248S392.967 8 256 8zm80 248c0 44.112-35.888 80-80 80s-80-35.888-80-80 35.888-80 80-80 80 35.888 80 80z" class="colorcurrentColor svgShape"></path></svg></g></svg> <span style="padding-left: 3px;">"""+str(l['detail'])+""" ("""+str(l['detail_per'])+"""%)</span></div>"""
                    a += """               </div>"""
                a += """               </div>
                                   </div>
                               </div>"""
            a += """</div>

                    </div>"""
        a += """    </div>
        </div>"""

        pdfkit.from_string(a, output_path="new_file.pdf")

    return render(request, 'candidate/ATS/jcr_candidate.html', context)


def applied_job_list(request):
    print(request.user.id)
    applied_job = AppliedCandidate.objects.filter(candidate=User.objects.get(id=request.user.id))
    return render(request, 'candidate/ATS/candidate_applied_job.html', {'applied_job':applied_job})


def applied_job_detail(request,id):
    job_obj = JobCreation.objects.get(id=id)
    workflow = JobWorkflow.objects.get(job_id=job_obj)
    workflow_stages = WorkflowStages.objects.filter(workflow=workflow.workflow_id).order_by('sequence_number').order_by('id')
    return render(request, 'candidate/ATS/candidate_applied_job_detail_view.html',
                  {'workflow_stages':workflow_stages,'job_obj':job_obj})


def prequisites_view(request,id,job_id):
    context = {}
    pre_requisite = PreRequisites.objects.get(template=Template_creation.objects.get(id=id))
    # pre_requisite = PreRequisites.objects.get(id=2)
    job_obj = JobCreation.objects.get(id=job_id)
    context['pre_requisite'] = {"template-data":eval(pre_requisite.data)}
    context['pre_requisite'] = json.dumps(context['pre_requisite'])
    print(context['pre_requisite'])
    context["html_data"] = pre_requisite.html_data
    context['job_obj']=job_obj
    return render(request,'candidate/ATS/prequisites_view.html',context)