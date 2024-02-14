#views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from .models import Survey, SurveyQuestion, AnswerChoice, SurveyResponse, SurveyResponseAnswer
from .forms import SurveyForm, SurveyQuestionForm, SurveyResponseForm
from django.views import View
from django.db.models import Count, Case, When, IntegerField, Sum, Avg
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa 
from io import BytesIO
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from allauth.account.views import LoginView as AllauthLoginView

class CustomLoginView(AllauthLoginView):
    def get_success_url(self):
        return '/'
    
class SurveyListView(ListView):
    model = Survey
    template_name = 'survey_list.html'

class SurveyDetailView(View):
    template_name = 'survey_detail.html'

    def get(self, request, *args, **kwargs):
        surveys = Survey.objects.all()
        selected_survey = None
        questions = []
        form = SurveyQuestionForm()

        if 'survey_id' in request.GET:
            selected_survey = get_object_or_404(Survey, pk=request.GET['survey_id'])
            questions = SurveyQuestion.objects.filter(survey=selected_survey)
            form.fields['survey'].initial = selected_survey  # Set the initial value of the hidden field

        context = {
            'surveys': surveys,
            'selected_survey': selected_survey,
            'questions': questions,
            'form': form,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        print(request.POST)
        surveys = Survey.objects.all()
        selected_survey = None
        questions = []
        
        # Move the form definition here
        form = SurveyQuestionForm()

        if 'survey_id' in request.POST:
            selected_survey = get_object_or_404(Survey, pk=request.POST['survey_id'])
            questions = SurveyQuestion.objects.filter(survey=selected_survey)
            request.POST = request.POST.copy()
            request.POST['survey_id'] = selected_survey.id

            form = SurveyQuestionForm(request.POST)
            form.fields['survey'].initial = selected_survey  # Set the initial value of the hidden field

            if form.is_valid():
                form.save()
                messages.success(request, 'successfull.')
                return redirect(request.path_info) 
            # If form is not valid, handle errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
            
        elif 'delete_question_id' in request.POST:
            # Handle deletion of a question
            question_id = request.POST['delete_question_id']
            question_to_delete = get_object_or_404(SurveyQuestion, pk=question_id)
            question_to_delete.delete()
            return redirect(request.path_info)  # Use Django's redirect function
        
        else:
                context = {
                    'surveys': surveys,
                    'selected_survey': selected_survey,
                    'questions': questions,
                    'form': form,
                }
                messages.error(request, 'Failed to update question. Please check the form.')
                return render(request, self.template_name, context)
            
class SurveyQuestionCreateView(CreateView):
    model = SurveyQuestion
    form_class = SurveyQuestionForm
    template_name = 'survey_question_create.html'
    success_url = reverse_lazy('survey_list')

    def form_valid(self, form):
        form.instance.survey = form.cleaned_data['survey']
        return super().form_valid(form)
    

class SurveyCreateView(CreateView):
    model = Survey
    form_class = SurveyForm
    template_name = 'survey_create.html'
    success_url = reverse_lazy('survey_list')  # Using reverse_lazy for the URL

    def form_valid(self, form):
        # Call the parent class's form_valid method to save the form
        return super().form_valid(form)
 
class SurveyUpdateView(UpdateView):
    model = Survey
    fields = ['name', 'description', 'department']
    template_name = 'survey_update.html'

class SurveyDeleteView(DeleteView):
    model = Survey
    success_url = '/surveys/manage'  # URL to redirect to after successful deletion
    template_name = 'survey_delete.html'
    
class SurveyQuestionEditView(UpdateView):
    model = SurveyQuestion
    form_class = SurveyQuestionForm
    template_name = 'survey_question_edit.html'
    success_url = reverse_lazy('survey_detail')


def survey_selection(request):
    surveys = Survey.objects.all()
    return render(request, 'survey_selection.html', {'surveys': surveys})

def survey_list(request, survey_id=None):
    if request.method == 'POST':
        print(request.POST)
        survey_id = request.POST.get('survey')
        print(f"POST request - survey_id: {survey_id}")

        # Get the selected survey
        survey = Survey.objects.get(pk=survey_id)
        questions = survey.surveyquestion_set.all()
        form = SurveyResponseForm(request.POST, questions=questions)

        if form.is_valid():
            # Save the survey response
            response = form.save(commit=False)
            response.survey = survey
            response.ip_address = request.META.get('REMOTE_ADDR')
            response.save()
            
            # Set remarks for the response
            response.remarks = form.cleaned_data.get('remarks')
            response.save()

            # Process each question and its answer
            for question in questions:
                answer_choice_value = form.cleaned_data.get(f'question_{question.id}')
                try:
                    answer_choice = AnswerChoice.objects.get(choice_value=answer_choice_value, question=question)
                except AnswerChoice.DoesNotExist:
                    print(f"AnswerChoice does not exist for question {question.id}.")

                    # Check if answer_choice_value is not None before creating the AnswerChoice
                    if answer_choice_value is not None:
                        answer_choice = AnswerChoice.objects.create(choice_value=answer_choice_value, question=question)
                    else:
                        print("Invalid answer_choice_value. Skipping the creation of AnswerChoice.")
                        continue

                SurveyResponseAnswer.objects.create(response=response, question=question, answer=answer_choice)

            return redirect('thank_you_page')  # Redirect after processing the form

    elif survey_id is None:
        print("Redirecting to survey_selection")
        return redirect('survey_selection')

    # Render the page with the selected survey
    survey = Survey.objects.get(pk=survey_id)
    questions = survey.surveyquestion_set.all()
    form = SurveyResponseForm(questions=questions)
    return render(request, 'survey_list.html', {'survey': survey, 'questions': questions, 'form': form})

def thank_you_page(request):
    return render(request, 'thank_you_page.html') 

class SurveyManagementView(View):
    template_name = 'survey_create.html'

    @login_required
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def get(self, request, *args, **kwargs):
        surveys = Survey.objects.all()
        form = SurveyForm()
        context = {
            'surveys': surveys,
            'form': form,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        surveys = Survey.objects.all()
        form = SurveyForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'Survey created successfully.')
            return redirect(request.path_info)

        context = {
            'surveys': surveys,
            'form': form,
        }
        return render(request, self.template_name, context)

class SurveyEditView(UpdateView):
    model = Survey
    form_class = SurveyForm
    template_name = 'survey_edit.html'
    success_url = reverse_lazy('survey_management')
    

def survey_statistics(request, survey_id=0):
    # print(f"Survey ID: {survey_id}")

    try:
        survey = Survey.objects.get(pk=survey_id)
    except Survey.DoesNotExist:
        messages.warning(request, 'Invalid survey ID. Please select a valid survey.')
        
        # Get the URL with preserved query parameters
        redirect_url = reverse('survey_selection_with_id') + '?' + request.GET.urlencode()
        
        return redirect(redirect_url)

    responses = survey.get_responses()
    
    # Initialize start_date and end_date outside the try-except block
    start_date = None
    end_date = None

    # Filter responses based on the selected date range
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')

    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            responses = responses.filter(timestamp__gte=timezone.make_aware(datetime.combine(start_date, datetime.min.time())))

        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            responses = responses.filter(timestamp__lte=timezone.make_aware(datetime.combine(end_date, datetime.max.time())))
    except ValueError:
        # Handle invalid date format gracefully, you may want to provide a message to the user
        messages.error(request, 'Invalid date format. Please use YYYY-MM-DD format.')
        return redirect('survey_statistics', survey_id=survey_id)
    
   # Calculate star counts for each question
    star_counts_annotations = {
        f'star_counts_{i}': Count(
            Case(
                When(
                    surveyresponseanswer__answer__choice_value=i,
                    surveyresponseanswer__response__survey=survey,
                    surveyresponseanswer__response__timestamp__date__range=(start_date, end_date),
                    then=1
                ),
                output_field=IntegerField()
            )
        ) for i in range(1, 6)
    }

    question_counts = SurveyQuestion.objects.filter(survey=survey).annotate(**star_counts_annotations)
    
    # Calculate average rating for each question
    question_averages = SurveyQuestion.objects.filter(survey=survey).annotate(avg_rating=Avg('surveyresponseanswer__answer__choice_value'))


    # Fetch remarks directly from SurveyResponse model with annotations
    remarks = SurveyResponseAnswer.objects.filter(
        response__survey=survey,
        response__timestamp__date__range=(start_date, end_date)
    ).exclude(response__remarks__exact='').order_by('response__timestamp')
    
    # Extract unique remarks and their counts
    unique_remarks = []

    for response in remarks:
        response_id = response.response.id
        remark = response.response.remarks
        timestamp = response.response.timestamp

        existing_remark = next((item for item in unique_remarks if item['id'] == response_id), None)

        if existing_remark:
            existing_remark['count'] += 1
            existing_remark['timestamps'].append(timestamp)
        else:
            unique_remarks.append({
                'id': response_id,
                'remark': remark,
                'count': 1,
                'timestamps': [timestamp],
            })
    # Sort unique remarks based on the first timestamp if it exists
    unique_remarks.sort(key=lambda x: x.get('timestamps', [None])[0] if x.get('timestamps') and x.get('timestamps')[0] is not None else float('inf'))
    
    # Paginate unique_remarks
    remarks_paginator = Paginator(unique_remarks, 5)
    page = request.GET.get('page', 1)

    try:
        remarks_page = remarks_paginator.page(page)
    except PageNotAnInteger:
        remarks_page = remarks_paginator.page(1)
    except EmptyPage:
        remarks_page = remarks_paginator.page(remarks_paginator.num_pages)
        
    print(f"Page Info: {remarks_page.has_previous()}, {remarks_page.has_next()}, {remarks_page.number}, {remarks_page.paginator.num_pages}")

    context = {
        'survey': survey,
        'responses': responses,
        'remarks_page': remarks_page,
        'total_responses': responses.count(),
        'question_counts': question_counts,
        'question_averages': question_averages,
        'start_date': start_date_str,  # Pass start_date to the context
        'end_date': end_date_str,  # Pass end_date to the context
        'unique_remarks': unique_remarks,
    }
    
    # print(f"Total Remarks: {remarks.count()}")
    # print(f"Remarks per Page: {remarks_paginator.per_page}")
    # print("Remarks QuerySet:", remarks)
    # print(f"Start Date: {start_date_str}, End Date: {end_date_str}")

    return render(request, 'survey_statistics.html', context)

def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

def survey_pdf_report(request, selected_survey_id):
    survey = get_object_or_404(Survey, pk=selected_survey_id)

    # Get start_date and end_date from the request parameters
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')
    all_responses = None
    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = None

        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
            end_date = end_date.replace(microsecond=999999)
        else:
            end_date = None

    
            # Reuse filtering logic from survey_statistics
            # all_responses = SurveyResponse.get_survey_responses(start_date, end_date)   

        
            # Explicitly filter responses based on start_date and end_date
            if start_date:
                all_responses = all_responses.filter(timestamp__gte=start_date)

            if end_date:
                all_responses = all_responses.filter(timestamp__lte=end_date)
        
        all_responses = SurveyResponse.objects.filter(
        survey=survey,
        timestamp__gte=start_date,
        timestamp__lte=end_date
        )
        
             
        print(all_responses) 
           
    except ValueError as e:
        print(f'Error parsing date: {e}')
        # Print the generated SQL query for debugging (if all_responses is not None)
        if all_responses is not None:
            print(all_responses.query)
        # Handle invalid date format gracefully, you may want to provide a message to the user
        messages.error(request, 'Invalid date format. Please use YYYY-MM-DD format.')
        return redirect('survey_pdf_report_with_id', selected_survey_id=selected_survey_id)
    
    # Check if all_responses is not None before calculating total_responses
    if all_responses is not None:
        # Calculate total_responses using the explicitly filtered responses
        total_responses = all_responses.count()
        # Print the total_responses for debugging
    else:
        total_responses = 0
    
    print(f'Total Responses: {total_responses}')
    print(f'Start Date: {start_date}')
    print(f'End Date: {end_date}')
    print(f'Start Date (Formatted): {start_date.strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'End Date (Formatted): {end_date.strftime("%Y-%m-%d %H:%M:%S")}')

    question_counts = (
        SurveyQuestion.objects.filter(survey=survey)
        .annotate(
            star_counts_1=Sum(
                Case(
                    When(
                        surveyresponseanswer__answer__choice_value=1,
                        surveyresponseanswer__response__timestamp__gte=start_date,
                        surveyresponseanswer__response__timestamp__lte=end_date,
                        then=1
                    ),
                    default=0,
                    output_field=IntegerField()
                )
            ),
            star_counts_2=Sum(
                Case(
                    When(
                        surveyresponseanswer__answer__choice_value=2,
                        surveyresponseanswer__response__timestamp__gte=start_date,
                        surveyresponseanswer__response__timestamp__lte=end_date,
                        then=1
                    ),
                    default=0,
                    output_field=IntegerField()
                )
            ),
            star_counts_3=Sum(
                Case(
                    When(
                        surveyresponseanswer__answer__choice_value=3,
                        surveyresponseanswer__response__timestamp__gte=start_date,
                        surveyresponseanswer__response__timestamp__lte=end_date,
                        then=1
                    ),
                    default=0,
                    output_field=IntegerField()
                )
            ),
            star_counts_4=Sum(
                Case(
                    When(
                        surveyresponseanswer__answer__choice_value=4,
                        surveyresponseanswer__response__timestamp__gte=start_date,
                        surveyresponseanswer__response__timestamp__lte=end_date,
                        then=1
                    ),
                    default=0,
                    output_field=IntegerField()
                )
            ),
            star_counts_5=Sum(
                Case(
                    When(
                        surveyresponseanswer__answer__choice_value=5,
                        surveyresponseanswer__response__timestamp__gte=start_date,
                        surveyresponseanswer__response__timestamp__lte=end_date,
                        then=1
                    ),
                    default=0,
                    output_field=IntegerField()
                )
            ),
        )
    )


    # Other data you want to include in the PDF context
    context = {
        'survey': survey,
        'responses': all_responses,
        'total_responses': total_responses,
        'question_counts': question_counts,
        'start_date': start_date,  
        'end_date': end_date,
    }

    pdf = render_to_pdf('survey_pdf_template.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f'{survey.name}_report.pdf'
        response['Content-Disposition'] = f'filename="{filename}"'

        # Check if 'view' parameter is provided in the URL
        if request.GET.get('view') == 'true':
            response['Content-Disposition'] = 'inline;' + response['Content-Disposition']

        return response
    return HttpResponse('Error generating PDF', status=500)

