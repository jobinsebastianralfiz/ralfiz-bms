"""The Academy at /academy/: the student portal, plus owner pages under manage/."""
from django.urls import path

from . import manage_views as m
from . import views as v

app_name = 'academy'

urlpatterns = [
    path('login/', v.academy_login, name='login'),
    path('logout/', v.academy_logout, name='logout'),

    path('', v.home, name='home'),
    path('profile/', v.profile, name='profile'),
    path('courses/', v.courses, name='courses'),
    path('assessments/', v.assessments, name='assessments'),
    path('certificates/', v.certificates, name='certificates'),
    path('tracks/<str:track_id>/', v.track_detail, name='track'),
    path('tracks/<str:track_id>/data.zip', v.track_data_zip, name='track_data_zip'),
    path('tracks/<str:track_id>/test/', v.test_start, name='test_start'),
    path('lessons/<str:lesson_id>/', v.lesson_detail, name='lesson'),
    path('lessons/<str:lesson_id>/files.zip', v.lesson_zip, name='lesson_zip'),
    path('files/<path:file_id>', v.file_download, name='file'),
    path('tests/<uuid:attempt_id>/', v.test_take, name='test_take'),
    path('tests/<uuid:attempt_id>/submit/', v.test_submit, name='test_submit'),
    path('tests/<uuid:attempt_id>/result/', v.test_result, name='test_result'),

    # JSON, session auth + CSRF
    path('api/lessons/<str:lesson_id>/lab/', v.api_lab, name='api_lab'),
    path('api/questions/<int:question_id>/answer/', v.api_answer, name='api_answer'),
    path('api/tests/<uuid:attempt_id>/', v.api_test_save, name='api_test_save'),

    # Owner pages (BMS layout)
    path('manage/', m.manage_home, name='manage_home'),
    path('manage/students/', m.manage_students, name='manage_students'),
    path('manage/students/new/', m.manage_student_new, name='manage_student_new'),
    path('manage/students/<uuid:pk>/', m.manage_student_detail, name='manage_student_detail'),
    path('manage/students/<uuid:pk>/edit/', m.manage_student_edit, name='manage_student_edit'),
    path('manage/students/<uuid:pk>/password/', m.manage_student_password,
         name='manage_student_password'),
    path('manage/students/<uuid:pk>/unlock/', m.manage_student_unlock,
         name='manage_student_unlock'),
    path('manage/students/<uuid:pk>/status/', m.manage_student_status,
         name='manage_student_status'),
    path('manage/progress/', m.manage_progress, name='manage_progress'),
]
