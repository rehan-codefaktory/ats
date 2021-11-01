import candidate
from django.db import models
from datetime import date
from django.utils.timezone import now
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.utils.translation import gettext_lazy as _
from accounts.models import User
import random
import os
from django.utils import timezone
from tinymce.models import HTMLField
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image, ImageDraw
from bidcruit import settings
from django.core.files.storage import FileSystemStorage


def generate_pk():
    number = random.randint(1000, 99999)
    return 'candidate-{}-{}'.format(timezone.now().strftime('%y%m%d'), number)


#  ##################################### Common Models ########################################################


class Month(models.Model):
    name = models.CharField(max_length=100)


class Languages(models.Model):
    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    language_name = models.CharField(max_length=200)


class Fluency(models.Model):
    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    fluency = models.CharField(max_length=200)


class Country(models.Model):
    country_name = models.CharField(max_length=200)
    country_sort_name = models.CharField(max_length=10)
    country_phone_code = models.CharField(max_length=200)

    def __str__(self):
        return str(self.id)


class State(models.Model):
    state_name = models.CharField(max_length=200)
    country_code = models.ForeignKey(Country, related_name="state_country_id", on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)


class City(models.Model):
    city_name = models.CharField(max_length=200)
    state_code = models.ForeignKey(State, related_name="state_id", on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)


class Gender(models.Model):
    name = models.CharField(max_length=200)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)

    def __str__(self):
        return str(self.id)


class MaritalType(models.Model):
    name = models.CharField(max_length=200)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)

    def __str__(self):
        return str(self.id)


class Degree(models.Model):
    name = models.CharField(max_length=200)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)

    def __str__(self):
        return str(self.id)


class UniversityBoard(models.Model):
    name = models.CharField(max_length=200)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)
    update_at = models.DateTimeField(max_length=200, null=True)

    def __str__(self):
        return str(self.id)


class Company(models.Model):
    company_name = models.CharField(max_length=50)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)

    def __str__(self):
        return str(self.id)


class Tags(models.Model):
    name = models.CharField(max_length=50)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)

    def __str__(self):
        return str(self.id)


class Skill(models.Model):
    name = models.CharField(max_length=50)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)

    def __str__(self):
        return str(self.id)


class NoticePeriod(models.Model):
    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    notice_period = models.CharField(max_length=300)


class IndustryType(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return str(self.id)


class CandidateProfileTheme(models.Model):
    image = models.ImageField()
    template_name = models.CharField(max_length=50)


#  ##################################### Common Models Ends ########################################################


class UploadCv(models.Model):
    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    candidate_id = models.ForeignKey(User, related_name="user_resume_id", on_delete=models.CASCADE, null=True)
    resume = models.FileField(verbose_name="candidate_resume", upload_to='resume/%Y/%m/%d')
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)


class ThemeColor(models.Model):
    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    candidate_id = models.ForeignKey(User, related_name="resume_theme_color", on_delete=models.CASCADE,
                                     null=True)
    background = models.CharField(max_length=50)
    primary = models.CharField(max_length=50)
    accent = models.CharField(max_length=50, null=True)
    text = models.CharField(max_length=50)


class ThemeFont(models.Model):
    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    candidate_id = models.ForeignKey(User, related_name="candidate_theme_font", on_delete=models.CASCADE,
                                     null=True)
    font_name = models.CharField(max_length=50)
    font_size = models.CharField(max_length=50)


class ThemeLayout(models.Model):
    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    candidate_id = models.ForeignKey(User, related_name="resume_theme_layout", on_delete=models.CASCADE,
                                     null=True)
    layout_name = models.CharField(max_length=50)
    layout_block_number = models.CharField(max_length=50)
    section_name = models.CharField(max_length=50)


class ThemeActive(models.Model):
    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    candidate_id = models.ForeignKey(User, related_name="resume_theme_active", on_delete=models.CASCADE,
                                     null=True)
    theme_name = models.CharField(max_length=50)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)


class ForgotPassword(models.Model):
    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    old_password = models.CharField(max_length=20)
    forgot_time = models.DateTimeField(max_length=200)
    candidate_id = models.ForeignKey(User, related_name="candidate_forgot_password", on_delete=models.CASCADE)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)

    def __str__(self):
        return str(self.id)
# ******************************* Final Models ******************************* #

# ****** Step 1 (user profile)******  #


class Profile(models.Model):
    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    candidate_id = models.ForeignKey(User, related_name="multiple_profile", on_delete=models.CASCADE,
                                     null=True)
    profile_name = models.CharField(max_length=50)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True,null=True)
    update_at = models.DateTimeField(max_length=200, null=True)
    url = models.CharField(max_length=15,default ='')
    active = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)


class CandidateProfile(models.Model):
    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    contact_no = models.CharField(max_length=10)
    address = models.CharField(max_length=200)
    dob = models.CharField(max_length=20, null=True)
    # subtitle = models.CharField(max_length=200, null=True)
    website = models.CharField(max_length=60, null=True)
    candidate_id = models.ForeignKey(User, related_name="candidate_profile", on_delete=models.CASCADE,
                                     null=True)
    country = models.ForeignKey(Country, related_name="candidate_country", on_delete=models.CASCADE, null=True)
    state = models.ForeignKey(State, related_name="candidate_state", on_delete=models.CASCADE, null=True)
    city = models.ForeignKey(City, related_name="candidate_city", on_delete=models.CASCADE, null=True)
    zip_code = models.CharField(max_length=8, null=True)
    marital_status = models.ForeignKey(MaritalType, related_name="candidate_martial_status", on_delete=models.CASCADE,
                                       null=True)
    gender = models.ForeignKey(Gender, related_name="candidate_gender", on_delete=models.CASCADE, null=True)
    user_image = models.ImageField(verbose_name="candidate_profile_image", upload_to='profile_image/%Y/%m/%d')
    notice_period = models.ForeignKey(NoticePeriod, related_name="candidate_notice_period", on_delete=models.CASCADE,
                                      null=True)
    url_name = models.CharField(max_length=50,null=True)
    custom_url=models.CharField(max_length=300,null=True)
    current_salary = models.IntegerField(null=True)
    expected_salary_min = models.CharField(null=True, max_length=50)
    expected_salary_max = models.CharField(null=True, max_length=50)
    total_experience = models.FloatField(null=True)
    designation = models.CharField(max_length=50,null=True)
    preferred_cities = models.CharField(null=True,max_length=200)
    qr_code = models.ImageField(verbose_name="candidate_qr_code", upload_to='qr_code/%Y/%m/%d',null=True)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)
    update_at = models.DateTimeField(max_length=200, null=True)
    final_status = models.BooleanField(default=False)
    technical_knowledge = HTMLField(null=True)
    about_me = HTMLField(null=True)
    resume = models.FileField(null=True)
    resume_password = models.CharField(max_length=500, null=True)
    profile_id=models.ForeignKey(Profile,related_name='candidateprofile_profile_id',on_delete=models.CASCADE, null=True)

    def __str__(self):
        return str(self.id)

    # def save(self, *args, **kwargs):
    #     # qr = qrcode.QRCode(
    #     #     version=1,
    #     #     error_correction=qrcode.constants.ERROR_CORRECT_L,
    #     #     box_size=6,
    #     #     border=4,
    #     # )
    #     # qr.add_data('qr_share_link/test')
    #     # qr.make(fit=True)
    #     # img = qr.make_image(fill_color="black", back_color="white")
    #     # blob = BytesIO()
    #     # img.save(blob, 'JPEG')
    #     random_no = random.randint(1000, 99999)
    #     url_name = self.candidate_id.first_name+'_'+self.candidate_id.last_name + '_' + str(random_no)
    #     print(url_name)
    #     qr_share_link = "localhost:8000/candidate/candidate_web_profile/" + url_name
    #     qrcode_img = qrcode.make(qr_share_link)
    #     canvas = Image.new('RGB', (290, 290), 'white')
    #     canvas.paste(qrcode_img)
    #     fname = f'qr_code-{self.candidate_id}.png'
    #     buffer = BytesIO()
    #     canvas.save(buffer, 'PNG')
    #     self.qr_code.save(fname, File(buffer))
    #     # canvas.close()
    #     super().save(*args, **kwargs)

# *************************************


class CandidateSocialNetwork(models.Model):
    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    candidate_id = models.ForeignKey(User, related_name="candidate_network", on_delete=models.CASCADE,
                                     null=True)
    network_name = models.CharField(max_length=50, null=True)
    url = models.URLField(max_length=200, null=True)
    record_id = models.CharField(max_length=200, null=True)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)
    update_at = models.DateTimeField(max_length=200, null=True)
    final_status = models.BooleanField(default=False)
    profile_id = models.ForeignKey(Profile,related_name='candidatesocial_profile_id',on_delete=models.CASCADE, null=True)

    def __str__(self):
        return str(self.id)


# ****** Step 2 (Education)******  #
def degree_document_path_handler(instance,filename):
#    file_extension = filename.split('.')
    path='{}{}/Candidate_Education/{}'.format(settings.MEDIA_ROOT,instance.candidate_id.id,instance.degree.name)
    print("degreeee path",path)
    print("does the folder exists",os.path.exists(path))
    if not os.path.exists(path):
        os.makedirs(path)
    return '{}{}/Candidate_Education/{}/{}'.format(settings.MEDIA_ROOT,instance.candidate_id.id,instance.degree.name,filename)


class CandidateEducation(models.Model):

    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    candidate_id = models.ForeignKey(User, related_name="candidate_id", on_delete=models.CASCADE, null=True)
    university_board = models.ForeignKey(UniversityBoard, related_name="candidate_university", on_delete=models.CASCADE,
                                         null=True)
    degree = models.ForeignKey(Degree, related_name="candidate_degree", on_delete=models.CASCADE, null=True)
    field = models.CharField(max_length=200, null=True)
    grade = models.CharField(max_length=10,null=True)
    start_date = models.CharField(max_length=50, null=True)
    end_date = models.CharField(max_length=50, null=True)
    certificate = models.FileField(max_length=1000, null=True, upload_to=degree_document_path_handler)
    gap_count = models.FloatField(max_length=50, null=True)
    gap_description = models.CharField(max_length=200, null=True)
    summary = HTMLField(null=True)
    record_id = models.CharField(max_length=200, null=True)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)
    update_at = models.DateTimeField(max_length=200, null=True)
    final_status = models.BooleanField(default=False)
    profile_id = models.ForeignKey(Profile,related_name='candidateeducation_profile_id',on_delete=models.CASCADE, null=True)

    def extension(self):
        name, extension = os.path.splitext(self.certificate.name)
        print('\n\n\n>>>>>>>>extension', extension)
        if extension == '.pdf':
            return 'pdf'
        if extension == '.doc':
            return 'doc'
        if extension == '.jpg' or extension == '.png' or extension == '.jpeg':
            return 'img'

    def __str__(self):
        return str(self.id)


# ****** Step 3 (work experience)******  #

class CandidateExperience(models.Model):
    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    job_profile_name = models.CharField(max_length=100, null=True)
    company = models.ForeignKey(Company, related_name="candidate_company_experience", on_delete=models.CASCADE,
                                null=True)
    start_date = models.CharField(max_length=100, null=True)
    end_date = models.CharField(max_length=100, null=True)
    start_salary = models.CharField(max_length=100, null=True)
    end_salary = models.CharField(max_length=100, null=True)
    job_description_responsibility = HTMLField(null=True)
    website = models.CharField(max_length=100, null=True)
    gap_count = models.FloatField(max_length=100, null=True)
    gap = models.CharField(max_length=100, null=True)
    candidate_id = models.ForeignKey(User, related_name="candidate_experience", on_delete=models.CASCADE,
                                     null=True)
    record_id = models.CharField(max_length=200, null=True)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)
    update_at = models.DateTimeField(max_length=200, null=True)
    final_status = models.BooleanField(default=False)
    profile_id = models.ForeignKey(Profile,related_name='candidateexperience_profile_id',on_delete=models.CASCADE, null=True)

    def extension(self):
        name, extension = os.path.splitext(self.certificate.name)
        print('\n\n\n>>>>>>>>extension', extension)
        if extension == '.pdf':
            return 'pdf'
        if extension == '.doc':
            return 'doc'
        if extension == '.jpg' or extension == '.png' or extension == '.jpeg':
            return 'img'

    def __str__(self):
        return str(self.id)


# ****** Step 4 (certificate)******  #


def certificate_document_path_handler(instance,filename):
#    file_extension = filename.split('.')
    path = '{}{}/Candidate Certificate/{}'.format(settings.MEDIA_ROOT,instance.candidate_id.id,instance.name_of_certificate)
    if not os.path.exists(path):
        os.makedirs(path)
    return '{}{}/Candidate Certificate/{}/{}'.format(settings.MEDIA_ROOT,instance.candidate_id.id,instance.name_of_certificate,filename)
    # return '{}\Candidate Experience\{}'.format(instance.candidate_id.id,filename)


class CandidateCertificationAttachment(models.Model):
    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    candidate_id = models.ForeignKey(User, related_name="candidate_certificate", on_delete=models.CASCADE,
                                     null=True)
    name_of_certificate = models.CharField(max_length=200, null=True)
    attached_certificate = models.FileField(max_length=500,null=True, upload_to=certificate_document_path_handler)
    institute_organisation = models.CharField(max_length=50, null=True)
    summary = HTMLField(null=True)
    year = models.CharField(max_length=50, null=True)
    record_id = models.CharField(max_length=20, null=True)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)
    update_at = models.DateTimeField(max_length=200, null=True)
    final_status = models.BooleanField(default=False)
    profile_id = models.ForeignKey(Profile,related_name='candidatecertification_profile_id',on_delete=models.CASCADE, null=True)

    def extension(self):
        name, extension = os.path.splitext(self.certificate.name)
        print('\n\n\n>>>>>>>>extension', extension)
        if extension == '.pdf':
            return 'pdf'
        if extension == '.doc':
            return 'doc'
        if extension == '.jpg' or extension == '.png' or extension == '.jpeg':
            return 'img'

    def __str__(self):
        return str(self.id)


# *********************************

def awards_document_path_handler(instance,filename):
#    file_extension = filename.split('.')
    path='{}{}/Candidate Awards/{}'.format(settings.MEDIA_ROOT,instance.candidate_id.id,instance.title)
    if not os.path.exists(path):
        os.makedirs(path)
    return '{}{}/Candidate Awards/{}/{}'.format(settings.MEDIA_ROOT,instance.candidate_id.id,instance.title,filename)


class CandidateAward(models.Model):
    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    candidate_id = models.ForeignKey(User, related_name="candidate_award", on_delete=models.CASCADE,
                                     null=True)
    title = models.CharField(max_length=200, null=True)
    award_img = models.FileField(max_length=1000,null=True, upload_to=awards_document_path_handler)
    awarder = models.CharField(max_length=50, null=True)
    year = models.CharField(max_length=50, null=True)
    summary = HTMLField(null=True)
    record_id = models.CharField(max_length=200, null=True)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)
    update_at = models.DateTimeField(max_length=200, null=True)
    final_status = models.BooleanField(default=False)
    profile_id=models.ForeignKey(Profile,related_name='candidateaward_profile_id',on_delete=models.CASCADE, null=True)

# ****** Step 5 (skill)******  #


class CandidateSkillUserMap(models.Model):
    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    candidate_id = models.ForeignKey(User, related_name="candidate_skill_user_map", on_delete=models.CASCADE,
                                     null=True)
    skill = models.ForeignKey(Skill, related_name="candidate_skill_user_map", on_delete=models.CASCADE, null=True)
    total_exp = models.CharField(null=True,max_length=10)
    last_used = models.CharField(null=True,max_length=10)
    record_id = models.CharField(max_length=200, null=True)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)
    update_at = models.DateTimeField(max_length=200, null=True)
    final_status = models.BooleanField(default=False)
    profile_id = models.ForeignKey(Profile,related_name='candidateskill_profile_id', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return str(self.id)


# ****** Step 6 (Portfolio)******  #


def portfolio_document_path_handler(instance,filename):
    
    path='{}{}/Candidate Portfolio/{}'.format(settings.MEDIA_ROOT,instance.candidate_id.id,instance.project_title)
    if not os.path.exists(path):
        os.makedirs(path)
    return '{}{}/Candidate Portfolio/{}/{}'.format(settings.MEDIA_ROOT,instance.candidate_id.id,instance.project_title,filename)


class CandidatePortfolio(models.Model):
    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    candidate_id = models.ForeignKey(User, related_name="User_portfolio", on_delete=models.CASCADE,
                                     null=True)
    project_title = models.CharField(max_length=200, null=True)
    link = models.CharField(max_length=2000, null=True)
    description = models.CharField(max_length=1000, null=True)
    year = models.CharField(max_length=500, null=True)
    learning_from_project = HTMLField(null=True)
    record_id = models.CharField(max_length=200, null=True)
    project_document = models.FileField(max_length=500,null=True, upload_to=portfolio_document_path_handler)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)
    update_at = models.DateTimeField(max_length=200, null=True)
    final_status = models.BooleanField(default=False)
    profile_id=models.ForeignKey(Profile,related_name='candidateportfolio_profile_id',on_delete=models.CASCADE, null=True)

    def extension(self):
        name, extension = os.path.splitext(self.certificate.name)
        print('\n\n\n>>>>>>>>extension', extension)
        if extension == '.pdf':
            return 'pdf'
        if extension == '.doc':
            return 'doc'
        if extension == '.jpg' or extension == '.png' or extension == '.jpeg':
            return 'img'

    def __str__(self):
        return str(self.id)


# ****** Step 7 (summery)******  #

class CandidateSummary(models.Model):
    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    candidate_id = models.ForeignKey(User, related_name="User_summary_id", on_delete=models.CASCADE,
                                     null=True)
    description = models.CharField(max_length=200, null=True)
    tag_line = models.CharField(max_length=100, null=True)
    summary = models.CharField(max_length=500, null=True)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)
    update_at = models.DateTimeField(max_length=200, null=True)
    final_status = models.BooleanField(default=False)
    profile_id=models.ForeignKey(Profile,related_name='candidatesummary_profile_id',on_delete=models.CASCADE, null=True)

    def __str__(self):
        return str(self.id)


# ****** Step 7 (other)******  #

class CandidateOtherField(models.Model):
    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    candidate_id = models.ForeignKey(User, related_name="candidate_other_fields", on_delete=models.CASCADE,
                                     null=True)
    record_id = models.CharField(max_length=200, null=True)
    label = models.CharField(max_length=200, null=True)
    value = models.CharField(max_length=200, null=True)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)
    update_at = models.DateTimeField(max_length=200, null=True)
    final_status = models.BooleanField(default=False)
    profile_id=models.ForeignKey(Profile,related_name='candidateother_profile_id',on_delete=models.CASCADE, null=True)
    def __str__(self):
        return str(self.id)


# ***********************************************


class CandidateLanguage(models.Model):
    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    candidate_id = models.ForeignKey(User, related_name="candidate_language", on_delete=models.CASCADE,
                                     null=True)
    language_id = models.ForeignKey(Languages, related_name="candidate_language_id", on_delete=models.CASCADE,
                                    null=True)
    fluency_id = models.ForeignKey(Fluency, related_name="candidate_fluency_id", on_delete=models.CASCADE, null=True)
    record_id = models.CharField(max_length=200, null=True)
    profile_id=models.ForeignKey(Profile,related_name='candidatelanguage_profile_id',on_delete=models.CASCADE, null=True)


# ************************************************

class CandidateHobbies(models.Model):
    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    candidate_id = models.ForeignKey(User, related_name="candidate_hobby", on_delete=models.CASCADE,
                                     null=True)
    record_id = models.CharField(max_length=200, null=True)
    name = models.CharField(max_length=200, null=True)
    profile_id=models.ForeignKey(Profile,related_name='candidatehobby_profile_id',on_delete=models.CASCADE, null=True)

# ***************************************************


class CandidateReference(models.Model):
    id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    candidate_id = models.ForeignKey(User, related_name="candidate_reference", on_delete=models.CASCADE,
                                     null=True)
    record_id = models.CharField(max_length=200, null=True)
    email = models.EmailField(max_length=200, null=True)
    name = models.CharField(max_length=200, null=True)
    phone = models.CharField(max_length=200, null=True)
    position = models.CharField(max_length=200, null=True)
    summary = models.CharField(max_length=200, null=True)
    profile_id=models.ForeignKey(Profile,related_name='candidatereference_profile_id',on_delete=models.CASCADE, null=True)

# ******************************* Resume theameupload ******************************* #


class Upload_Resume_Theme(models.Model):
    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    Title = models.CharField(max_length=50)
    preview_image = models.FileField(verbose_name="resume__theme_image", upload_to='resume_theme/%Y/%m/%d')
    html_file_name = models.CharField(max_length=50)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)
    update_at = models.DateTimeField(max_length=200, null=True)

    def __str__(self):
        return str(self.id)


class CandidateJobPreference(models.Model):
    job_type_choices = [
        ('PartTime', 'PartTime'),
        ('FullTime', 'FullTime'),
    ]
    number_of_employee_choices = [
        ('1-10', '1-10 employees'),
        ('11-50', '11-50 employees'),
        ('51-200', '51-200 employees'),
        ('201-500', '201-500 employees'),
        ('501-1000', '501-1000 employees'),
        ('1001-5000', '1001-5000 employees'),
        ('5001-10,000', '5001-10,000 employees'),
        ('10,001+', '10,001+ employees'),
    ]
    working_day_choices = [
        ('5day', '5 Days Working'),
        ('6day', '6 Days Working')
    ]
    preferred_shift_choices = [
        ('day', 'Day Shift'),
        ('night', 'Night Shift'),
        ('flexible', 'Flexible'),
        ('any', 'Any of Above')
    ]
    job_type = models.CharField(max_length=50,choices=job_type_choices)
    number_of_employee = models.CharField(max_length=50,choices=number_of_employee_choices)
    working_days = models.CharField(max_length=50,choices=working_day_choices)
    preferred_shift = models.CharField(max_length=50,choices=preferred_shift_choices)
    candidate_id = models.ForeignKey(User, related_name="candidate_job_preferences", on_delete=models.CASCADE,
                                     null=True)
    relocation = models.BooleanField(null=True)
    relocation_cities = models.CharField(max_length=1000,null=True)


class CandidateJobPreferenceOther(models.Model):
    candidate_id = models.ForeignKey(User, related_name='candidate_other_preferences', on_delete=models.CASCADE)
    label = models.CharField(max_length=200)
    value = models.CharField(max_length=300)


class ReferralDetails(models.Model):
    referred_by = models.ForeignKey(User, related_name="referred_by_candidate_id", on_delete=models.CASCADE)
    referred_to = models.ForeignKey(User, related_name="referred_to_candidate_id", on_delete=models.CASCADE)


class Candidate_Hide_Fields(models.Model):
    email = models.IntegerField(default=0)
    # phone_no =models.IntegerField(default=0)
    contact = models.IntegerField(default=0)
    edu_document = models.IntegerField(default=0)
    exp_document = models.IntegerField(default=0)
    portfolio_document = models.IntegerField(default=0)
    certificate_document = models.IntegerField(default=0)
    candidate_id = models.ForeignKey(User, related_name="candidate_hide_field_id", on_delete=models.CASCADE,null = True)
    # profile_id = models.ForeignKey(CandidateProfile, related_name="profile_hide_field_id", on_delete=models.CASCADE)
    profile_id = models.ForeignKey(Profile, related_name="profile_hide_field_id", on_delete=models.CASCADE, null = True)


class Gap(models.Model):
    start_date = models.CharField(null=True,max_length=20)
    end_date = models.CharField(null=True,max_length=20)
    reason = models.CharField(max_length=200,null=True)
    type = models.CharField(max_length=100,null=True)
    record_id = models.CharField(max_length=10,null=True)
    candidate_id = models.ForeignKey(User, related_name="candidate_gap_id", on_delete=models.CASCADE,
                                     null=True)
    profile_id = models.ForeignKey(Profile, related_name="company_gap_profile_id", on_delete=models.CASCADE,
                                   null=True)


def experience_document_path_handler(instance, filename):
        path = '{}{}/Candidate_Experience/{}'.format(settings.MEDIA_ROOT,instance.candidate_id.id,
                                                   instance.candidate_exp_id.company.company_name)
        if not os.path.exists(path):
            os.makedirs(path)
        return '{}{}/Candidate_Experience/{}/{}_{}'.format(settings.MEDIA_ROOT,instance.candidate_id.id,
                                                         instance.candidate_exp_id.company.company_name,
                                                         instance.candidate_exp_id.id, filename)


class CandidateExpDocuments(models.Model):
    candidate_id = models.ForeignKey(User, related_name='candidate_exp_doc', on_delete=models.CASCADE)
    profile_id = models.ForeignKey(Profile, related_name="candidate_profile_id", on_delete=models.CASCADE,null=True)
    candidate_exp_id = models.ForeignKey(CandidateExperience, related_name='candidate_exp_doc', on_delete=models.CASCADE)
    record_id = models.CharField(max_length=10)
    exp_document = models.FileField(max_length=500, null=True, upload_to=experience_document_path_handler)
    document_name = models.CharField(max_length=100, null=True)


class company_data_request(models.Model):
    message=models.CharField(max_length=500,null=True)
    zip_link=models.CharField(max_length=500,null=True)
    status=models.IntegerField(default=0)
    candidate_id = models.ForeignKey(User, related_name="company_candidate_hide_field_id", on_delete=models.CASCADE,null = True)
    profile_id = models.ForeignKey(Profile, related_name="company_profile_hide_field_id", on_delete=models.CASCADE, null = True)
    company_id= models.ForeignKey(User, related_name="company_hide_field_id", on_delete=models.CASCADE,null = True)


class CandidateSEO(models.Model):
    candidate_id = models.ForeignKey(User, related_name="candidate_seo_id", on_delete=models.CASCADE,
                                     null=True)
    looking_for_job = models.BooleanField(default=False)
    google_search = models.BooleanField(default=False)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)
    update_at = models.DateTimeField(max_length=200, null=True) 


class CandidateCounter(models.Model):
    candidate_id = models.ForeignKey(User, related_name="candidate_counter_fields_id", on_delete=models.CASCADE,null=True)
    profile_id = models.ForeignKey(Profile, related_name="profile_counter_fields_id", on_delete=models.CASCADE, null=True)
    ip_address = models.GenericIPAddressField()
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)



def resume_path_handler(instance,filename):
#    file_extension = filename.split('.')
    path='{}{}/Candidate_Resume/{}'.format(settings.MEDIA_ROOT,instance.candidate_id.id,instance.resume)
    if not os.path.exists(path):
        os.makedirs(path)
    return '{}{}/Candidate_Resume/{}/{}'.format(settings.MEDIA_ROOT,instance.candidate_id.id,instance.resume,filename)


class candidate_job_apply_detail(models.Model):
    candidate_id = models.ForeignKey(User, related_name="candidate_job_apply", on_delete=models.CASCADE,null=True)
    gender=models.CharField(max_length=10)
    resume=models.FileField(max_length=500,null=True, upload_to=resume_path_handler)
    contact=models.CharField(max_length=100)
    skill=models.CharField(max_length=100,null=True)
    designation=models.CharField(max_length=100,null=True)
    notice = models.ForeignKey(NoticePeriod, related_name="candidate_applyjob_notice_period", on_delete=models.CASCADE,
                                      null=True)
    current_work=models.CharField(max_length=100,null=True)
    ctc=models.CharField(max_length=100,null=True)
    expectedctc=models.CharField(max_length=100,null=True)
    total_exper=models.CharField(max_length=100,null=True)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)


from company import models as CompanyModels


class JcrFill(models.Model):
    candidate_id = models.ForeignKey(User, related_name="candidate_jcr_apply", on_delete=models.CASCADE, null=True)
    jcr_id = models.ForeignKey(CompanyModels.JCR, related_name="candidate_jcr_id", on_delete=models.CASCADE)
    job_id = models.ForeignKey(CompanyModels.JobCreation, related_name="candidate_job_id", on_delete=models.CASCADE)
    template = models.ForeignKey(CompanyModels.Template_creation, related_name="candidate_template_id",
                                 on_delete=models.CASCADE, null=True)
    company_id = models.ForeignKey(User, related_name='candidate_company_jcr_id', on_delete=models.CASCADE,
                                   null=True)

class JcrRatio(models.Model):
    candidate_id = models.ForeignKey(User, related_name="candidate_jcr_ratio", on_delete=models.CASCADE, null=True)
    Primary = models.CharField(max_length=10)
    Secondary = models.CharField(max_length=10)
    Objective = models.CharField(max_length=10)
    Total = models.CharField(max_length=10)
    job_id = models.ForeignKey(CompanyModels.JobCreation, related_name="candidate_jcrratio_job_id", on_delete=models.CASCADE)
    template = models.ForeignKey(CompanyModels.Template_creation, related_name="candidate_jcrratio_template_id",
                                 on_delete=models.CASCADE, null=True)
    company_id = models.ForeignKey(User, related_name='candidate_jcrratio_company_jcr_id', on_delete=models.CASCADE,
                                   null=True)