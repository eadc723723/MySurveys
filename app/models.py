# models.py
from django.db import models
from django.utils import timezone


class Department(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'department'

class Survey(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    
    def get_responses(self):
        return SurveyResponse.objects.filter(survey=self)
    
    def __str__(self):
        return self.name
    class Meta:

        db_table = 'survey'

class SurveyQuestion(models.Model):
    question_text = models.TextField()
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.question_text
    class Meta:

        db_table = 'survey_question'

class AnswerChoice(models.Model):
    choice_value = models.IntegerField(choices=[(1, '⭐'), (2, '⭐⭐'), (3, '⭐⭐⭐'), (4, '⭐⭐⭐⭐'), (5, '⭐⭐⭐⭐⭐')])
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE)

    class Meta:
        db_table = 'answer_choice'
    
class SurveyResponse(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(default=timezone.now)
    remarks = models.TextField(blank=True, null=True)
    
    def get_survey_responses(self, start_date=None, end_date=None):
        responses = SurveyResponse.objects.filter(survey=self)

        if start_date:
            responses = responses.filter(timestamp__gte=start_date)

        if end_date:
            responses = responses.filter(timestamp__lte=end_date)

        return responses
    
    class Meta:

        db_table = 'survey_response'

class SurveyResponseAnswer(models.Model):
    response = models.ForeignKey(SurveyResponse, on_delete=models.CASCADE)
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE)
    answer = models.ForeignKey(AnswerChoice, on_delete=models.CASCADE)
    class Meta:

        db_table = 'survey_response_answer'