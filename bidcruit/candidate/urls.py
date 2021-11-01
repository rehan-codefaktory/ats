from django.urls import path
from django.conf.urls import url
from . import views
app_name= 'candidate'

urlpatterns = [
    path('home/', views.index, name='home'),
    path('signup', views.ragister, name="signup"),
    path('signup/<str:referral>', views.referral_signup, name="referral_signup"),
    url(r'^country/(?P<id>\d+)/$', views.state_view),
    url(r'^state/(?P<id>\d+)/$', views.city_view),
    url(r'^cities_by_country/(?P<id>\d+)/$', views.cities_by_country),
    url(r'^preference_cities_by_country/(?P<id>\d+)/$', views.preference_cities_by_country),
    path('candidate_profile', views.candidate_profile, name="candidate_profile"),
    path('check_email_is_valid', views.check_email_is_valid, name="check_email_is_valid"),
    path('/<str:url>/', views.timeline, name="timeline"),
   
    # charts
    path('statistics/', views.statistics_view, name="candidate_statistics"),
    path('chart/filter-options/', views.get_filter_options, name='chart-filter-options'),
    path('chart/payment-method/', views.payment_method_chart, name='chart-payment-method'),
    path('chart/job-experience/', views.job_exp_Chart, name='chart-job-experience'),
    path('chart/edu-percentage/', views.edu_per_chart, name='chart-edu-percentage'),
    path('charts', views.charts, name='charts'),


    # Wizard
    path('upload_resume/personal_detail_temp', views.personal_detail_temp, name="personal_detail_temp"),
    path('upload_resume/education_temp', views.education_temp, name="education_temp"),
    path('upload_resume/work_experience_temp', views.work_experience_temp, name="work_experience_temp"),
    path('upload_resume/skill_temp', views.skill_temp, name="skill_temp"),
    path('upload_resume/other_temp', views.other_temp, name="other_temp"),
    path('upload_resume/remove_record', views.remove_record, name="remove_record"),
    path('upload_resume/save_resume', views.save_resume, name="save_resume"),
    path('create_resume_pass/', views.create_resume_pass, name="create_resume_pass"),
    path('update_resume_pass/', views.update_resume_pass, name="update_resume_pass"),
    path('update_share_url/',views.update_share_url,name="update_share_url"),
    path('check_sharing_url_is_valid',views.check_sharing_url_is_valid,name="check_sharing_url_is_valid"),

    # Dashboard
    path('upload_resume_add/<str:url>', views.upload_resume, name='upload_resume_add'),
    path('add_profile/',views.add_profile,name='add_profile'),
    path('add_profile_detail/<str:url>',views.add_profile_detail,name='add_profile_detail'),
    path('toggle_profile/', views.toggle_profile, name="toggle_profile"),
    path('toggle_field_state/', views.toggle_field_state, name="toggle_field_state"),
    path('edit_profile/<str:profile_id>', views.edit_profile, name="edit_profile"),
    path('job_preference/', views.candidate_job_preference, name="job_preference"),

    #  Request
    path('hire_request/', views.hire_request, name="hire_request"),
    path('accept_request/<str:profile_id>/<int:company_id>/<str:hire_id>', views.accept_request, name="accept_request"),
    path('reject_request/<str:profile_id>/<int:company_id>/<str:hire_id>', views.reject_request, name="reject_request"),
    path('data_accept_request/<str:profile_id>/<int:company_id>/<str:data_id>/', views.data_accept_request, name="data_accept_request"),
    path('data_reject_request/<str:profile_id>/<int:company_id>/<str:data_id>/', views.data_reject_request, name="data_reject_request"),

    path('file_download',views.file_download,name="file_download"),
    path('look_for_job_check/', views.look_for_job_check, name="look_for_job_check"),
    path('delete_exp_document', views.delete_exp_doc, name="delete_exp_doc"),
    path('candidate_resume_update/', views.candidate_resume_update, name="candidate_resume_update"),

    # Profile update
    # path('edit_profile/<str:profile_id>', views.edit_profile, name="edit_profile"),
    path('download_folder/<int:candidate_id>/',views.download_folder,name="download_folder"),
    path('test_redirect/', views.test_redirect, name="test_redirect"),


    #apply job
    path('add_apply_candidate/', views.add_apply_candidate, name='add_apply_candidate'),
    path('applied_job_list/', views.applied_job_list, name='applied_job_list'),
    path('candidate_jcr/<int:id>/<int:job_id>', views.candidate_jcr, name='candidate_jcr'),
    path('applied_job_detail/<int:id>', views.applied_job_detail, name='applied_job_detail'),
    path("prequisites_view/<int:id>/<int:job_id>", views.prequisites_view, name="prequisites_view"),

]

