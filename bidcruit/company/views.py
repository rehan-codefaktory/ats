from django.contrib.auth.forms import PasswordResetForm
from bidcruit import settings
import re
import json
import base64
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta
import datetime
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from accounts.tokens import account_activation_token
from django.core.mail import EmailMessage, BadHeaderError, EmailMultiAlternatives
from django.contrib.auth.decorators import login_required
import pandas as pd
import candidate
from . import models
from candidate import models as CandidateModels
import pyotp
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.db.models.query_utils import Q as Query
from elasticsearch_dsl import Q
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from .documents import CandidateDocument
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
from accounts.models import LoginDetail
from chat.models import Messages

User = get_user_model()

# FOR ADVANCED SEARCH
from company.forms import CandidateForm

from accounts.views import activate_account_confirmation
from itertools import zip_longest
from django.core.signing import Signer, TimestampSigner
from django.core import serializers


@login_required(login_url="/")
def index(request):
    context = {}
    return render(request, 'company/index.html', context)


def all_countries(request):
    country_list = []
    countries = CandidateModels.Country.objects.all()
    for i in countries:
        country_dict = {'id': i.id, 'country_name': i.country_name}
        country_list.append(country_dict)
    return JsonResponse(country_list, safe=False)


def all_states(request, country_id):
    country = CandidateModels.Country.objects.get(id=int(country_id))
    data_dict = {'id': country.id, 'country_name': country.country_name}
    states = CandidateModels.State.objects.filter(country_code=int(country_id))
    state_list = []
    for i in states:
        state_dict = {'id': i.id, 'name': i.state_name}
        state_list.append(state_dict)
    data_dict['states'] = state_list
    return JsonResponse([data_dict], safe=False)


def all_cities(request, state_id):
    state = CandidateModels.State.objects.get(id=int(state_id))
    data_dict = {'id': state.id, 'state_name': state.state_name}
    cities = CandidateModels.City.objects.filter(state_code=int(state_id))
    city_list = []
    for i in cities:
        city_dict = {'id': i.id, 'name': i.city_name}
        city_list.append(city_dict)
    data_dict['cities'] = city_list
    return JsonResponse([data_dict], safe=False)


def ragister(request):
    alert = {}
    if not request.user.is_authenticated:
        if request.method == 'POST':
            companyname = request.POST.get('company_name')
            website = request.POST.get('website')
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
                usr = User.objects.create_company(email=email, company_name=companyname, website=website,
                                                  password=password, ip=ip, device_type=device_type,
                                                  browser_type=browser_type,
                                                  browser_version=browser_version, os_type=os_type,
                                                  os_version=os_version)
                try:
                    mail_subject = 'Activate your account.'
                    current_site = get_current_site(request)
                    html_content = render_to_string('accounts/acc_active_email.html', {'user': usr,
                                                                                       'name': companyname,
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
                except BadHeaderError:
                    ins = User.objects.get(email__exact=email).delete()
                    alert['message'] = "email not send"
                return activate_account_confirmation(request, companyname, email)
    else:
        if request.user.is_authenticated:
            if request.user.is_candidate:
                return redirect('candidate:home')
            if request.user.is_company:
                profile = models.CompanyProfile.objects.filter(company_id=request.user.id)
                if profile:
                    return redirect('company:company_profile')
                else:
                    return redirect('company:add_edit_profile')
    return render(request, 'company/companyregister.html', alert)


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'company/company_login_email.html')
    else:
        return HttpResponse('Activation link is invalid!')


def generateOTP(request):
    totp = None
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret, interval=300)
    one_time = totp.now()
    request.session['otp'] = one_time
    return one_time


def user_login_password(request):
    if request.method == 'POST':
        email = request.session['email']
        password = request.POST.get('password')
        user = authenticate(email=email, password=password)
        user_id = User.objects.get(email=email)
        request.session['user_id'] = user_id.id
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
        if user:
            if user.is_active:
                otp = generateOTP(request)
                LoginDetail.objects.create(user_id=User.objects.get(email=email), otp=otp, ip=ip,
                                           device_type=device_type, browser_type=browser_type,
                                           browser_version=browser_version, os_type=os_type,
                                           os_version=os_version)
                try:
                    mail_subject = 'OTP.'
                    html_content = render_to_string('accounts/acc_otp_email.html', {'user': user,
                                                                                    'otp': otp})
                    to_email = email
                    from_email = settings.EMAIL_HOST_USER
                    msg = EmailMultiAlternatives(mail_subject, mail_subject, from_email, to=[to_email])
                    msg.attach_alternative(html_content, "text/html")
                    msg.send()
                except BadHeaderError:
                    print("email not send")
                return redirect('company:verify_otp')
            else:
                return HttpResponse("Your account was inactive.")
        else:
            print("Someone tried to login and failed.")
            return HttpResponse("Invalid login details given")
    else:
        return render(request, 'company/company_login.html')


def user_login_email(request):
    if request.method == 'POST':
        email = request.POST.get('emailaddress')
        request.session['email'] = email
        return redirect('company:user_login_password')
    return render(request, 'company/company_login_email.html')


def resend_otp(request):
    user = User.objects.get(id=request.session['user_id'])
    otp = generateOTP(request)
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
    LoginDetail.objects.create(company_id=User.objects.get(id=request.session['user_id']), otp=otp, ip=ip,
                               device_type=device_type, browser_type=browser_type,
                               browser_version=browser_version, os_type=os_type,
                               os_version=os_version)
    try:
        mail_subject = 'OTP.'
        html_content = render_to_string('accounts/acc_otp_email.html', {'user': user,
                                                                        'otp': otp})
        to_email = user.email
        from_email = settings.EMAIL_HOST_USER
        msg = EmailMultiAlternatives(mail_subject, mail_subject, from_email, to=[to_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except BadHeaderError:
        print("email not send")
    return render(request, 'company/company_otp_verify.html')


def verify_otp(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        login_otp = LoginDetail.objects.filter(company_id=request.session['user_id']).order_by(
            '-create_at').first()
        if login_otp.otp == otp:
            user = User.objects.get(id=login_otp.company_id.id)
            login(request, user)
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            chk_register_detail = models.User.objects.get(email=request.user.email)
            if ip != chk_register_detail.ip:
                mail_subject = 'Change Ip Notification'
                html_content = render_to_string('accounts/login_change_ip_email.html', {'user': user, })
                to_email = request.user.email
                from_email = settings.EMAIL_HOST_USER
                msg = EmailMultiAlternatives(mail_subject, mail_subject, from_email, to=[to_email])
                msg.attach_alternative(html_content, "text/html")
                msg.send()
            return redirect('company:home')
        else:
            return HttpResponse(False)
    return render(request, 'company/company_otp_verify.html')


@login_required(login_url="/")
def user_logout(request):
    logout(request)
    return redirect('company:user_login_email')


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


def candidate_hire(request):
    if request.method == 'POST':
        print('hire_message', request.POST.get('hire_message'))
        candidate_id = User.objects.get(id=request.POST.get('candidate_id'))
        company_id = User.objects.get(id=request.user.id)
        active_profile = CandidateModels.Profile.objects.get(candidate_id=candidate_id, active=True)
        profile_id = CandidateModels.CandidateProfile.objects.get(candidate_id=candidate_id,
                                                                  profile_id=active_profile.id)

        models.CandidateHire.objects.create(title='None',
                                            message=request.POST.get('hire_message'),
                                            candidate_id=candidate_id, company_id=company_id, profile_id=active_profile)
        Messages.objects.create(description=request.POST.get('hire_message'), sender_name=company_id,
                                receiver_name=candidate_id)
        try:
            mail_subject = 'Company wants to Hire You.'
            html_content = render_to_string('accounts/candidate_hire_email.html',
                                            {'message': request.POST.get('hire_message')})
            to_email = candidate_id.email
            from_email = settings.EMAIL_HOST_USER
            msg = EmailMultiAlternatives(mail_subject, mail_subject, from_email, to=[to_email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            return HttpResponse(True)
        except BadHeaderError:
            print("email not send")
            return HttpResponse(False)
    else:
        return HttpResponse('Invalid Request')

    # return render(request, 'company/candidate_hire.html',{'candidate_id':pk})


def company_login_direct(request):
    if request.method == 'POST':
        print('\n\ncalled company_login_email', request.POST.get('company_login_email'))
        print('\n\ncalled company_login_password', request.POST.get('company_login_password'))
    return HttpResponse(True)


def candidate_list_view(request):
    candidate_list = CandidateModels.CandidateProfile.objects.all().order_by('id')
    page = request.GET.get('page', 1)
    paginator = Paginator(candidate_list, 1)
    try:
        candidates = paginator.page(page)
    except PageNotAnInteger:
        candidates = paginator.page(1)
    except EmptyPage:
        candidates = paginator.page(paginator.num_pages)
    return render(request, 'company/candidate_list_view.html', {'candidates': candidates})


def user_login_email_popup(request):
    data = json.loads(request.body.decode('UTF-8'))
    email = data['email']
    regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'
    if (re.search(regex, email)):
        user_obj = models.User.objects.filter(email=email, is_company=True).exists()
        if user_obj:
            print('\n\nuser_login_email_popup', data)
            request.session['company_email'] = data['email']
            request.session['login_type'] = data['type_name']
            return HttpResponse(True)
        else:
            return HttpResponse(False)
    else:
        return HttpResponse(False)


def user_login_password_popup(request):
    data = json.loads(request.body.decode('UTF-8'))
    print('\n\nuser_login_password_popup', data)
    if request.method == 'POST':
        email = request.session['company_email']
        password = data['password']
        print("==================", email, password)
        user = authenticate(email=email, password=password)
        user_id = User.objects.get(email=email)
        request.session['user_id'] = user_id.id
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
        if user:
            if user.is_active:
                otp = generateOTP(request)
                LoginDetail.objects.create(user_id=User.objects.get(email=email), otp=otp, ip=ip,
                                           device_type=device_type, browser_type=browser_type,
                                           browser_version=browser_version, os_type=os_type,
                                           os_version=os_version)
                try:
                    mail_subject = 'OTP.'
                    html_content = render_to_string('accounts/acc_otp_email.html', {'user': user,
                                                                                    'otp': otp})
                    to_email = email
                    from_email = settings.EMAIL_HOST_USER
                    msg = EmailMultiAlternatives(mail_subject, mail_subject, from_email, to=[to_email])
                    msg.attach_alternative(html_content, "text/html")
                    msg.send()
                except BadHeaderError:
                    print("email not send")
                return HttpResponse(True)
            else:
                return HttpResponse("Your account is inactive.")
        else:
            print("Someone tried to login and failed.")
            return HttpResponse("Invalid login details given")
    else:
        return HttpResponse(False)


def user_login_verify_otp_popup(request):
    data = json.loads(request.body.decode('UTF-8'))
    if request.method == 'POST':
        otp = data['otp']
        login_otp = LoginDetail.objects.filter(user_id=request.session['user_id']).order_by(
            '-create_at').first()
        if login_otp.otp == otp:
            user = User.objects.get(id=login_otp.user_id.id)
            login(request, user)
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            chk_register_detail = models.User.objects.get(email=request.user.email)
            print('----------=======', request.session['login_type'])
            if ip != chk_register_detail.ip:
                mail_subject = 'Change Ip Notification'
                html_content = render_to_string('accounts/login_change_ip_email.html', {'user': user, })
                to_email = request.user.email
                from_email = settings.EMAIL_HOST_USER
                msg = EmailMultiAlternatives(mail_subject, mail_subject, from_email, to=[to_email])
                msg.attach_alternative(html_content, "text/html")
                msg.send()
            return HttpResponse(request.session['login_type'])
        else:
            return HttpResponse(False)
    else:
        return HttpResponse(False)


def candidate_preference_check(request):
    if request.user.is_company:
        if request.method == 'POST':
            company_id = User.objects.get(id=request.user.id)
            exclude_list = ['candidate_id', 'relocation_cities', 'id']
            print('-----------', request.POST.get('candidate_id'))
            candidate_id = User.objects.get(id=int(request.POST.get('candidate_id')))
            for i in CandidateModels.CandidateJobPreference._meta.get_fields():
                if i.name not in exclude_list:
                    print('\n\n', i.name)
                    print('', type(i.name))
                    if request.POST.get(i.name) == 'on':
                        models.CandidateSelectedPreference.objects.update_or_create(company_id=company_id,
                                                                                    candidate_id=candidate_id,
                                                                                    preference_name=i.name, defaults={
                                'is_selected': True, 'company_id': company_id, 'candidate_id': candidate_id,
                                'preference_name': i.name})
                    else:
                        models.CandidateSelectedPreference.objects.update_or_create(company_id=company_id,
                                                                                    candidate_id=candidate_id,
                                                                                    preference_name=i.name, defaults={
                                'is_selected': False, 'company_id': company_id, 'candidate_id': candidate_id,
                                'preference_name': i.name})
            # for i in CandidateModels.CandidateJobPreferenceOther.objects.filter(candidate_id=candidate_id):
            #     print('i',i)
            #     print('i',i.label)

            return HttpResponse(True)
    else:
        return HttpResponse(False)


def search(request):
    search_string = request.GET.get('candidate_search')
    search_city = request.GET.get('candidate_search_city')
    print(search_city)
    advanced_search_form = CandidateForm()
    users = []
    custom_queries = []
    print("search string", search_string)
    print("search city", search_city)

    if search_string:
        q = Q("multi_match", query=search_string, fields=['skills', 'job_titles'])
        print("search string appended")
        custom_queries.append(q)

    if search_city:
        city_name = CandidateModels.City.objects.get(id=int(search_city)).city_name
        q = Q("multi_match", query=city_name, fields=['current_city'])
        print("search city appended")
        custom_queries.append(q)
    if custom_queries:
        final_query = custom_queries[0]
        if len(custom_queries) >= 1:
            for i in range(1, len(custom_queries)):
                final_query = final_query & custom_queries[i]

        s = CandidateDocument.search().query(final_query).extra(size=10000)
        for hit in s:
            try:
                user = User.objects.get(email=hit.email)
                # for i in range(100):
                users.append(user.id)
            except:
                print("error")
    print(custom_queries)
    print(users)
    users = list(set(users))
    # if request.GET.get['getpage']==None:
    item = 10
    paginator = Paginator(users, item)
    # else:
    #     item=request.session['getpage']
    #     paginator = Paginator(users, int(item))
    page_number = request.GET.get("page", 1)
    try:
        candidate = paginator.page(page_number)

    except PageNotAnInteger:
        # If page parameter is not an integer, show first page.
        candidate = paginator.page(1)
    except EmptyPage:
        # If page parameter is out of range, show last existing page.
        candidate = paginator.page(paginator.num_pages)

    return render(request, 'company/search.html',
                  {'users': candidate, 'item': item, 'form': advanced_search_form, 'search_string': search_string,
                   'search_string_city': search_city})


def get_page_no(request):
    if request.method == 'POST':
        getpage = request.POST.get('item')
        request.session['getpage'] = getpage
        if request.session.get('data_set'):
            return redirect('company:advanced_search')
        return redirect('company:search_result')
    advanced_search_form = CandidateForm()
    return render(request, "company/candidatelistview.html", {'form': advanced_search_form})


def search_result(request):
    users = []
    try:
        search_string = request.session.get('search')
        print("search string is ------->", search_string)
        search_string_city = request.session.get('search_city')
        print("search string is ------->", search_string_city)
        print("search sting", search_string)
    except:
        pass
    if search_string != None or search_string_city != None:

        custom_queries = []
        if search_string != None:
            q = Q("multi_match", query=search_string, fields=['skills', 'job_titles'])
            print("search string appended")
            custom_queries.append(q)

        if search_string_city != None:
            city_name = CandidateModels.City.objects.get(id=int(search_string_city)).city_name
            q = Q("multi_match", query=city_name, fields=['current_city'])
            print("search city appended")
            custom_queries.append(q)

        final_query = custom_queries[0]
        if len(custom_queries) >= 1:
            for i in range(1, len(custom_queries)):
                final_query = final_query & custom_queries[i]

        page = request.GET.get('page', '1')
        s = CandidateDocument.search().query(final_query).extra(size=10000)
        for hit in s:
            try:
                user = User.objects.get(email=hit.email)
                users.append(user.id)
            except:
                pass
    users = list(set(users))
    if request.session['getpage'] == None:
        item = 20
        paginator = Paginator(users, item)
    else:
        item = request.session['getpage']
        paginator = Paginator(users, int(item))
    page_number = request.GET.get("page", 1)
    try:
        candidate = paginator.page(page_number)

    except PageNotAnInteger:
        # If page parameter is not an integer, show first page.
        candidate = paginator.page(1)
    except EmptyPage:
        # If page parameter is out of range, show last existing page.
        candidate = paginator.page(paginator.num_pages)
    if request.is_ajax():
        html = render_to_string('company/candidatelistview.html', {"users": candidate, 'search_string': search_string,
                                                                   'search_string_city': search_string_city})
        return HttpResponse(html)
    print('candidatecandidatecandidate---------', candidate)
    advanced_search_form = CandidateForm()
    return render(request, 'company/candidatelistview.html',
                  {"users": candidate, 'item': item, 'form': advanced_search_form, 'search_string': search_string,
                   'search_string_city': search_string_city})


def get_cities(request):
    # cities = City.objects.all()
    print("GET CITIES WAS CALLLLED")
    term = request.GET.get('term')
    cities = CandidateModels.City.objects.filter(city_name__istartswith=term)
    city_list = []
    for i in cities:
        data = {}
        data['id'] = i.id
        data['city_name'] = i.city_name
        data['state_name'] = i.state_code.state_name
        city_list.append(data)

    # print("citiesss",cities)
    return JsonResponse(city_list, safe=False)


def get_skills(request):
    print("\n\nget_skills WAS CALLLLED")
    term = request.GET.get('term')
    skills = CandidateModels.Skill.objects.filter(name__istartswith=term)
    skill_list = []
    for i in skills:
        data = {}
        data['id'] = i.id
        data['name'] = i.name
        skill_list.append(data)
    return JsonResponse(skill_list, safe=False)


def get_degrees(request):
    print("GET DEGREES WAS CALLLLLLLED")
    term = request.GET.get('term')
    degrees = CandidateModels.Degree.objects.filter(name__icontains=term)
    print("degreees", degrees)
    return JsonResponse(list(degrees.values()), safe=False)


def advanced_search(request):
    # if len(request.POST) ==0 :
    #     return redirect('company:search_result')
    print("advanced seaaaaaaaaaaaaaaaaaaaaaaaaarch")
    method = None
    custom_queries = []
    print("POST DATA", request.POST)
    count = -1
    form = CandidateForm(request.GET)
    users = []
    advanced_search_form = CandidateForm(request.GET)

    # user_ids=[]

    notice_period = request.GET.get('notice_period')
    print("GEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEET", request.GET)

    # print("advanaceeeeeeeeeeeeeeeed",advanced_search_form['current_city'])

    include_skills = request.GET.getlist('include_skills')
    exclude_skills = request.GET.getlist('exclude_skills')
    preferred_cities_id = request.GET.getlist('preferred_cities')
    current_city_id = request.GET.get('current_city')
    minimum_experience = request.GET.get('minimum_experience')
    maximum_experience = request.GET.get('maximum_experience')
    education_ids = request.GET.getlist('education')
    if request.GET.get('notice_period'):
        notice_period = CandidateModels.NoticePeriod.objects.get(id=request.GET.get('notice_period'))
    else:
        notice_period = CandidateModels.NoticePeriod.objects.get(id=1)
    current_city = ''
    if current_city_id:
        current_city = CandidateModels.City.objects.get(id=current_city_id).city_name

    if current_city:
        q = Q('multi_match', query=current_city, fields=['current_city'])
        custom_queries.append(q)
        # request.session['current_city'] = current_city

    # city = CandidateModels.City.objects.get(id=current_city_id)

    preferred_cities = []
    for i in preferred_cities_id:
        preferred_cities.append(CandidateModels.City.objects.get(id=i).city_name)

    if len(preferred_cities):
        # preferred_cities_string = ','.join(preferred_cities)
        # request.session['preferred_cities'] = preferred_cities_string
        for i in preferred_cities:
            q = Q('multi_match', query=i, fields=['preferred_cities'])
            custom_queries.append(q)

    if len(include_skills):
        # include_skills_string= ','.join(include_skills)
        # request.session['include_skills'] = include_skills_string
        for i in include_skills:
            q = Q('multi_match', query=i, fields=['skills'])
            custom_queries.append(q)
    if len(exclude_skills):
        # exclude_skills_string= ','.join(exclude_skills)
        # request.session['exclude_skills'] = exclude_skills_string
        for i in exclude_skills:
            q = ~Q('multi_match', query=i, fields=['skills'])
            custom_queries.append(q)

    if minimum_experience == '':
        minimum_experience = 0
    else:
        minimum_experience = int(minimum_experience)

    if maximum_experience == '':
        maximum_experience = 99
    else:
        maximum_experience = int(maximum_experience)

    degrees = []

    for i in education_ids:
        try:
            i = int(i)
            print("INTEGER I ", i)
            degree = CandidateModels.Degree.objects.get(id=i).name
            degrees.append(degree)
        except:
            pass

    if len(degrees):
        # degrees_string = ','.join(degrees)
        # request.session['degrees'] = degrees_string
        for i in degrees:
            q = Q('multi_match', query=i, fields=['education_list'])
            custom_queries.append(q)

    length = len(custom_queries)
    final_query = ''
    print("custom_queries", custom_queries)
    if length:
        final_query = custom_queries[0]
        if length > 1:
            for i in range(1, length):
                final_query = final_query & custom_queries[i]

    print("final_query: ", final_query)

    if final_query == "":
        search_string = request.GET.get('candidate_search')
        search_city = request.GET.get('candidate_search_city')
        if search_string:
            q = Q("multi_match", query=search_string, fields=['skills', 'job_titles'])
            print("search string appended")
            custom_queries.append(q)

        if custom_queries:
            final_query = custom_queries[0]
            if len(custom_queries) >= 1:
                for i in range(1, len(custom_queries)):
                    final_query = final_query & custom_queries[i]

            s = CandidateDocument.search().query(final_query).extra(size=10000)
            for hit in s:
                try:

                    user = User.objects.get(email=hit.email)
                    profile = CandidateModels.Profile.objects.get(candidate_id=user, active=True)
                    candidate_profile = CandidateModels.CandidateProfile.objects.get(candidate_id=user,
                                                                                     profile_id=profile)
                    if candidate_profile.notice_period == notice_period:
                        users.append(user.id)
                except:
                    print("error")
        else:
            profile = CandidateModels.Profile.objects.filter(active=True)
            for i in profile:
                print("the profile id is", i.id)
                candidate_profile = CandidateModels.CandidateProfile.objects.get(profile_id=i)
                if candidate_profile.notice_period == notice_period:
                    users.append(candidate_profile.candidate_id.id)


    else:
        s = CandidateDocument.search().query(final_query).extra(size=10000)
        print("candidate documebnt", s)
        count = 0
        for hit in s:
            print("HIT USER!!!!!")
            # try:
            user = User.objects.get(email=hit.email)
            print("emaiiiiiiil", user.email)
            # users.append(user)
            print(user.id)
            # count +=1
            # profiles = CandidateModels.Profile.objects.filter(candidate_id=user)
            profiles = CandidateModels.Profile.objects.filter(candidate_id=user, active=True)
            print("asdasdasdasdasdasdasdasdsd========================>", profiles)
            for i in profiles:
                print("prooooooooooooooofile", i)
            if profiles:
                profile = CandidateModels.Profile.objects.get(candidate_id=user, active=True)
                candidate_profile = CandidateModels.CandidateProfile.objects.get(candidate_id=user, profile_id=profile)
                print("found active profileeeeee")

                print(type(candidate_profile.total_experience))
                print(type(minimum_experience))
                print(maximum_experience)
                # candidate_profile = CandidateModels.CandidateProfile.objects.get(candidate_id=user)
                if (candidate_profile.total_experience >= minimum_experience) and (
                        candidate_profile.total_experience <= maximum_experience):

                    # users.append(user.id)

                    if candidate_profile.notice_period == notice_period:
                        users.append(user.id)
                        # user_ids.append(user.id)

                    count += 1
            # except:
            #         print("exception occured")

    item = 10
    paginator = Paginator(users, item)
    # else:
    #     item=request.session['getpage']
    #     paginator = Paginator(users, int(item))
    page_number = request.GET.get("page", 1)
    try:
        candidate = paginator.page(page_number)

    except PageNotAnInteger:
        # If page parameter is not an integer, show first page.
        candidate = paginator.page(1)
    except EmptyPage:
        # If page parameter is out of range, show last existing page.
        candidate = paginator.page(paginator.num_pages)

    # return render(request,"company/candidatelistview.html")

    if minimum_experience == 0:
        minimum_experience = ''
    if maximum_experience == 99:
        maximum_experience = ""
    print("-=-=-=-=-==--=-=-=-=-=-=-=-=-=-=-=-=-=-=-=", minimum_experience)

    education_choices = []
    print("-=-=-=-=-==--=-=-=-=-=-=-=-=-=-=-=-=-=-=-=", education_ids)
    for i in education_ids:
        education = CandidateModels.Degree.objects.get(id=i)
        education_choices.append((i, education.name))
    print(education_choices)
    # city = CandidateModels.City.objects.get(id=current_city_id)
    if current_city:
        city = CandidateModels.City.objects.get(id=current_city_id)
        current_city_choice = [(city.id, city.city_name)]
    else:
        current_city_choice = None

    preferred_cities = []
    if preferred_cities_id:
        for i in preferred_cities_id:
            city = CandidateModels.City.objects.get(id=i)
            preferred_cities.append((i, city.city_name))

    notice_period = (notice_period.id, notice_period.notice_period)
    advanced_search_form = CandidateForm(current_city=current_city_choice, minimum_experience=minimum_experience,
                                         maximum_experience=maximum_experience, education_choices=education_choices,
                                         preferred_cities=preferred_cities, include_skills=include_skills,
                                         exclude_skills=exclude_skills, notice_period=notice_period)
    return render(request, 'company/search.html', {"users": candidate, 'item': item, 'form': advanced_search_form})


def add_edit_profile(request):
    context = {}
    print(request.user)
    if request.user.is_company:
        context['country'] = CandidateModels.Country.objects.all()
        context['founded_years'] = [str(i) for i in range(1950, datetime.datetime.now().year + 1)]
        context['industrytype'] = CandidateModels.IndustryType.objects.all()
        context['employee_count_'] = models.CompanyProfile.employee_count_choices
        context['company_type_'] = models.CompanyProfile.company_type_choices
        profile_already_exists = models.CompanyProfile.objects.filter(
            company_id=User.objects.get(id=request.user.id)).exists()
        context['profile_already_exists'] = profile_already_exists
        if profile_already_exists:
            company_profile_obj = models.CompanyProfile.objects.get(company_id=User.objects.get(id=request.user.id))
            context['company_profile'] = company_profile_obj
            context['states'] = CandidateModels.State.objects.filter(country_code=company_profile_obj.country.id)
            context['cities'] = CandidateModels.City.objects.filter(state_code=company_profile_obj.state.id)
        if request.method == 'POST':
            models.CompanyProfile.objects.update_or_create(company_id=User.objects.get(id=request.user.id),
                                                           defaults={
                                                               'universal_Name': request.POST.get('universal_name'),
                                                               'compnay_type': request.POST.get('company_type'),
                                                               'industry_type': CandidateModels.IndustryType.objects.get(
                                                                   id=request.POST.get('industrial_type')),
                                                               'company_logo': request.FILES.get('logo'),
                                                               'speciality': request.POST.get('speciality'),
                                                               'address': request.POST.get('address'),
                                                               'country': CandidateModels.Country.objects.get(
                                                                   id=request.POST.get('country')),
                                                               'state': CandidateModels.State.objects.get(
                                                                   id=request.POST.get('state')),
                                                               'city': CandidateModels.City.objects.get(
                                                                   id=request.POST.get('city')),
                                                               'zip_code': request.POST.get('zipcode'),
                                                               'contact_no1': request.POST.get('contactno1'),
                                                               'contact_no2': request.POST.get('contactno2'),
                                                               'founded_year': request.POST.get('foundedyear'),
                                                               'employee_count': request.POST.get('employeecount')
                                                           })
            return redirect('company:company_profile')
    else:
        return redirect('accounts:user_logout')
    return render(request, 'company/add_profile.html', context)
def add_edit_profile(request):
    context = {}
    print(request.user)
    if request.user.is_company:
        context['country'] = CandidateModels.Country.objects.all()
        context['founded_years'] = [str(i) for i in range(1950, datetime.datetime.now().year + 1)]
        context['industrytype'] = CandidateModels.IndustryType.objects.all()
        context['employee_count_'] = models.CompanyProfile.employee_count_choices
        context['company_type_'] = models.CompanyProfile.company_type_choices
        profile_already_exists = models.CompanyProfile.objects.filter(
            company_id=User.objects.get(id=request.user.id)).exists()
        context['profile_already_exists'] = profile_already_exists
        if profile_already_exists:
            company_profile_obj = models.CompanyProfile.objects.get(company_id=User.objects.get(id=request.user.id))
            context['company_profile'] = company_profile_obj
            context['states'] = CandidateModels.State.objects.filter(country_code=company_profile_obj.country.id)
            context['cities'] = CandidateModels.City.objects.filter(state_code=company_profile_obj.state.id)
        if request.method == 'POST':
            models.CompanyProfile.objects.update_or_create(company_id=User.objects.get(id=request.user.id),
                                                           defaults={
                                                               'universal_Name': request.POST.get('universal_name'),
                                                               'compnay_type': request.POST.get('company_type'),
                                                               'industry_type': CandidateModels.IndustryType.objects.get(
                                                                   id=request.POST.get('industrial_type')),
                                                               'company_logo': request.FILES.get('logo'),
                                                               'speciality': request.POST.get('speciality'),
                                                               'address': request.POST.get('address'),
                                                               'country': CandidateModels.Country.objects.get(
                                                                   id=request.POST.get('country')),
                                                               'state': CandidateModels.State.objects.get(
                                                                   id=request.POST.get('state')),
                                                               'city': CandidateModels.City.objects.get(
                                                                   id=request.POST.get('city')),
                                                               'zip_code': request.POST.get('zipcode'),
                                                               'contact_no1': request.POST.get('contactno1'),
                                                               'contact_no2': request.POST.get('contactno2'),
                                                               'founded_year': request.POST.get('foundedyear'),
                                                               'employee_count': request.POST.get('employeecount')
                                                           })
            return redirect('company:company_profile')
    else:
        return redirect('accounts:user_logout')
    return render(request, 'company/add_profile.html', context)


from django.db.models import Count, Sum


def hire_request(request):
    active = models.CandidateHire.objects.filter(company_id=request.user.id, request_status=1).values('message',
                                                                                                      'company_id',
                                                                                                      'candidate_id',
                                                                                                      'profile_id').annotate(
        cnt=Count('profile_id'))
    new_request = models.CandidateHire.objects.filter(company_id=request.user.id, request_status=0).values('message',
                                                                                                           'company_id',
                                                                                                           'candidate_id',
                                                                                                           'profile_id').annotate(
        cnt=Count('profile_id'))
    archive = models.CandidateHire.objects.filter(company_id=request.user.id, request_status=-1).values('message',
                                                                                                        'company_id',
                                                                                                        'candidate_id',
                                                                                                        'profile_id').annotate(
        cnt=Count('profile_id'))
    shortlisted_candidates = models.ShortlistedCandidates.objects.filter(company_id=request.user.id)
    print("^^^^^^^^^^^^++++++++++++++++++++", shortlisted_candidates)
    data_active = CandidateModels.company_data_request.objects.filter(company_id=request.user.id, status=1).values('id',
                                                                                                                   'message',
                                                                                                                   'company_id',
                                                                                                                   'candidate_id',
                                                                                                                   'profile_id')
    data_new_request = CandidateModels.company_data_request.objects.filter(company_id=request.user.id,
                                                                           status=-1).values('id', 'message',
                                                                                             'company_id',
                                                                                             'candidate_id',
                                                                                             'profile_id')
    data_archive = CandidateModels.company_data_request.objects.filter(company_id=request.user.id, status=-2).values(
        'id', 'message', 'company_id', 'candidate_id', 'profile_id')
    return render(request, 'company/request.html', {'active': active, 'new_request': new_request, 'archive': archive,
                                                    'shortlisted_candidates': shortlisted_candidates,
                                                    'data_active': data_active,
                                                    'data_new_request': data_new_request, 'data_archive': data_archive})


def accept_request(request, profile_id, company_id):
    if request.method == "POST":
        MessageModel.objects.create(user=User.objects.get(id=request.user.id),
                                    recipient=User.objects.get(id=candidate_id),
                                    body=request.POST.get('accept_message'), request_status=1)
        models.CandidateHire.objects.filter(company_id=request.user.id, candidate_id=candidate_id,
                                            profile_id=profile_id).update(request_status=1,
                                                                          message=request.POST.get('accept_message'))
    return redirect('company:hire_request')


def reject_request(request, profile_id, company_id):
    if request.method == "POST":
        MessageModel.objects.create(user=User.objects.get(id=request.user.id),
                                    recipient=User.objects.get(id=candidate_id),
                                    body=request.POST.get('reject_message'), request_status=-1)
        modelsCandidateHire.objects.filter(comapny_id=request.user.id, candidate_id=candidate_id_id,
                                           profile_id=profile_id).update(request_status=-1,
                                                                         message=request.POST.get('reject_message'))
    return redirect('company:hire_request')


def file_request(request):
    if request.is_ajax():
        company = User.objects.get(id=request.user.id)

        profile = CandidateModels.Profile.objects.get(id=request.GET.get('profile'), candidate_id_id=User.objects.get(
            id=int(request.GET.get('candidate'))))

        candidate = User.objects.get(id=int(request.GET.get('candidate')))
        print(candidate)
        if request.GET.get('s_type') == "Experience":
            CandidateModels.company_Hide_Fields_request.objects.update_or_create(company_id_id=company.id,
                                                                                 profile_id_id=profile.id,
                                                                                 candidate_id_id=candidate.id,
                                                                                 defaults={
                                                                                     'exp_document': -1,
                                                                                 })
        elif request.GET.get('s_type') == "Education":
            CandidateModels.company_Hide_Fields_request.objects.update_or_create(company_id_id=company.id,
                                                                                 profile_id_id=profile.id,
                                                                                 candidate_id_id=candidate.id,
                                                                                 defaults={
                                                                                     'edu_document': -1,
                                                                                 })
        elif request.GET.get('s_type') == "Portfolio":
            CandidateModels.company_Hide_Fields_request.objects.update_or_create(company_id_id=company.id,
                                                                                 profile_id_id=profile.id,
                                                                                 candidate_id_id=candidate.id,
                                                                                 defaults={
                                                                                     'portfolio_document': -1,
                                                                                 })
        elif request.GET.get('s_type') == "Certificarte":
            CandidateModels.company_Hide_Fields_request.objects.update_or_create(company_id_id=company.id,
                                                                                 profile_id_id=profile.id,
                                                                                 candidate_id_id=candidate.id,
                                                                                 defaults={
                                                                                     'certificate_document': -1,
                                                                                 })
        elif request.GET.get('s_type') == "email":
            CandidateModels.company_Hide_Fields_request.objects.update_or_create(company_id_id=company.id,
                                                                                 profile_id_id=profile.id,
                                                                                 candidate_id_id=candidate.id,
                                                                                 defaults={
                                                                                     'email': -1,
                                                                                 })
        elif request.GET.get('s_type') == "contact":
            CandidateModels.company_Hide_Fields_request.objects.update_or_create(company_id_id=company.id,
                                                                                 profile_id_id=profile.id,
                                                                                 candidate_id_id=candidate.id,
                                                                                 defaults={
                                                                                     'contact': -1,
                                                                                 })

        return HttpResponse(True)

    else:
        return HttpResponse(False)


def demo(request):
    return render(request, 'company/demo.html')


def candidate_detail(request, url):
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
    profile_id_get = CandidateModels.CandidateProfile.objects.get(url_name=url)
    activeprofile = CandidateModels.Profile.objects.get(candidate_id=profile_id_get.candidate_id, active=True)
    hire = {}
    company_data_status = {}
    # activeprofile=CandidateModels.Profile.objects.get(id=profile_id_get.profile_id)
    if activeprofile.active:
        profile = profile_id_get.profile_id
        candidate_id = ''
        if request.user.is_authenticated:
            print('asdddasddas')
            if request.user.is_company:
                candidate_id = profile_id_get.candidate_id_id
                # hire=CandidateModels.objects.filter(profile_id=activeprofile.id,candidate_id=candidate_id,company_id=User.objects.get(id=request.user.id))
                company_data_status = CandidateModels.company_data_request.objects.filter(profile_id=activeprofile.id,
                                                                                          candidate_id=candidate_id,
                                                                                          company_id=User.objects.get(
                                                                                              id=request.user.id))
            elif request.user.is_candidate:
                candidate_id = request.user.id
        else:
            candidate_id = profile_id_get.candidate_id.id
        user = User.objects.get(id=activeprofile.candidate_id.id)
        print()
        count = 0
        year_title_pairs = {}
        print("before hide field")
        print("user is ", user)
        print("profile is ", profile)
        hidefield = CandidateModels.Candidate_Hide_Fields.objects.get(candidate_id=user, profile_id=profile)
        profile_show = CandidateModels.CandidateProfile.objects.get(candidate_id=user, profile_id=profile)
        skills = CandidateModels.CandidateSkillUserMap.objects.filter(candidate_id=user, profile_id=profile)
        start_years = []
        end_years = []
        last_used = 0
        skill_names = ''
        if skills:
            for i in skills:
                skill_names += i.skill.name + ','
                if i.last_used == 'present':
                    last_used = int(datetime.datetime.now().year)
                else:
                    last_used = int(i.last_used)
                start_year = int(last_used) - int(i.total_exp)
                start_years.append(start_year)
                end_years.append(int(last_used))
        year_salary_pair = []
        company_names = []
        experiences = CandidateModels.CandidateExperience.objects.filter(candidate_id=user, profile_id=activeprofile.id)
        if experiences:
            for i in experiences:
                company_names.append(i.company.company_name)
                end_date_year = 0
                end_date_month = 0
                if i.end_date:
                    if i.end_date == 'present':
                        end_date_year = int(datetime.datetime.now().year)
                        end_date_month = datetime.datetime.now().strftime("%B")
                    else:
                        end_date_year = int(i.end_date.split(',')[1])
                        end_date_month = i.end_date.split(',')[0]

                    salary_start_year = int(i.start_date.split(',')[1])
                    salary_start_year += month[i.start_date.split(',')[0]] / 12
                    salary_end_year = end_date_year
                    salary_end_year += month[end_date_month] / 12
                    year_salary_pair.append([salary_start_year, i.start_salary])
                    year_salary_pair.append([salary_end_year, i.end_salary])
                    if int(end_date_year) not in list(year_title_pairs.keys()):
                        year_title_pairs[end_date_year] = []
                        year_title_pairs[end_date_year].append(i)
                    else:
                        year_title_pairs[int(i.end_date.split(',')[1])].append(i)
                # year_title_pairs.add(i.end_date.split(',')[1],i.job_profile_name)
        company_names = ','.join(company_names)
        educations = CandidateModels.CandidateEducation.objects.filter(candidate_id=user, profile_id=activeprofile.id)
        if educations:
            for i in educations:
                count += 1
                if i.end_date:
                    if int(i.end_date.split(',')[1]) not in list(year_title_pairs.keys()):
                        year_title_pairs[int(i.end_date.split(',')[1])] = []
                        year_title_pairs[int(i.end_date.split(',')[1])].append(i)
                    else:
                        year_title_pairs[int(i.end_date.split(',')[1])].append(i)
        certificates = CandidateModels.CandidateCertificationAttachment.objects.filter(candidate_id=user,
                                                                                       profile_id=activeprofile.id)
        if certificates:
            for i in certificates:
                count += 1
                if i.year:
                    if int(i.year) not in list(year_title_pairs.keys()):
                        year_title_pairs[int(i.year)] = []
                        year_title_pairs[int(i.year)].append(i)
                    else:
                        year_title_pairs[int(i.year)].append(i)
        awards = CandidateModels.CandidateAward.objects.filter(candidate_id=user, profile_id=activeprofile.id)
        if awards:
            for i in awards:
                count += 1
                if i.year:
                    if int(i.year) not in list(year_title_pairs.keys()):
                        year_title_pairs[int(i.year)] = []
                        year_title_pairs[int(i.year)].append(i)
                    else:
                        year_title_pairs[int(i.year)].append(i)
        print(hidefield.edu_document)
        portfolio = CandidateModels.CandidatePortfolio.objects.filter(candidate_id=user, profile_id=activeprofile.id)
        if portfolio:
            for i in portfolio:
                count += 1
                if i.year:
                    if int(i.year) not in list(year_title_pairs.keys()):
                        year_title_pairs[int(i.year)] = []
                        year_title_pairs[int(i.year)].append(i)
                    else:
                        year_title_pairs[int(i.year)].append(i)
        print(hidefield.edu_document)
        gaps = CandidateModels.Gap.objects.filter(candidate_id=user, profile_id=activeprofile.id)
        print(gaps)
        if gaps:
            for i in gaps:
                print("enterrred for loop for jgaps")
                if i.end_date:
                    if int(i.end_date.split(',')[1]) not in list(year_title_pairs.keys()):
                        print("ifffffffffffffffffffffffffffffffffffffffffffffff")
                        year_title_pairs[int(i.end_date.split(',')[1])] = []
                        year_title_pairs[int(i.end_date.split(',')[1])].append(i)
                    else:
                        year_title_pairs[int(i.end_date.split(',')[1])].append(i)
        print("gaaaaaaaaaps ", gaps)
        print(year_title_pairs)
    sorted_key_list = sorted(year_title_pairs)
    sorted_key_list.reverse()
    job_preference = CandidateModels.CandidateJobPreference.objects.filter(candidate_id=user)

    return render(request, 'company/Dashbord-search-c-detail.html',
                  {'company_data_status': company_data_status, 'profile': profile_id_get, 'gaps': gaps,
                   'hidefield': hidefield, 'profile_show': profile_show, 'user': user, 'experiences': experiences,
                   'portfolios': portfolio, 'educations': educations, 'certificates': certificates, 'awards': awards,
                   'sorted_keys': sorted_key_list, 'year_title_pairs': year_title_pairs, 'start_years': start_years,
                   'end_years': end_years, 'skills': skill_names, 'year_salary_pair': year_salary_pair,
                   'company_names': company_names, 'job_preference': job_preference})


def doc_request(request):
    active = models.CandidateHire.objects.filter(company_id=request.user.id, request_status=1).values('id', 'message',
                                                                                                      'company_id',
                                                                                                      'candidate_id',
                                                                                                      'profile_id')
    new_request = models.CandidateHire.objects.filter(company_id=request.user.id, request_status=0).values('id',
                                                                                                           'message',
                                                                                                           'company_id',
                                                                                                           'candidate_id',
                                                                                                           'profile_id')
    archive = models.CandidateHire.objects.filter(company_id=request.user.id, request_status=-1).values('id', 'message',
                                                                                                        'company_id',
                                                                                                        'candidate_id',
                                                                                                        'profile_id')
    print('========================', active)
    data_active = CandidateModels.company_data_request.objects.filter(company_id=request.user.id, status=1).values('id',
                                                                                                                   'message',
                                                                                                                   'company_id',
                                                                                                                   'candidate_id',
                                                                                                                   'profile_id')
    data_new_request = CandidateModels.company_data_request.objects.filter(company_id=request.user.id,
                                                                           status=0).values('id', 'message',
                                                                                            'company_id',
                                                                                            'candidate_id',
                                                                                            'profile_id')
    data_archive = CandidateModels.company_data_request.objects.filter(company_id=request.user.id, status=-2).values(
        'id', 'message', 'company_id', 'candidate_id', 'profile_id')
    print('========================', data_new_request)
    shortlisted_candidates = models.ShortlistedCandidates.objects.filter(company_id=request.user.id)
    print("^^^^^^^^^^^^++++++++++++++++++++", shortlisted_candidates)
    return render(request, 'company/request.html',
                  {'active': active, 'new_request': new_request, 'archive': archive, 'data_active': data_active,
                   'data_new_request': data_new_request, 'data_archive': data_archive,
                   'shortlisted_candidates': shortlisted_candidates})


def document_request(request):
    data = json.loads(request.body.decode('UTF-8'))
    # data = json.loads()
    print("======data============", data)
    CandidateModels.company_data_request.objects.create(message=data['message'],
                                                        candidate_id=User.objects.get(id=int(data['candidate'])),
                                                        profile_id=CandidateModels.Profile.objects.get(
                                                            id=int(data['profile'])),
                                                        company_id=User.objects.get(id=request.user.id))
    return HttpResponse(True)


def company_profile(request):
    if request.user.is_authenticated:
        if request.user.is_company:
            profile = models.CompanyProfile.objects.filter(company_id=User.objects.get(id=request.user.id))
            if not profile:
                return redirect('company:add_edit_profile')
            else:
                profile = models.CompanyProfile.objects.get(company_id=User.objects.get(id=request.user.id))
            return render(request, 'company/Dashbord-company-profile.html', {'profile': profile})
        else:
            return render(request, 'accounts/404.html')
    else:
        return render(request, 'accounts/404.html')


from django.db.models import Count, Sum


def shortlist_candidate(request):
    if request.user.is_authenticated:
        if request.user.is_company:
            user_id = User.objects.get(id=int(request.GET.get('user_id')))
            company_id = User.objects.get(id=request.user.id)
            if models.ShortlistedCandidates.objects.filter(candidate_id=user_id, company_id=company_id).exists():
                models.ShortlistedCandidates.objects.filter(candidate_id=user_id,
                                                            company_id=company_id).delete()
                return HttpResponse('removed')
            else:
                models.ShortlistedCandidates.objects.create(candidate_id=user_id,
                                                            company_id=company_id)
                return HttpResponse('shortlisted')
        else:
            return HttpResponse(False)
    else:
        return HttpResponse(False)


# ############################################    ATS    #################################################


# ########################    Internal Candidate    ########################

def add_candidate(request):
    context = {'notice_period': CandidateModels.NoticePeriod.objects.all(),
               'working_day_types': models.InternalCandidatePreference.working_day_choices,
               'company_type': models.CompanyType.objects.all(), 'countries': CandidateModels.Country.objects.all(),
               'sources': models.Source.objects.all(), 'languages': CandidateModels.Languages.objects.all()}
    if request.method == 'POST':
        # Basic Details
        # internal_candidate_skill_obj = models.InternalCandidateProfessionalSkill.objects.create(internal_candidate_id=models.InternalCandidate.objects.get(id=6))
        # for i in request.POST.getlist('professional_skills'):
        #     if i.isnumeric():
        #         main_skill_obj = models.CandidateModels.Skill.objects.get(id=i)
        #         internal_candidate_skill_obj.skills.add(main_skill_obj)
        #     else:
        #         if models.InternalCandidateAddedSkill.objects.filter(name=i).exists():
        #             custom_added_skill_obj = models.InternalCandidateAddedSkill.objects.get(name=i)
        #         else:
        #             custom_added_skill_obj = models.InternalCandidateAddedSkill.objects.create(name=i)
        #         internal_candidate_skill_obj.custom_added_skills.add(custom_added_skill_obj)
        # gender = CandidateModels.Gender.objects.get(name=request.POST.get('gender'))
        # current_country = CandidateModels.Country.objects.get(id=request.POST.get('current_country'))
        # current_state = CandidateModels.State.objects.get(id=request.POST.get('current_state'))
        # current_city = CandidateModels.City.objects.get(id=request.POST.get('current_city'))
        # if request.POST.get('checked-address') == '':
        #     permanent_country = current_country
        #     permanent_state = current_state
        #     permanent_city = current_city
        #     permanent_zip_code = request.POST.get('current_zip_code')
        #     permanent_street = request.POST.get('current_street')
        # else:
        #     permanent_country = CandidateModels.Country.objects.get(id=request.POST.get('permanent_country'))
        #     permanent_state = CandidateModels.State.objects.get(id=request.POST.get('permanent_state'))
        #     permanent_city = CandidateModels.City.objects.get(id=request.POST.get('permanent_city'))
        #     permanent_zip_code = request.POST.get('permanent_zip_code')
        #     permanent_street = request.POST.get('permanent_street')
        # temp, created=models.InternalCandidate.objects.update_or_create(email=request.POST.get('email'),defaults={
        #                                                 'first_name':request.POST.get('first_name'),
        #                                                 'last_name':request.POST.get('last_name'),
        #                                                 'email':request.POST.get('email'),
        #                                                 'gender':gender,
        #                                                 'dob':request.POST.get('dob'),
        #                                                 'phone_no':request.POST.get('phone_no'),
        #                                                 'current_country':current_country,
        #                                                 'current_state':current_state,
        #                                                 'current_city':current_city,
        #                                                 'current_zip_code':request.POST.get('current_zip_code'),
        #                                                 'current_street':request.POST.get('current_street'),
        #                                                 'permanent_country':permanent_country,
        #                                                 'permanent_state':permanent_state,
        #                                                 'permanent_city':permanent_city,
        #                                                 'permanent_zip_code':permanent_zip_code,
        #                                                 'permanent_street':permanent_street,
        #                                           })
        #
        # # PROFESSIONAL DETAILS
        # exp_year = request.POST.get('professional-experience-year')
        # exp_month = request.POST.get('professional-experience-month')
        # experience = exp_year + '.' + exp_month
        # notice_period = CandidateModels.NoticePeriod.objects.get(id=request.POST.get('professional-notice-period'))
        # models.InternalCandidateProfessionalDetail.objects.create(internal_candidate_id=temp, experience=experience,
        #                                                           current_job_title=request.POST.get('professional-job-title'),
        #                                                           highest_qualification=request.POST.get('professional-high-qualify'),
        #                                                           expected_salary=request.POST.get('professional-expect-salary'),
        #                                                           current_salary=request.POST.get('professional-current-salary'),
        #                                                           current_employer=request.POST.get('professional-current-emp'),
        #                                                           skills=request.POST.get('professional_skills'),
        #                                                           notice_period=notice_period)
        #
        # # education details
        #
        # edu_institute = request.POST.getlist('edu_institute')
        # edu_department = request.POST.getlist('edu_department')
        # edu_degree = request.POST.getlist('edu_degree')
        # edu_duration = request.POST.getlist('edu_duration')
        # start_month = request.POST.getlist('edu-detail-start-month')
        # start_year = request.POST.getlist('edu-detail-start-year')
        # end_month = request.POST.getlist('edu-detail-end-month')
        # end_year = request.POST.getlist('edu-detail-end-year')
        # is_pursuing = request.POST.getlist('edu_pursuing_check')
        #
        # print('edu is_pursuing >>>>>>>>',is_pursuing)
        #
        # for inst, dept, deg, dur, start_month, start_year, end_month, end_year, is_purs \
        #         in zip_longest(edu_institute, edu_department, edu_degree, edu_duration, start_month, start_year,
        #                        end_month, end_year, is_pursuing, fillvalue=None):
        #     inst_id, created = CandidateModels.UniversityBoard.objects.get_or_create(name=inst)
        #     deg_id, created = CandidateModels.Degree.objects.get_or_create(name=deg)
        #     start_date = CandidateModels.Month.objects.get(id=start_month).name + "," + " " + start_year
        #     if is_purs == '':
        #         is_purs = True
        #         end_date = None
        #     else:
        #         end_date = CandidateModels.Month.objects.get(id=end_month).name + "," + " " + end_year
        #         is_purs = False
        #     models.InternalCandidateEducation.objects.create(internal_candidate_id=temp,
        #                                                      university_board=inst_id,
        #                                                      department=dept,
        #                                                      degree=deg_id,
        #                                                      duration=dur,
        #                                                      start_date=start_date,
        #                                                      end_date=end_date,
        #                                                      is_pursuing=is_purs
        #                                                      )
        #
        # # experience details
        #
        # job_title = request.POST.getlist('exper_details_jobtitle')
        # company_name = request.POST.getlist('exper_details_companyname')
        # start_month = request.POST.getlist('exper_details_start_month')
        # start_year = request.POST.getlist('exper_details_start_year')
        # end_month = request.POST.getlist('exper_details_end_month')
        # end_year = request.POST.getlist('exper_details_end_year')
        # skills = request.POST.getlist('exper_details_skills')
        # summary = request.POST.getlist('exper_details_summary')
        # work_status = request.POST.getlist('checked_workstatus')
        # # notice_period = request.POST.getlist('exper_details_notice')
        #
        # print('\n\nwork_status >>>>>>>', work_status)
        #
        # for (job_ti, company_name, start_m, start_y, end_m, end_y, skills, summary, work_stat)\
        #         in zip_longest(job_title, company_name, start_month, start_year, end_month,
        #                                 end_year, skills, summary, work_status, fillvalue=None):
        #     start_date = CandidateModels.Month.objects.get(id=start_m).name + "," + " " + start_y
        #     if end_month is not None:
        #         print('>>>>>>>end_m', end_m, type(end_m))
        #         # end_date = CandidateModels.Month.objects.get(id=end_m).name + "," + " " + end_y
        #         end_date = None
        #         work_stat = False
        #     else:
        #         work_stat = True
        #         end_date = None
        #     models.InternalCandidateExperience.objects.create(internal_candidate_id=temp,
        #                                                       job_title=job_ti,
        #                                                       company_name=company_name,
        #                                                       start_date=start_date,
        #                                                       end_date=end_date,
        #                                                       summary=summary,
        #                                                       skills=skills,
        #                                                       currently_working=work_stat)
        #
        # # PREFERENCE
        #
        # country = request.POST.get('preference_country')
        # city = request.POST.get('preference_city')
        # company_type = request.POST.get('preference_company_type')
        # working_day = request.POST.get('preference_working_day')
        # if len(country) and len(city) and len(company_type) and len(working_day):
        #     country = CandidateModels.Country.objects.get(id=request.POST.get('preference_country'))
        #     city = CandidateModels.City.objects.get(id=request.POST.get('preference_city'))
        #     company_type = models.CompanyType.objects.get(id=request.POST.get('preference_company_type'))
        #     models.InternalCandidatePreference.objects.create(internal_candidate_id=temp,country=country,
        #                                                       city=city,company_type=company_type,
        #                                                       working_days=request.POST.get('preference_working_day'))
        #
        # # Portfolio
        #
        # project_name = request.POST.getlist('project_name')
        # project_link = request.POST.getlist('project_link')
        # portfolio_attachment = request.FILES.getlist('portfolio_attachment')
        # print('port attach', portfolio_attachment)
        # portfolio_description = request.POST.getlist('portfolio_description')
        #
        # for (name, link, attachment, descrip) in zip_longest(project_name, project_link,
        #                                                      portfolio_attachment, portfolio_description,fillvalue=None):
        #     models.InternalCandidatePortfolio.objects.create(internal_candidate_id=temp,
        #                                                      project_name=name,project_link=link,
        #                                                      attachment=attachment,
        #                                                      description=descrip)
        temp = models.InternalCandidate.objects.get(id=6)
        # Source
        if request.POST.get('source'):
            selected_source = models.Source.objects.get(id=request.POST.get('source'))
            if selected_source.name == 'Other':
                other_source = request.POST.get('other_source')
                models.InternalCandidateSource.objects.create(internal_candidate_id=temp,
                                                              source_id=selected_source,
                                                              custom_source_name=other_source)
            else:
                models.InternalCandidateSource.objects.create(internal_candidate_id=temp, source_id=selected_source)

        #
        # # Attachment
        #
        # resume_file = request.FILES.get('attachment_resume')
        # print('resume_file', resume_file)
        # models.InternalCandidateAttachment.objects.create(
        #     internal_candidate_id=temp,
        #     file_name='resume', file=resume_file)
        # file_names = request.POST.getlist('file_name')
        # print('file_names', file_names)
        # files = request.FILES.getlist('file')
        # print('files', files)
        # if len(file_names) > 0 and len(files) > 0:
        #     for (name, file) in zip_longest(file_names,files):
        #         models.InternalCandidateAttachment.objects.create(internal_candidate_id=temp, file_name=name,
        #                                                           file=file)
    return render(request, 'company/ATS/add_candidate.html', context)


signer = Signer()


def all_candidates(request):
    data = []
    candidates = models.InternalCandidate.objects.all()
    for candidate in candidates:
        candidate_dict = {'id': candidate.id, 'name': candidate.first_name + ' ' + candidate.last_name,
                          'city': candidate.current_city.city_name}
        professional_detail = models.InternalCandidateProfessionalDetail.objects.get(internal_candidate_id=candidate.id)
        candidate_dict['job_title'] = professional_detail.current_job_title
        candidate_dict['experience'] = professional_detail.experience
        candidate_dict['expected_salary'] = professional_detail.expected_salary
        candidate_dict['notice_period'] = professional_detail.notice_period.notice_period
        candidate_dict['source'] = models.InternalCandidateSource.objects.get(internal_candidate_id=candidate.id)
        data.append(candidate_dict)
    context = {'candidates': data}
    return render(request, 'company/ATS/all_candidates.html', context)


def view_candidate(request, candidate_id):
    if models.InternalCandidate.objects.filter(id=candidate_id).exists():
        context = {}
        basic_detail = models.InternalCandidate.objects.get(id=candidate_id)
        professional_detail = models.InternalCandidateProfessionalDetail.objects.get(internal_candidate_id=candidate_id)
        candidate_preference = models.InternalCandidatePreference.objects.get(internal_candidate_id=candidate_id)
        candidate_education = models.InternalCandidateEducation.objects.filter(internal_candidate_id=candidate_id)
        candidate_experience = models.InternalCandidateExperience.objects.filter(internal_candidate_id=candidate_id)
        candidate_attachments = models.InternalCandidateAttachment.objects.filter(internal_candidate_id=candidate_id)
        candidate_source = models.InternalCandidateSource.objects.get(internal_candidate_id=candidate_id)
        main_skills = models.InternalCandidateProfessionalSkill.objects.get(
            internal_candidate_id=candidate_id).skills.all()
        custom_added_skill = models.InternalCandidateProfessionalSkill.objects.get(
            internal_candidate_id=candidate_id).custom_added_skills.all()
        notes = models.InternalCandidateNotes.objects.filter(internal_candidate_id=candidate_id)
        skills = []
        for i in main_skills:
            skills.append(i.name)
        for i in custom_added_skill:
            skills.append(i.name)

        context['basic_detail'] = basic_detail
        context['professional_detail'] = professional_detail
        context['candidate_preference'] = candidate_preference
        context['candidate_education'] = candidate_education
        context['candidate_experience'] = candidate_experience
        context['attachments'] = candidate_attachments
        context['sources'] = candidate_source
        context['skills'] = skills
        context['notes'] = notes
        return render(request, 'company/ATS/Candidate_view.html', context)
    else:
        return HttpResponse('Invalid Url')


def internal_candidate_notes(request):
    if request.method == 'POST':
        print('\n\n\nmessage', request.POST.get('message'))
        print('\n\n\ndate', request.POST.get('date'))
        print('\n\n\nuser', request.POST.get('user'))
        print('\n\n\ndepartment', request.POST.get('department'))
        print('\n\n\ncandidate_id', request.POST.get('candidate_id'))
        # try:
        candidate = models.InternalCandidate.objects.get(id=request.POST.get('candidate_id'))
        created_note = models.InternalCandidateNotes.objects.create(internal_candidate_id=candidate,
                                                                    note=request.POST.get('message'),
                                                                    time=request.POST.get('date'))
        return JsonResponse({'date': created_note.time, 'status': 'success'}, safe=False)
        # except:
        # return JsonResponse({'status': 'failed'}, safe=False)

# ########################    Internal Candidate  End  ########################


# ########################    JOB    ########################

def job_creation(request):
    context = {}
    context['job_types'] = models.JobTypes.objects.all()
    context['job_status'] = models.JobStatus.objects.all()
    context['job_shift'] = models.JobShift.objects.all()
    context['countries'] = CandidateModels.Country.objects.all()
    context['industry_types'] = CandidateModels.IndustryType.objects.all()
    if request.method == 'POST':
        if request.POST.get('remote_job') == 'yes':
            remote_job = True
        else:
            remote_job = False
        user_id = User.objects.get(id=request.user.id)
        job_type = models.JobTypes.objects.get(id=request.POST.get('job_type'))
        status = models.JobStatus.objects.get(id=request.POST.get('status'))
        industry_type = CandidateModels.IndustryType.objects.get(id=request.POST.get('industry_type'))
        country_id = CandidateModels.Country.objects.get(id=request.POST.get('country'))
        city_id = CandidateModels.City.objects.get(id=request.POST.get('city'))

        job_id = models.JobCreation.objects.create(company_id=user_id, job_title=request.POST.get('job_title'),
                                                   job_type=job_type, target_date=request.POST.get('target_date'),
                                                   status=status, industry_type=industry_type, remote_job=remote_job,
                                                   min_salary=request.POST.get('Min'),
                                                   max_salary=request.POST.get('Max'),
                                                   experience_year=request.POST.get('exp_years'),
                                                   experience_month=request.POST.get('exp_month'),
                                                   job_description=request.POST.get('job_description'),
                                                   benefits=request.POST.get('job_benefit'),
                                                   requirements=request.POST.get('job_requirement'), country=country_id,
                                                   city=city_id, zip_code=request.POST.get('zipcode'))
        job_shifts = request.POST.getlist('job_shifts')
        for shift in models.JobShift.objects.all():
            if shift.name in job_shifts:
                job_shift_obj = models.JobShift.objects.get(id=shift.id)
                models.CompanyJobShift.objects.create(job_id=job_id, job_shift_id=job_shift_obj, status=True)
            else:
                job_shift_obj = models.JobShift.objects.get(id=shift.id)
                models.CompanyJobShift.objects.create(job_id=job_id, job_shift_id=job_shift_obj, status=False)
        return redirect('company:workflow_selection', id=job_id.id)
    return render(request, 'company/ATS/job_creation.html', context)


def job_openings_table(request):
    jobs = models.JobCreation.objects.filter(company_id=User.objects.get(id=request.user.id))
    return render(request, 'company/ATS/job_openings_table.html', {'jobs': jobs})


def job_openings_requests(request):
    return render(request, 'company/ATS/job_openings_requests.html')


def created_job_view(request, id):
    job_obj = models.JobCreation.objects.get(id=id)
    job_workflow = models.JobWorkflow.objects.get(job_id=job_obj)
    main_workflow = models.Workflows.objects.get(id=job_workflow.workflow_id.id)
    workflow_stages = models.WorkflowStages.objects.filter(workflow=main_workflow).order_by('sequence_number')
    if request.method == 'POST':
        job_obj.is_publish = True
        job_obj.save()
    return render(request, 'company/ATS/job-creation-view.html', {'workflow_stages': workflow_stages,
                                                                  'job_obj': job_obj,
                                                                  'main_workflow': main_workflow})

# ########################    JOB Creation End   ########################


# ########################    Workflow Management    ########################


def workflow_list(request):
    data = []
    flows = models.Workflows.objects.filter(is_configured=True)
    for flow in flows:
        stages = models.WorkflowStages.objects.filter(workflow=flow).order_by('sequence_number')
        stage_list = [stage.stage.name for stage in stages]
        data.append({'workflow_id': flow.id, 'workflow_name': flow.name, 'stages': stage_list})
    return render(request, 'company/ATS/workflow_list.html', {'stage': data})


def create_workflow(request):
    if request.method == 'POST':
        workflow_data = json.loads(request.body.decode('UTF-8'))
        workflow_obj = models.Workflows.objects.create(name=workflow_data['name'])
        print('\n\n workflow data', workflow_data['data'])
        print('\n\n workflow name', workflow_data['name'])
        count = 1
        for data in workflow_data['data']:
            stage_obj = models.Stage_list.objects.get(id=data['stage_id'])
            category_obj = models.TemplateCategory.objects.get(id=data['cate_id'])
            template_obj = models.Template_creation.objects.get(id=data['temp_id'])
            models.WorkflowStages.objects.create(stage_name=data['stage_name'], workflow=workflow_obj, stage=stage_obj,
                                                 category=category_obj, template=template_obj, sequence_number=count)
            count += 1
        request.session['workflow_configure'] = workflow_obj.id
        return HttpResponse(True)
        # return redirect("company:workflow_configuration")
    return render(request, 'company/ATS/create_workflow.html')


def edit_workflow(request, id):
    print('w -id', id)
    workflow_obj = models.Workflows.objects.get(id=id)
    stages = models.WorkflowStages.objects.filter(workflow=workflow_obj)
    if request.method == 'POST':
        workflow_data = json.loads(request.body.decode('UTF-8'))
        print('\n\n workflow data1', workflow_data['data'])
        print('\n\n workflow name', workflow_data['name'])

        # workflow
        workflow_obj = models.Workflows.objects.get(id=id)
        workflow_obj.name = workflow_data['name']
        workflow_obj.is_configured = False
        workflow_obj.save()

        # stages

        models.WorkflowStages.objects.filter(workflow=workflow_obj).delete()
        count = 1
        for data in workflow_data['data']:
            stage_obj = models.Stage_list.objects.get(id=data['stage_id'])
            category_obj = models.TemplateCategory.objects.get(id=data['cate_id'])
            template_obj = models.Template_creation.objects.get(id=data['temp_id'])
            models.WorkflowStages.objects.create(stage_name=data['stage_name'], workflow=workflow_obj, stage=stage_obj,
                                                 category=category_obj, template=template_obj, sequence_number=count)
            count += 1
        request.session['workflow_configure'] = workflow_obj.id
        return HttpResponse(True)
    return render(request, 'company/ATS/create_workflow.html', {'stages': stages,
                                                                'workflow_obj': workflow_obj, 'is_edit': True})


def get_workflow_data(request):
    stages_data = []
    category_data = []
    template_data = []
    stages = models.Stage_list.objects.all()
    for i in stages:
        # stage
        if models.TemplateCategory.objects.filter(stage=i.id).exists():
            stage_dict = {'key': i.id, 'stage_name': i.name}
            stages_data.append(stage_dict)
            print('satge name', i.name)

            # category
            categories = models.TemplateCategory.objects.filter(stage=i.id)
            cate_list = []
            for cat in categories:
                if models.Template_creation.objects.filter(category=cat.id).exists():
                    cate_dict = {'key': cat.id, 'cate_name': cat.name}
                    cate_list.append(cate_dict)
                tem_list = []
                templates = models.Template_creation.objects.filter(category=cat.id)
                for temp in templates:
                    tem_dict = {'key': temp.id, 'temp_name': temp.name}
                    tem_list.append(tem_dict)
                temp_dict = {'cateKey': cat.id, 'temp_list': tem_list}
                template_data.append(temp_dict)
            categ_dict = {'stageKey': i.id, 'cate_list': cate_list}
            category_data.append(categ_dict)

    # print('\n\ncategory_data', category_data)
    print('\n\ntemplate_data', template_data)
    return JsonResponse(
        {'stages_data': list(stages_data), 'category_data': list(category_data), 'template_data': list(template_data)})


def workflow_configuration(request):
    if request.session.has_key('workflow_configure'):
        print('session workflow id', request.session['workflow_configure'])
        workflow_obj = models.Workflows.objects.get(id=request.session['workflow_configure'])
        workflow_stages = models.WorkflowStages.objects.filter(workflow=workflow_obj)
        if request.method == 'POST':
            print('post called', request.POST.get('jcr-action'))
            print('jcr-short-list', request.POST.get('jcr-short-list'))
            print('jcr-on-hol', request.POST.get('jcr-on-hold'))
            print('jcr-rejected', request.POST.get('jcr-rejected'))

            if request.POST.get('jcr-action') == 'auto':
                is_automation = True
            else:
                is_automation = False

            for stage in workflow_stages:
                if stage.stage.name == 'JCR':
                    models.WorkflowConfiguration.objects.create(workflow_stage=stage,
                                                                interviewer=None,
                                                                is_automation=is_automation,
                                                                shortlist=request.POST.get('jcr-short-list'),
                                                                onhold=request.POST.get('jcr-on-hold'),
                                                                reject=request.POST.get('jcr-rejected'))
                if stage.stage.name == 'Prerequisites':
                    models.WorkflowConfiguration.objects.create(workflow_stage=stage)
            workflow_obj.is_configured = True
            workflow_obj.save()
            del request.session['workflow_configure']
            return redirect('company:workflow_list')
        return render(request, 'company/ATS/workflow_configuration.html', {'workflow_name': workflow_obj.name,
                                                                           'workflow_stages': workflow_stages})
    else:
        return render(request, 'accounts/404.html')


def workflow_selection(request, id):
    workflows = models.Workflows.objects.filter(is_configured=True)
    if request.method == 'POST':
        print('called', id)
        print('\n\nselected_workflow', request.POST.get('selected_workflow'))
        workflow = models.Workflows.objects.get(id=request.POST.get('selected_workflow'))
        job_obj = models.JobCreation.objects.get(id=id)
        models.JobWorkflow.objects.create(job_id=job_obj, workflow_id=workflow)
        return redirect('company:created_job_view', id=job_obj.id)
    return render(request, 'company/ATS/workflow_selection.html', {'workflows': workflows})


# ########################    Workflow Management End   ########################


# ################################################################################


# PRE REQUISITES VIEW


def pre_requisites(request):
    return render(request, 'company/ATS/prerequisites-form.html')


def save_pre_requisites(request):
    if request.method == 'POST':
        print("saaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaavvvvvvvvvvvvvvvvvvvved")
        data = json.loads(request.body.decode('UTF-8'))
        print("data", data)
        template_data = data[0]['template-data']
        print("tempplate _data ", template_data)
        pre_requisite, created = models.PreRequisites.objects.get_or_create(
            stage=models.Stage_list.objects.get(id=int(request.session['create_template']['stageid'])),
            category=models.TemplateCategory.objects.get(id=int(request.session['create_template']['categoryid'])),
            template=models.Template_creation.objects.get(id=int(request.session['create_template']['templateid'])),
            company_id=User.objects.get(id=request.user.id))
        pre_requisite.data = data[0]['template-data']
        pre_requisite.html_data = data[0]['html-data']
        pre_requisite.save()
        data = {}
        data['status'] = True
        data['url'] = 'http://192.168.1.72:8000/company/template_listing/'
        return HttpResponse(json.dumps(data))
    else:
        data = {}
        data['status'] = False
        data['url'] = ''
        return HttpResponse(json.dumps(data))


# jcr
def get_jcr_data(request):
    context = {}
    jcr_obj_temp = models.JCR.objects.filter(company_id=User.objects.get(id=request.user.id),
                                             stage=models.Stage_list.objects.get(
                                                 id=int(request.session['create_template']['stageid'])),
                                             category=models.TemplateCategory.objects.get(
                                                 id=int(request.session['create_template']['categoryid'])),
                                             template=models.Template_creation.objects.get(
                                                 id=int(request.session['create_template']['templateid']))).order_by(
        '-id')
    jcr_categories = jcr_obj_temp.filter(pid=None).order_by('id')
    print("jcrrrrrrrr all daaaata", jcr_obj_temp)
    context['getStoreData'] = []
    for category in jcr_categories:
        add_details_item = []
        sub_categories = jcr_obj_temp.filter(pid=category)
        for sub_category in sub_categories:
            sub_type = []
            leaf_nodes = jcr_obj_temp.filter(pid=sub_category)

            for node in leaf_nodes:
                detail = []
                det_data = jcr_obj_temp.filter(pid=node.id)
                for detail_data in det_data:
                    detail.append({
                        'id': detail_data.id,
                        'title': detail_data.name,
                        'percent': detail_data.ratio
                    })
                sub_type.append({'question': node.name,
                                 'id': node.id,
                                 'q_percent': node.ratio,
                                 'matching': node.flag,
                                 'details': detail
                                 })
            add_details_item.append({'cat_type': sub_category.name,
                                     'id': sub_category.id,
                                     'cate_percent': sub_category.ratio,
                                     'cat_subtype': sub_type})

        context['getStoreData'].append({'cat_name': category.name, 'cat_value': category.ratio, 'id': category.id,
                                        'addDetailsItem': add_details_item})

    if len(context['getStoreData']) == 0:
        print("kabkjasdadadakasdjkasdkljd;ldk;laskd;ldksd===================================ndlkmnklmadasdm")
        context['getStoreData'] = 'null'
    getStoreData = json.dumps(context)
    return getStoreData


def jcr(request):
    print("===============")
    if request.method == 'POST':
        jcr_data = json.loads(request.body.decode('UTF-8'))
        for main_data in jcr_data['updateCategoryList']:
            models.JCR.objects.update_or_create(name=main_data['cat_name'],
                                                company_id=User.objects.get(id=request.user.id),
                                                stage=models.Stage_list.objects.get(
                                                    id=int(request.session['create_template']['stageid'])),
                                                category=models.TemplateCategory.objects.get(
                                                    id=int(request.session['create_template']['categoryid'])),
                                                template=models.Template_creation.objects.get(
                                                    id=int(request.session['create_template']['templateid'])),
                                                defaults={'name': main_data['cat_name'],
                                                          'ratio': main_data['cat_value']})
        return JsonResponse(get_jcr_data(request), safe=False)
    return render(request, 'company/ATS/jcr.html', {'getStoreData': get_jcr_data(request)})


def insert_jcr(request):
    context = {}
    jcr_data = []
    jcr_obj = models.JCR.objects.filter(company_id=User.objects.get(id=request.user.id),
                                        stage=models.Stage_list.objects.get(
                                            id=int(request.session['create_template']['stageid'])),
                                        category=models.TemplateCategory.objects.get(
                                            id=int(request.session['create_template']['categoryid'])),
                                        template=models.Template_creation.objects.get(
                                            id=int(request.session['create_template']['templateid'])),
                                        pid=None).order_by(
        'id')
    if jcr_obj.exists():
        for record in jcr_obj:
            obj_dict = {}
            obj_dict['cat_name'] = record.name
            obj_dict['cat_value'] = record.ratio
    if request.method == 'POST':
        jcr_data = json.loads(request.body.decode('UTF-8'))
        # print(jcr_data['getStoreData'])
        for record in jcr_data['getStoreData']:
            for add_item in record['addDetailsItem']:
                if add_item['id']:
                    # get_key = models.JCR.objects.get(id=int(record['id']))
                    models.JCR.objects.update_or_create(company_id=User.objects.get(id=request.user.id),
                                                        stage=models.Stage_list.objects.get(
                                                            id=int(request.session['create_template']['stageid'])),
                                                        category=models.TemplateCategory.objects.get(
                                                            id=int(request.session['create_template']['categoryid'])),
                                                        template=models.Template_creation.objects.get(
                                                            id=int(request.session['create_template']['templateid'])),
                                                        id=int(add_item['id']), defaults={
                            'name': add_item['cat_type'], 'ratio': add_item['cate_percent'], 'flag': None,
                        })
                else:
                    get_key = models.JCR.objects.get(name=record['cat_name'], company_id=request.user.id,
                                                     stage=models.Stage_list.objects.get(
                                                         id=int(request.session['create_template']['stageid'])),
                                                     category=models.TemplateCategory.objects.get(
                                                         id=int(request.session['create_template']['categoryid'])),
                                                     template=models.Template_creation.objects.get(
                                                         id=int(request.session['create_template']['templateid'])))
                    models.JCR.objects.update_or_create(company_id=User.objects.get(id=request.user.id),
                                                        stage=models.Stage_list.objects.get(
                                                            id=int(request.session['create_template']['stageid'])),
                                                        category=models.TemplateCategory.objects.get(
                                                            id=int(request.session['create_template']['categoryid'])),
                                                        template=models.Template_creation.objects.get(
                                                            id=int(request.session['create_template']['templateid'])),
                                                        pid=get_key, name=add_item['cat_type'], defaults={
                            'name': add_item['cat_type'], 'ratio': int(add_item['cate_percent']), 'flag': None,
                        })
                if add_item['cat_subtype']:
                    print("?>>>>>>>>>>>>>>>>>", add_item['cat_subtype'])
                    for cat_subtype in add_item['cat_subtype']:

                        if 'id' in [*cat_subtype] and cat_subtype['id']:
                            print("================", cat_subtype['id'])
                            models.JCR.objects.update_or_create(company_id=User.objects.get(id=request.user.id),
                                                                stage=models.Stage_list.objects.get(id=int(
                                                                    request.session['create_template']['stageid'])),
                                                                category=models.TemplateCategory.objects.get(
                                                                    id=int(request.session['create_template'][
                                                                               'categoryid'])),
                                                                template=models.Template_creation.objects.get(id=int(
                                                                    request.session['create_template']['templateid'])),
                                                                id=cat_subtype['id'],
                                                                defaults={
                                                                    'name': cat_subtype['question'],
                                                                    'ratio': cat_subtype['q_percent'], 'flag': None,
                                                                })
                        else:
                            get_item_key = models.JCR.objects.get(name=add_item['cat_type'], company_id=request.user.id,
                                                                  stage=models.Stage_list.objects.get(id=int(
                                                                      request.session['create_template']['stageid'])),
                                                                  category=models.TemplateCategory.objects.get(
                                                                      id=int(request.session['create_template'][
                                                                                 'categoryid'])),
                                                                  template=models.Template_creation.objects.get(id=int(
                                                                      request.session['create_template'][
                                                                          'templateid'])))
                            models.JCR.objects.update_or_create(company_id=User.objects.get(id=request.user.id),
                                                                stage=models.Stage_list.objects.get(id=int(
                                                                    request.session['create_template']['stageid'])),
                                                                category=models.TemplateCategory.objects.get(
                                                                    id=int(request.session['create_template'][
                                                                               'categoryid'])),
                                                                template=models.Template_creation.objects.get(id=int(
                                                                    request.session['create_template']['templateid'])),
                                                                pid=get_item_key, name=cat_subtype['question'],
                                                                defaults={
                                                                    'name': cat_subtype['question'],
                                                                    'ratio': int(cat_subtype['q_percent']),
                                                                    'flag': cat_subtype['matching'],
                                                                })
                        if cat_subtype['details']:
                            for detail in cat_subtype['details']:
                                if 'id' in [*detail] and detail['id']:
                                    models.JCR.objects.update_or_create(company_id=User.objects.get(id=request.user.id),
                                                                        stage=models.Stage_list.objects.get(id=int(
                                                                            request.session['create_template'][
                                                                                'stageid'])),
                                                                        category=models.TemplateCategory.objects.get(
                                                                            id=int(request.session['create_template'][
                                                                                       'categoryid'])),
                                                                        template=models.Template_creation.objects.get(
                                                                            id=int(request.session['create_template'][
                                                                                       'templateid'])),
                                                                        id=detail['id'], defaults={
                                            'name': detail['title'], 'ratio': int(detail['percent']), 'flag': None,
                                        })
                                else:
                                    get_sub_item_key = models.JCR.objects.get(name=cat_subtype['question'],
                                                                              company_id=request.user.id,
                                                                              stage=models.Stage_list.objects.get(
                                                                                  id=int(request.session[
                                                                                             'create_template'][
                                                                                             'stageid'])),
                                                                              category=models.TemplateCategory.objects.get(
                                                                                  id=int(request.session[
                                                                                             'create_template'][
                                                                                             'categoryid'])),
                                                                              template=models.Template_creation.objects.get(
                                                                                  id=int(request.session[
                                                                                             'create_template'][
                                                                                             'templateid'])))
                                    models.JCR.objects.update_or_create(company_id=User.objects.get(id=request.user.id),
                                                                        stage=models.Stage_list.objects.get(id=int(
                                                                            request.session['create_template'][
                                                                                'stageid'])),
                                                                        category=models.TemplateCategory.objects.get(
                                                                            id=int(request.session['create_template'][
                                                                                       'categoryid'])),
                                                                        template=models.Template_creation.objects.get(
                                                                            id=int(request.session['create_template'][
                                                                                       'templateid'])),
                                                                        pid=get_sub_item_key, name=detail['title'],
                                                                        defaults={
                                                                            'name': detail['title'],
                                                                            'ratio': int(detail['percent']),
                                                                            'flag': None,
                                                                        })
        models.Template_creation.objects.filter(
            stage=models.Stage_list.objects.get(id=int(request.session['create_template']['stageid'])),
            category=models.TemplateCategory.objects.get(id=int(request.session['create_template']['categoryid'])),
            id=int(request.session['create_template']['templateid'])).update(status=True)
        data = {"true": "true", 'getStoreData': get_jcr_data(request)}
        return JsonResponse(json.dumps(data), safe=False)


def remove_jcr(request):
    print("=============================remove_jcr--------")
    if request.method == 'POST':
        jcr_data = json.loads(request.body.decode('UTF-8'))
        if jcr_data['deleteid']:
            models.JCR.objects.get(company_id=User.objects.get(id=request.user.id), stage=models.Stage_list.objects.get(
                id=int(request.session['create_template']['stageid'])),
                                   category=models.TemplateCategory.objects.get(
                                       id=int(request.session['create_template']['categoryid'])),
                                   template=models.Template_creation.objects.get(
                                       id=int(request.session['create_template']['templateid'])),
                                   id=int(jcr_data['deleteid'])).delete()
            data = {"true": "true", 'getStoreData': get_jcr_data(request)}
            return JsonResponse(data)
        else:
            data = {"true": "false", 'getStoreData': get_jcr_data(request)}
            return JsonResponse(data)


def remove_sub_jcr(request):
    print("=============================remove_sub_jcr")
    if request.method == 'POST':
        jcr_data = json.loads(request.body.decode('UTF-8'))

        if jcr_data['deleteid']:
            models.JCR.objects.get(company_id=User.objects.get(id=request.user.id), stage=models.Stage_list.objects.get(
                id=int(request.session['create_template']['stageid'])),
                                   category=models.TemplateCategory.objects.get(
                                       id=int(request.session['create_template']['categoryid'])),
                                   template=models.Template_creation.objects.get(
                                       id=int(request.session['create_template']['templateid'])),
                                   id=int(jcr_data['deleteid'])).delete()
            data = {"true": "true", 'getStoreData': get_jcr_data(request)}
            return JsonResponse(data)
        else:
            data = {"true": "false", 'getStoreData': get_jcr_data(request)}
            return JsonResponse(data)


def jcr_preview(request):
    context = {}
    jcr_obj_temp = models.JCR.objects.filter(company_id=User.objects.get(id=request.user.id),
                                             stage=models.Stage_list.objects.get(
                                                 id=int(request.session['create_template']['stageid'])),
                                             category=models.TemplateCategory.objects.get(
                                                 id=int(request.session['create_template']['categoryid'])),
                                             template=models.Template_creation.objects.get(
                                                 id=int(request.session['create_template']['templateid']))).order_by(
        '-id')
    jcr_categories = jcr_obj_temp.filter(pid=None).order_by('id')
    context['getStoreData'] = []
    for category in jcr_categories:
        if int(category.ratio) != 0:
            add_details_item = []
            sub_categories = jcr_obj_temp.filter(pid=category)
            for sub_category in sub_categories:
                sub_type = []
                leaf_nodes = jcr_obj_temp.filter(pid=sub_category)

                for node in leaf_nodes:
                    detail = []
                    det_data = jcr_obj_temp.filter(pid=node.id)
                    for detail_data in det_data:
                        detail.append({
                            'id': detail_data.id,
                            'title': detail_data.name,
                            'percent': detail_data.ratio
                        })
                    sub_type.append({'question': node.name,
                                     'id': node.id,
                                     'q_percent': node.ratio,
                                     'matching': node.flag,
                                     'details': detail
                                     })
                add_details_item.append({'cat_type': sub_category.name,
                                         'id': sub_category.id,
                                         'cate_percent': sub_category.ratio,
                                         'cat_subtype': sub_type})

            context['getStoreData'].append({'cat_name': category.name, 'cat_value': category.ratio, 'id': category.id,
                                            'addDetailsItem': add_details_item})
    if len(context['getStoreData']) == 0:
        context['getStoreData'] = None
    getStoreData = json.dumps(context['getStoreData'])

    return render(request, 'company/ATS/jcr-template-preview.html', {'getStoreData': getStoreData})


def template_listing(request):
    get_stage = models.Stage_list.objects.filter(active=True).order_by('id')
    get_category = models.TemplateCategory.objects.filter(
        company_id=User.objects.get(id=request.user.id)).order_by('id')
    get_templates = models.Template_creation.objects.filter(company_id=User.objects.get(id=request.user.id))
    if request.method == 'POST':
        print('\n\n\nstage>>>', request.POST.get('stage'))
        print('\n\n\ncategory>>>', request.POST.get('category'))
        print('\n\n\ntemplate-name>>>', request.POST.get('template-name'))
        print('\n\n\ntemplate-description>>>', request.POST.get('template-description'))

        template_create = models.Template_creation.objects.create(name=request.POST.get('template-name'),
                                                                  description=request.POST.get('template-description'),
                                                                  stage=models.Stage_list.objects.get(
                                                                      id=int(request.POST.get('stage'))),
                                                                  category=models.TemplateCategory.objects.get(
                                                                      id=int(request.POST.get('category'))),
                                                                  company_id=User.objects.get(id=request.user.id))
        stage = models.Stage_list.objects.get(id=int(request.POST.get('stage')))
        request.session['create_template'] = {'stageid': template_create.stage.id,
                                              'categoryid': template_create.category.id,
                                              'templateid': template_create.id}
        print('stage name  >>>>>..', stage.name)
        data = {}
        data['status'] = True
        if str(stage.name).upper() == 'JCR':
            return redirect('company:jcr')
            # data['url'] = 'http://192.168.1.72:8000/company/jcr/'
        if str(stage.name).upper() == 'PREREQUISITES':
            print('\n\n\n in >>>>>>>>>>>>')
            return redirect('company:pre_requisites')
            # data['url'] = 'http://192.168.1.72:8000/company/pre_requisites/'
        # if str(stage.name).upper() == 'MCQ TEST':
        #     data['url'] = 'http://192.168.1.72:8000/company/add_exam_template/'
        #     return HttpResponse(json.dumps(data))
        if str(stage.name).upper() == 'JOB CREATION':
            return redirect('company:job_creation')
            # data['url'] = 'http://192.168.1.72:8000/company/job_creation/'
            # return HttpResponse(json.dumps(data))
    return render(request, 'company/ATS/template-creation.html',
                  {'stage': get_stage, 'get_category': get_category, 'get_templates': get_templates})


def add_category(request):
    if request.method == 'POST':
        category_name = json.loads(request.body.decode('UTF-8'))
        print("======================================", category_name)
        create_stage_id = models.TemplateCategory.objects.create(name=category_name['add_category'],
                                                                 stage=models.Stage_list.objects.get(
                                                                     id=int(category_name['stage_id'])),
                                                                 company_id=User.objects.get(id=request.user.id))
        create_stage_id.save()
        data = {}
        data['status'] = True
        data['cat_id'] = create_stage_id.id
        return HttpResponse(json.dumps(data))


def delete_category(request):
    if request.method == 'POST':
        category_data = json.loads(request.body.decode('UTF-8'))
        models.TemplateCategory.objects.get(id=int(category_data['cat_id']),
                                            stage=models.Stage_list.objects.get(id=int(category_data['stage_id'])),
                                            company_id=User.objects.get(id=request.user.id)).delete()
        return HttpResponse(True)


def update_category(request):
    if request.method == 'POST':
        category_data = json.loads(request.body.decode('UTF-8'))
        print(category_data)
        category_get = models.TemplateCategory.objects.get(id=int(category_data['cat_id']),
                                                           stage=models.Stage_list.objects.get(
                                                               id=int(category_data['stage_id'])),
                                                           company_id=User.objects.get(id=request.user.id))
        category_get.name = category_data['cat_name']
        category_get.save()
        return HttpResponse(True)
    else:
        return HttpResponse(False)


def get_category(request):
    if request.method == 'POST':
        category_data = json.loads(request.body.decode('UTF-8'))
        category_get = models.TemplateCategory.objects.filter(
            stage=models.Stage_list.objects.get(id=int(category_data['stage_id'])),
            company_id=User.objects.get(id=request.user.id))
        print("============------", category_get)
        data = {}
        data['status'] = True
        data['category_get'] = serializers.serialize('json', category_get)
        return HttpResponse(json.dumps(data))
    else:
        return HttpResponse(False)


# def create_template(request):
#     if request.method == 'POST':
#         template_data = json.loads(request.body.decode('UTF-8'))
#         template_create = models.Template_creation.objects.create(name=template_data['template_name'],
#                                                                   description=template_data['template_discriiption'],
#                                                                   stage=models.Stage_list.objects.get(
#                                                                       id=int(template_data['stage_id'])),
#                                                                   category=models.TemplateCategory.objects.get(
#                                                                       id=int(template_data['category_id'])),
#                                                                   company_id=User.objects.get(id=request.user.id))
#         print("============------", template_data)
#         template_create.save()
#         get_stage = models.Stage_list.objects.get(id=int(template_data['stage_id']))
#         request.session['create_template'] = {'stageid': template_create.stage.id,
#                                               'categoryid': template_create.category.id,
#                                               'templateid': template_create.id}
#         data = {}
#         data['status'] = True
#         if str(get_stage.name).upper() == 'JCR':
#             return redirect('company:jcr')
#             # data['url'] = 'http://192.168.1.72:8000/company/jcr/'
#         if str(get_stage.name).upper() == 'PREREQUISITES':
#             return redirect('company:pre_requisites')
#             # data['url'] = 'http://192.168.1.72:8000/company/pre_requisites/'
#         # if str(get_stage.name).upper() == 'MCQ TEST':
#         #     data['url'] = 'http://192.168.1.72:8000/company/add_exam_template/'
#         #     return HttpResponse(json.dumps(data))
#         if str(get_stage.name).upper() == 'JOB CREATION':
#             return redirect('company:job_creation')
#             # data['url'] = 'http://192.168.1.72:8000/company/job_creation/'
#             # return HttpResponse(json.dumps(data))
#     else:
#         return HttpResponse(False)


def edit_template(request):
    if request.method == 'POST':
        template_data = json.loads(request.body.decode('UTF-8'))
        template_get = models.Template_creation.objects.get(id=int(template_data['template_id']),
                                                            stage=models.Stage_list.objects.get(
                                                                id=int(template_data['stage_id'])),
                                                            category=models.TemplateCategory.objects.get(
                                                                id=int(template_data['cat_id'])),
                                                            company_id=User.objects.get(id=request.user.id))
        get_stage = models.Stage_list.objects.get(id=int(template_data['stage_id']))
        data = {}
        data['status'] = True
        if str(get_stage.name).upper() == 'JCR':
            request.session['create_template'] = {'stageid': template_get.stage.id,
                                                  'categoryid': template_get.category.id, 'templateid': template_get.id}
            data['url'] = 'http://192.168.1.72:8000/company/jcr/'
            return HttpResponse(json.dumps(data))
        if str(get_stage.name).upper() == 'PREREQUISITES':
            data['url'] = 'http://192.168.1.72:8000/company/pre_requisites/'
            return HttpResponse(json.dumps(data))
        if str(get_stage.name).upper() == 'MCQ TEST':
            data['url'] = 'http://192.168.1.72:8000/company/add_exam_template/'
            return HttpResponse(json.dumps(data))
        if str(get_stage.name).upper() == 'JOB CREATION':
            data['url'] = 'http://192.168.1.72:8000/company/job_update/'
            return HttpResponse(json.dumps(data))
    else:
        return HttpResponse(False)


def delete_template(request):
    if request.method == 'POST':
        template_data = json.loads(request.body.decode('UTF-8'))
        models.Template_creation.objects.get(id=int(template_data['template_id']),
                                             category=models.TemplateCategory.objects.get(
                                                 id=int(template_data['cat_id'])),
                                             stage=models.Stage_list.objects.get(id=int(template_data['stage_id'])),
                                             company_id=User.objects.get(id=request.user.id)).delete()
        return HttpResponse(True)


def view_job(request, id):
    job = models.JobCreation.objects.get(id=id)
    return render(request, 'company/ATS/job-opening-view.html', {'job_obj': job})
