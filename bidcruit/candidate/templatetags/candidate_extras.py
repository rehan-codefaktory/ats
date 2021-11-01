from django.http import request
import candidate
from django import template
from candidate.models import CandidateProfile,Profile,CandidateProfile, Profile,CandidateExpDocuments
from accounts.models import User
from company import models as Companymodels
import math
register = template.Library()

 
 
@register.filter()
def to_split(value):
    # print('=================================',value.split(",")[1])
    s_split=value.split(",")[1]
    return s_split[1:]


@register.filter()
def to_str(value):
    return str(value)


@register.filter()
def to_type(value):
    print('==============================',type(value))
    # return str(value)


@register.filter()
def range(min=5):
    return range(min)


@register.filter()
def get_profile_url(value,login_user):
    print(value,login_user)
    url_=CandidateProfile.objects.get(profile_id=value,candidate_id=User.objects.get(id=login_user))
    if url_.custom_url:
        return url_.custom_url
    else:
        return url_.url_name


@register.filter()
def get_profile_designation(value,login_user):
    print(value,login_user)
    designation_=CandidateProfile.objects.get(profile_id=value,candidate_id=User.objects.get(id=login_user))
    return designation_.designation


@register.filter()
def get_companyname(value):
    user = User.objects.get(id=value)
    companyname = str(user.company_name)
    return companyname
@register.filter()
def get_company_image(value):
    print('=============',value)
    print('=======',type(value))
    # user = User.objects.get(id=value)
    logo = Companymodels.CompanyProfile.objects.get(company_id=int(value))
    print('=============',logo)
    return logo.company_logo.url


@register.filter()
def get_user_image(user_id):
    user_obj = User.objects.get(id=user_id)
    if user_obj.is_candidate:
        profiles = Profile.objects.filter(candidate_id=user_obj.id)
        if profiles:
            for i in profiles:
                if i.active == True:
                    active_profile = i
                    candidate_profile = CandidateProfile.objects.get(profile_id=active_profile)
                    return candidate_profile.user_image.url
        else:
            return '/static/chat/images/user_image.jpg'

    else:
        if user_obj.is_company:
            if Companymodels.CompanyProfile.objects.filter(company_id=user_obj.id).exists():
                logo = Companymodels.CompanyProfile.objects.get(company_id=user_obj.id)
                return logo.company_logo.url
            else:
                return '/static/chat/images/user_image.jpg'
        else:
            return '/static/chat/images/user_image.jpg'


@register.filter()
def get_exp_documents(experience):
    exp_documents =CandidateExpDocuments.objects.filter(candidate_exp_id=experience)
    return exp_documents


@register.filter()
def get_exp_year_value(profile):
    return str(math.trunc(profile.total_experience))


@register.filter()
def get_exp_month_value(profile):
    total_exp =str(profile.total_experience)
    if total_exp == '30+':
        return "30+"
    else:
        total_exp = total_exp.split('.')
        total_exp = total_exp[-1]
        if total_exp == '':
            return 0
        else:
            return total_exp

   
@register.filter()
def convert_date_format(dob):
    dob = dob.split('/')
    return dob[2] + '-' + dob[1] + '-' + dob[0]


@register.filter()
def get_start_month(obj):
    start_date = obj.start_date.split(',')
    return start_date[0]


@register.filter()
def get_start_year(obj):
    start_date = obj.start_date.split(',')
    return start_date[1]


@register.filter()
def get_end_month(obj):
    print("get end montgh vs called")
    if obj.end_date != 'present':
        end_date = obj.end_date.split(',')
        return end_date[0]
    else:
        return None


@register.filter()
def get_end_year(obj):
    if obj.end_date != 'present':
        end_date = obj.end_date.split(',')
        print('\n\n\nend_date yaear >>>>>>>>', end_date[1])
        return end_date[1]
    else:
        return None
        
        
@register.filter()
def get_file_name(value):
    print("valueeee",value)
    # name, extension = os.path.splitext(value.exp_document.name)
    value = value.name.split('/')
    return value[len(value)-1]

