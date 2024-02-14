# admin.py
from django.contrib import admin
from .models import Department, Survey, SurveyQuestion, AnswerChoice, SurveyResponse, SurveyResponseAnswer

admin.site.register(Department)
admin.site.register(Survey)
admin.site.register(SurveyQuestion)
admin.site.register(AnswerChoice)
admin.site.register(SurveyResponse)
admin.site.register(SurveyResponseAnswer)
