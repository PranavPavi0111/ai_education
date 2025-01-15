from django.contrib import admin
from .import views
from django.urls import path,include,re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from  rest_framework.routers import DefaultRouter
from .views import *

schema_view = get_schema_view(
    openapi.Info(
        title="Educational Management APP API",
        default_version="v1",
        description="API documentation for the Educational Management APP.",
        terms_of_service="https://www.google.com/policies/terms/",
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)


router = DefaultRouter()
router.register(r"parent_register",ParentRegistrationView,basename='parent_register')
router.register(r"parent_add_student",ParentAddStudentView,basename='parent_add_student')
# router.register(r'quizzes', QuizView, basename='quiz')
router.register(r'assignments', AssignmentView, basename='assignment')
router.register(r'remove_student',RemoveStudentView,basename='remove_student')
# router.register(r'participations', QuizParticipationView, basename='participation')
# router.register(r'results', ResultView, basename='result')
# router.register(r'quiz-results', QuizResultViewSet, basename='quizresult')
# router.register(r'performance-reports', PerformanceReportView, basename='performance-report')



urlpatterns = [
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "redoc/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),
    
    path('',include(router.urls)),
    path('login/', LoginView.as_view(), name='login'),
    path('parent_view_child/',ParentViewChild.as_view({'get':'list'}),name='parent_view_child'),
    path('update_student_profile/',UpdateStudentProfileView.as_view(),name='update_student_profile'),
    path('search-image/', ImageSearchView.as_view(), name='search-image'),
    path('check-api-key/', views.check_api_key, name='check_api_key'),
    path('quiz/', views.quiz_view, name='quiz'),
    path('check_answers/', views.check_answers_view, name='check_answers'),
    path('feedback/', views.feedback_view, name='feedback'),
    path('student_view_profile/',StudentViewProfile.as_view({'get':'list'}),name='student_view_profile'),
    path('quiz/<int:quiz_id>/response/', store_response_view, name='store_response'),
    path('student/<int:student_id>/quizzes/', student_assigned_quizzes, name='student_assigned_quizzes'),
    path('student/<int:student_id>/quiz_responses/', student_quiz_responses, name='student_quiz_responses'),
]