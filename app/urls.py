# urls.py
from django.urls import path
from .views import (
    SurveyListView,
    SurveyDetailView,
    SurveyCreateView,
    SurveyDeleteView,
    SurveyQuestionCreateView,
    SurveyQuestionEditView, 
    survey_selection, 
    survey_list, 
    thank_you_page,
    SurveyManagementView, 
    SurveyEditView,
    survey_statistics,
    survey_pdf_report,
    
       
)

urlpatterns = [
    path('surveys/list/', SurveyListView.as_view(), name='survey_list_view'),
    path('surveys/', SurveyDetailView.as_view(), name='survey_detail'),
    path('surveys/<int:pk>/', SurveyDetailView.as_view(), name='survey_detail_with_pk'),
    path('surveys/create/', SurveyCreateView.as_view(), name='survey_create'),
    path('surveys/<int:pk>/delete/', SurveyDeleteView.as_view(), name='survey_delete'),
    path('surveys/add-question/', SurveyQuestionCreateView.as_view(), name='survey_question_create'),
    path('surveys/edit-question/<int:pk>/', SurveyQuestionEditView.as_view(), name='survey_question_edit'),
    path('survey/selection/', survey_selection, name='survey_selection'),
    path('survey/list/<int:survey_id>/', survey_list, name='survey_list'),
    path('thank-you/', thank_you_page, name='thank_you_page'),
    path('surveys/manage/', SurveyManagementView.as_view(), name='survey_management'),
    path('surveys/edit/<int:pk>/', SurveyEditView.as_view(), name='survey_edit'),
    path('surveys/statistics/<int:survey_id>/', survey_statistics, name='survey_statistics_with_id'),
    path('surveys/pdf-report/<int:selected_survey_id>/', survey_pdf_report, name='survey_pdf_report_with_id'),
]
