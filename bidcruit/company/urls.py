from django.urls import path
from django.conf.urls import url
from . import views
app_name = 'company'

urlpatterns = [
    path('home/', views.index, name='home'),
    path('signup', views.ragister, name="signup"),
    url(r'^verify_otp/$', views.verify_otp, name='verify_otp'),
    path('candidate_hire', views.candidate_hire, name='candidate_hire'),
    path('check_email_is_valid', views.check_email_is_valid, name="check_email_is_valid"),
    path('company_login_direct', views.company_login_direct, name="company_login_direct"),
    path('candidate_list_view', views.candidate_list_view, name="candidate_list_view"),
    path('user_login_email_popup', views.user_login_email_popup, name="user_login_email_popup"),
    path('user_login_password_popup', views.user_login_password_popup, name="user_login_password_popup"),
    path('user_login_verify_otp_popup', views.user_login_verify_otp_popup, name="user_login_verify_otp_popup"),
    path('candidate_preference_check', views.candidate_preference_check, name="candidate_preference_check"),

    # candidate search urls
    path('search', views.search, name="search"),
    path('search_result', views.search_result, name="search_result"),
    path('advanced_search', views.advanced_search, name="advanced_search"),
    path('get_page_no', views.get_page_no, name="get_page_no"),
    path('get_cities/',views.get_cities,name='get_cities'),
    path('get_skills/',views.get_skills,name='get_skills'),
    path('get_degrees/',views.get_degrees,name='get_degrees'),
    path('add_edit_profile/',views.add_edit_profile,name='add_edit_profile'),
    path('file_request',views.file_request,name="file_request"),
    # path('demo',views.demo,name='demo'),
    path('candidate_detail/<str:url>',views.candidate_detail,name='candidate_detail'),
    path('hire_request/', views.doc_request, name="hire_request"),
    path('document_request/',views.document_request,name='document_request'),
    path('company_profile/',views.company_profile,name='company_profile'),
    path('shortlist/',views.shortlist_candidate,name='shortlist_candidate'),

    # ############################## ATS ####################################

    #   Candidates
    path('all_countries/', views.all_countries, name='all_countries'),
    path('all_states/<str:country_id>', views.all_states, name='all_states'),
    path('all_cities/<str:state_id>', views.all_cities, name='all_cities'),
    path('add_candidate/', views.add_candidate, name='add_candidate'),
    path('all_candidates/', views.all_candidates, name='all_candidates'),
    path('view_candidate/<str:candidate_id>', views.view_candidate, name='view_candidate'),
    path('internal_candidate_notes/', views.internal_candidate_notes, name='internal_candidate_notes'),

    #  Job Creation
    path('job_creation/', views.job_creation, name='job_creation'),
    path('job_openings_table/', views.job_openings_table, name='job_openings_table'),
    path('job_openings_requests/', views.job_openings_requests, name='job_openings_requests'),

    # Template Creation
    path('template_listing/', views.template_listing, name='template_listing'),
    path('add_category/', views.add_category, name='add_category'),
    path('delete_category/', views.delete_category, name='delete_category'),
    path('update_category/', views.update_category, name='update_category'),
    path('get_category/', views.get_category, name='get_category'),
    # path('create_template/', views.create_template, name='create_template'),
    path('edit_template/', views.edit_template, name='edit_template'),
    path('delete_template/', views.delete_template, name='delete_template'),

    # Pre requisites
    path("pre_requisites/", views.pre_requisites, name="pre_requisites"),
    path("save_pre_requisites/", views.save_pre_requisites, name="save_pre_requisites"),

    # JCR
    path('jcr/', views.jcr, name='jcr'),
    path('insert_jcr/', views.insert_jcr, name='insert_jcr'),
    path('remove_jcr/', views.remove_jcr, name='remove_jcr'),
    path('remove_sub_jcr/', views.remove_sub_jcr, name='remove_sub_jcr'),
    path('jcr_preview/', views.jcr_preview, name='jcr_preview'),

    #  Workflow Management
    path("workflow_list/", views.workflow_list, name="workflow_list"),
    path("create_workflow/", views.create_workflow, name="create_workflow"),
    path("edit_workflow/<int:id>", views.edit_workflow, name="edit_workflow"),
    path("workflow_configuration/", views.workflow_configuration, name="workflow_configuration"),
    path("get_workflow_data/", views.get_workflow_data, name="get_workflow_data"),
    path("workflow_selection/<int:id>", views.workflow_selection, name="workflow_selection"),

    path("created_job_view/<int:id>", views.created_job_view, name="created_job_view"),

]
