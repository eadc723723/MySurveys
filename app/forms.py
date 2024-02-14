# forms.py
from django import forms
from .models import Survey, Department, SurveyQuestion, AnswerChoice, SurveyResponse

class SurveyForm(forms.ModelForm):
    department = forms.ModelChoiceField(queryset=Department.objects.all(), empty_label=None, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Survey
        fields = ['name', 'description', 'department']
        
class SurveyQuestionForm(forms.ModelForm):
    survey = forms.ModelChoiceField(queryset=Survey.objects.all(), widget=forms.HiddenInput(), required=False)

    class Meta:
        model = SurveyQuestion
        fields = ['survey', 'question_text']

    def clean(self):
        cleaned_data = super().clean()
        survey = cleaned_data.get('survey')
        question_text = cleaned_data.get('question_text')

        # Validate and return the selected survey if it exists
        if not survey and not question_text:
            raise forms.ValidationError("Survey or question text is required.")

        # Check if the provided survey is in the queryset
        queryset = self.fields['survey'].queryset
        if survey not in queryset:
            raise forms.ValidationError("Invalid survey selected.")

        return cleaned_data

class SurveyResponseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        questions = kwargs.pop('questions', None)
        super().__init__(*args, **kwargs)

        for question in questions:
            field_name = f'question_{question.id}'
            self.fields[field_name] = forms.ChoiceField(
                choices=[(1, '⭐'), (2, '⭐⭐'), (3, '⭐⭐⭐'), (4, '⭐⭐⭐⭐'), (5, '⭐⭐⭐⭐⭐')],
                widget=forms.Select(attrs={'class': 'star-rating'}),
                label=question.question_text,
                required=True,
                
            )
            

        # Handle the remarks field outside the loop
        self.fields['remarks'] = forms.CharField(
            widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            required=False
        )

    class Meta:
        model = SurveyResponse
        fields = ['remarks']







