from django.db import models
from datetime import date
from django.utils.timezone import now
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from tinymce.models import HTMLField
from candidate import models as CandidateModels
import random
from tinymce.models import HTMLField
import os
from django.utils import timezone


def generate_pk():
    number = random.randint(1000, 99999)
    return 'company-{}-{}'.format(timezone.now().strftime('%y%m%d'), number)

# ##################################### Common Models ########################################################


class CompanyType(models.Model):
    name = models.CharField(max_length=100)


class InternalCandidateAddedSkill(models.Model):
    name = models.CharField(max_length=100)


class Source(models.Model):
    name = models.CharField(max_length=100)

# ##################################### Common Models Ends ########################################################


class CandidateHire(models.Model):
    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    company_id = models.ForeignKey(User, related_name="Company_id", on_delete=models.CASCADE)
    candidate_id = models.ForeignKey(User, related_name="candidate_hire_id", on_delete=models.CASCADE)
    message = models.CharField(max_length=50)
    profile_id = models.ForeignKey(CandidateModels.Profile,related_name='profile_id',null=True,on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    request_status = models.IntegerField(default=0,null=True)

    def __str__(self):
        return str(self.id)


class CandidateSelectedPreference(models.Model):
    # id = models.CharField(default=generate_pk, primary_key=True, max_length=255, unique=True)
    company_id = models.ForeignKey(User, related_name="preference_check_company_id", on_delete=models.CASCADE)
    candidate_id = models.ForeignKey(User, related_name="preference_check_candidate_id", on_delete=models.CASCADE)
    preference_name = models.CharField(max_length=100)
    # preference_id = models.ForeignKey(CandidateModels.CandidateJobPreference, related_name="candidate_preference_id", on_delete=models.CASCADE)
    is_selected = models.BooleanField(null=True)

    def __str__(self):
        return str(self.id)


class CompanyProfile(models.Model):
    employee_count_choices = [
        ('1-10', '1-10 employees'),
        ('11-50', '11-50 employees'),
        ('51-200', '51-200 employees'),
        ('201-500', '201-500 employees'),
        ('501-1000', '501-1000 employees'),
        ('1001-5000', '1001-5000 employees'),
        ('5001-10,000', '5001-10,000 employees'),
        ('10,001+', '10,001+ employees'),
    ]
    company_type_choices=[
        ('Public Company','Public Company'),
        ('Educational','Educational'),
        ('Self Employed','Self Employed'),
        ('Government Agency','Government Agency'),
        ('Non Profit','Non Profit'),
        ('Self Owned','Self Owned'),
        ('Privately Held','Privately Held'),
        ('Partnership','Partnership')
        ]
    company_id = models.ForeignKey(User,related_name='company_profile',on_delete=models.CASCADE)
    universal_Name = models.CharField(max_length=500)
    compnay_type = models.CharField(max_length=50,choices=company_type_choices)
    industry_type = models.ForeignKey(CandidateModels.IndustryType, related_name="company_industrytype", on_delete=models.CASCADE, null=True)
    company_logo = models.ImageField(verbose_name="company_logo_image")
    speciality = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    country = models.ForeignKey(CandidateModels.Country, related_name="company_country", on_delete=models.CASCADE, null=True)
    state = models.ForeignKey(CandidateModels.State, related_name="company_state", on_delete=models.CASCADE, null=True)
    city = models.ForeignKey(CandidateModels.City, related_name="company_city", on_delete=models.CASCADE, null=True)
    zip_code = models.CharField(max_length=10, null=True)
    contact_no1 = models.CharField(max_length=10)
    contact_no2 = models.CharField(max_length=10)
    founded_year = models.CharField(max_length=5)
    employee_count = models.CharField(max_length=50,choices=employee_count_choices)


class ShortlistedCandidates(models.Model):
    candidate_id = models.ForeignKey(User, related_name="shortlisted_candidate_id", on_delete=models.CASCADE,null=True)
    company_id = models.ForeignKey(User, related_name="shortlisted_company_id", on_delete=models.CASCADE, null=True)

# ############################################    ATS    #################################################


#  ################## -------ADD Candidate------- ##################


class InternalCandidate(models.Model):
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    gender = models.ForeignKey(CandidateModels.Gender, related_name="internal_candidate_gender",
                               on_delete=models.CASCADE, null=True)
    dob = models.CharField(max_length=20, null=True)
    phone_no = models.CharField(max_length=20)
    current_country = models.ForeignKey(CandidateModels.Country, related_name="internal_candidate_current_country",
                                        on_delete=models.CASCADE, null=True)
    current_state = models.ForeignKey(CandidateModels.State, related_name="internal_candidate_current_state",
                                      on_delete=models.CASCADE, null=True)
    current_city = models.ForeignKey(CandidateModels.City, related_name="internal_candidate_current_city",
                                     on_delete=models.CASCADE, null=True)
    current_zip_code = models.CharField(max_length=10, null=True)
    current_street = models.CharField(max_length=50, null=True)
    permanent_country = models.ForeignKey(CandidateModels.Country, related_name="internal_candidate_permanent_country",
                                          on_delete=models.CASCADE, null=True)
    permanent_state = models.ForeignKey(CandidateModels.State, related_name="internal_candidate_permanent_state",
                                        on_delete=models.CASCADE, null=True)
    permanent_city = models.ForeignKey(CandidateModels.City, related_name="internal_candidate_permanent_city",
                                       on_delete=models.CASCADE, null=True)
    permanent_zip_code = models.CharField(max_length=10, null=True)
    permanent_street = models.CharField(max_length=50, null=True)


class InternalCandidateProfessionalDetail(models.Model):
    internal_candidate_id = models.ForeignKey(InternalCandidate, related_name="internal_candidate_professional_detail",
                                              on_delete=models.CASCADE, null=True)
    experience = models.CharField(max_length=20, null=True)
    current_job_title = models.CharField(max_length=30, null=True)
    highest_qualification = models.CharField(max_length=30, null=True)
    expected_salary = models.CharField(max_length=20, null=True)
    current_salary = models.CharField(max_length=20, null=True)
    current_employer = models.CharField(max_length=30, null=True)
    skills = models.CharField(max_length=100, null=True)
    notice_period = models.ForeignKey(CandidateModels.NoticePeriod, related_name="internal_candidate_notice_period",
                                      on_delete=models.CASCADE, null=True)


class InternalCandidateEducation(models.Model):
    internal_candidate_id = models.ForeignKey(InternalCandidate, related_name="internal_candidate_id",
                                              on_delete=models.CASCADE, null=True)
    university_board = models.ForeignKey(CandidateModels.UniversityBoard, related_name="internal_candidate_university",
                                         on_delete=models.CASCADE,
                                         null=True)
    department = models.CharField(max_length=50, null=True)
    degree = models.ForeignKey(CandidateModels.Degree, related_name="internal_candidate_degree",
                               on_delete=models.CASCADE, null=True)
    duration = models.CharField(max_length=50, null=True)
    start_date = models.CharField(max_length=50, null=True)
    end_date = models.CharField(max_length=50, null=True)
    is_pursuing = models.BooleanField(default=False, null=True)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)
    update_at = models.DateTimeField(max_length=200, null=True)


class InternalCandidateExperience(models.Model):
    internal_candidate_id = models.ForeignKey(InternalCandidate, related_name="internal_candidate_experience_id",
                                              on_delete=models.CASCADE,
                                              null=True)
    job_title = models.CharField(max_length=100, null=True)
    company_name = models.CharField(max_length=100, null=True)
    company = models.ForeignKey(CandidateModels.Company, related_name="internal_candidate_company_id",
                                on_delete=models.CASCADE,
                                null=True)
    start_date = models.CharField(max_length=100, null=True)
    end_date = models.CharField(max_length=100, null=True)
    summary = models.CharField(max_length=100, null=True)
    skills = models.ForeignKey(CandidateModels.Skill, related_name="internal_candidate_skill_id",
                               on_delete=models.CASCADE,
                               null=True)
    currently_working = models.BooleanField(default=False, null=True)
    # notice_period = models.ForeignKey(CandidateModels.NoticePeriod, related_name="internal_candidate_exp_notice_period",on_delete=models.CASCADE,
    #                            null=True)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)
    update_at = models.DateTimeField(max_length=200, null=True)


class InternalCandidatePreference(models.Model):
    working_day_choices = [
        ('5day', '5 Days Working'),
        ('6day', '6 Days Working')
    ]
    internal_candidate_id = models.ForeignKey(InternalCandidate, related_name="internal_candidate_preference",
                                              on_delete=models.CASCADE,
                                              null=True)
    country = models.ForeignKey(CandidateModels.Country, related_name="internal_candidate_preference_country",
                                on_delete=models.CASCADE, null=True)
    city = models.ForeignKey(CandidateModels.City, related_name="internal_candidate_preference_city",
                             on_delete=models.CASCADE, null=True)
    company_type = models.ForeignKey(CompanyType, related_name="internal_candidate_preference_company_type",
                                     on_delete=models.CASCADE, null=True)
    working_days = models.CharField(max_length=20, choices=working_day_choices)


class InternalCandidatePortfolio(models.Model):
    internal_candidate_id = models.ForeignKey(InternalCandidate, related_name="internal_candidate_portfolio",
                                              on_delete=models.CASCADE,
                                              null=True)
    project_name = models.CharField(max_length=100)
    project_link = models.CharField(max_length=100)
    attachment = models.FileField(null=True)
    description = HTMLField()


class InternalCandidateSource(models.Model):
    internal_candidate_id = models.ForeignKey(InternalCandidate, related_name="internal_candidate_source",
                                              on_delete=models.CASCADE,
                                              null=True)
    source_id = models.ForeignKey(Source, related_name="internal_candidate_source_id", on_delete=models.CASCADE)
    custom_source_name = models.CharField(max_length=200,null=True)


class InternalCandidateAttachment(models.Model):
    internal_candidate_id = models.ForeignKey(InternalCandidate, related_name="internal_candidate_attachment",
                                              on_delete=models.CASCADE,
                                              null=True)
    file_name = models.CharField(max_length=50)
    file = models.FileField()


class InternalCandidateProfessionalSkill(models.Model):
    internal_candidate_id = models.ForeignKey(InternalCandidate, related_name="internal_candidate_skill_user_id", on_delete=models.CASCADE,
                                     null=True)
    skills = models.ManyToManyField(CandidateModels.Skill, related_name="internal_candidate_skill_user_map", null=True)
    custom_added_skills = models.ManyToManyField(InternalCandidateAddedSkill, related_name="internal_candidate_skill_user_map", null=True)


class InternalCandidateNotes(models.Model):
    internal_candidate_id = models.ForeignKey(InternalCandidate, related_name="internal_candidate_notes_id", on_delete=models.CASCADE,
                                     null=True)
    note = models.TextField()
    time = models.DateTimeField()
    # user_id and department pending

#  ################## -------Job Creation------- ##################


class JobTypes(models.Model):
    name = models.CharField(max_length=100)


class JobStatus(models.Model):
    name = models.CharField(max_length=100)


class JobShift(models.Model):
    name = models.CharField(max_length=100)


class JobCreation(models.Model):
    company_id = models.ForeignKey(User, related_name="job_create_company_id",on_delete=models.CASCADE)
    job_title = models.CharField(max_length=100,null=True)
    job_type = models.ForeignKey(JobTypes,related_name="job_type_id",on_delete=models.CASCADE)
    contact_name = models.CharField(max_length=100, null=True)
    target_date = models.DateField()
    status = models.ForeignKey(JobStatus,related_name="job_status_id",on_delete=models.CASCADE)
    industry_type = models.ForeignKey(CandidateModels.IndustryType,related_name="industry_type_id",on_delete=models.CASCADE, null=True)
    remote_job = models.BooleanField()
    min_salary = models.CharField(max_length=10)
    max_salary = models.CharField(max_length=10)
    experience_year = models.CharField(max_length=10)
    experience_month = models.CharField(max_length=10)
    job_description = HTMLField()
    benefits = HTMLField(max_length=100)
    requirements = HTMLField(max_length=100)
    country = models.ForeignKey(CandidateModels.Country,related_name="job_country",on_delete=models.CASCADE)
    city = models.ForeignKey(CandidateModels.City,related_name="job_city",on_delete=models.CASCADE)
    zip_code = models.CharField(max_length=10)
    job_owner = models.CharField(max_length=100, null=True)
    job_link = models.TextField(null=True)
    is_publish = models.BooleanField(default=False)
    created_by = models.CharField(max_length=10, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)


class CompanyJobShift(models.Model):
    company_id = models.ForeignKey(User, related_name="company_shift", on_delete=models.CASCADE, null=True)
    job_id = models.ForeignKey(JobCreation, related_name="job_id", on_delete=models.CASCADE)
    job_shift_id = models.ForeignKey(JobShift, related_name="job_shift_id", on_delete=models.CASCADE)
    status = models.BooleanField(default=False)

#  ################## -------Template Creation------- ##################


class Stage_list(models.Model):
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=False)


class TemplateCategory(models.Model):
    name = models.CharField(max_length=100)
    stage = models.ForeignKey(Stage_list,on_delete=models.CASCADE)
    company_id = models.ForeignKey(User, related_name='category_company_id', on_delete=models.CASCADE)
    active = models.BooleanField(default=True)


class Template_creation(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=2000)
    stage = models.ForeignKey(Stage_list, related_name="Template_creation_stage",on_delete=models.CASCADE)
    category = models.ForeignKey(TemplateCategory,related_name="Template_creation_category",on_delete=models.CASCADE,null=True)
    company_id = models.ForeignKey(User, related_name='Template_creation_company_id', on_delete=models.CASCADE,null=True)
    active = models.BooleanField(default=True)
    status = models.BooleanField(default=False,null=True)
    created_by = models.CharField(max_length=10,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class JCR(models.Model):
    company_id = models.ForeignKey(User, related_name='jcr_company_id', on_delete=models.CASCADE,null=True)
    stage = models.ForeignKey(Stage_list, related_name="jcr_creation_stage",on_delete=models.CASCADE,null=True)
    category = models.ForeignKey(TemplateCategory, related_name="jcr_creation_category",on_delete=models.CASCADE,null=True)
    template = models.ForeignKey(Template_creation, related_name="jcr_creation_temnplate",on_delete=models.CASCADE,null=True)
    name = models.CharField(max_length=100)
    ratio = models.IntegerField()
    flag = models.CharField(max_length=10, null=True)
    pid = models.ForeignKey('JCR', related_name='jcr_id',on_delete=models.CASCADE,null=True)


class PreRequisites(models.Model):
    company_id = models.ForeignKey(User, related_name='prerequisites_company_id', on_delete=models.CASCADE,null=True)
    stage = models.ForeignKey(Stage_list, related_name="prerequisites_creation_stage",on_delete=models.CASCADE,null=True)
    category = models.ForeignKey(TemplateCategory,related_name="prerequisites_creation_category",on_delete=models.CASCADE,null=True)
    template = models.ForeignKey(Template_creation,related_name="prerequisites_creation_temnplate",on_delete=models.CASCADE,null=True)
    data = HTMLField()
    html_data = HTMLField()


# ############################################### Workflow Creation ###############################################


class Workflows(models.Model):
    company_id = models.ForeignKey(User, related_name='company_workflow', on_delete=models.CASCADE,
                                   null=True)
    name = models.TextField()
    is_configured = models.BooleanField(default=False)
    active = models.BooleanField(default=True)


class WorkflowStages(models.Model):
    company_id = models.ForeignKey(User, related_name='company_workflow_stages', on_delete=models.CASCADE,
                                   null=True)
    stage_name = models.CharField(max_length=100)
    workflow = models.ForeignKey(Workflows, related_name="workflow_id", on_delete=models.CASCADE,null=True)
    stage = models.ForeignKey(Stage_list, related_name="workflow_stage", on_delete=models.CASCADE,null=True)
    category = models.ForeignKey(TemplateCategory, related_name="workflow_category", on_delete=models.CASCADE,null=True)
    template = models.ForeignKey(Template_creation, related_name="workflow_template",on_delete=models.CASCADE, null=True)
    sequence_number = models.IntegerField()


class WorkflowConfiguration(models.Model):
    company_id = models.ForeignKey(User, related_name='company_workflow_configuration', on_delete=models.CASCADE,
                                   null=True)
    workflow_stage = models.ForeignKey(WorkflowStages, related_name="workflow_stage_id", on_delete=models.CASCADE)
    interviewer = models.CharField(max_length=100, null=True)
    is_automation = models.BooleanField(null=True)
    shortlist = models.FloatField(null=True)
    onhold = models.FloatField(null=True)
    reject = models.FloatField(null=True)


class JobWorkflow(models.Model):
    company_id = models.ForeignKey(User, related_name='company_job_workflow', on_delete=models.CASCADE,
                                   null=True)
    job_id = models.ForeignKey(JobCreation, related_name="job_workflow_id", on_delete=models.CASCADE)
    workflow_id = models.ForeignKey(Workflows, related_name="job_workflow_id", on_delete=models.CASCADE)


class AppliedCandidate(models.Model):
    company_id = models.ForeignKey(User, related_name='applied_candidate_company_id', on_delete=models.CASCADE, null=True)
    job_id = models.ForeignKey(JobCreation, related_name="applied_job_id", on_delete=models.CASCADE)
    candidate = models.ForeignKey(User, related_name="applied_candidate_id", on_delete=models.CASCADE)
    create_at = models.DateTimeField(max_length=200, auto_now_add=True)