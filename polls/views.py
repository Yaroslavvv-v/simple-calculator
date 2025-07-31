from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from .models import Question, Choice, Voter
from django.views.decorators.csrf import csrf_exempt
import uuid
import json

# Helper to get MAC address (simplified for demonstration)
def get_mac_address(request):
    # In a real application, you'd use a more robust method to get a unique identifier
    # For now, we'll use a session-based UUID or a simplified IP-based approach
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key

def index(request):
    latest_question_list = Question.objects.order_by('-pub_date')[:5]
    data = [{
        'id': question.id,
        'question_text': question.question_text,
        'pub_date': question.pub_date.isoformat(),
        'end_date': question.end_date.isoformat() if question.end_date else None
    } for question in latest_question_list]
    return JsonResponse(data, safe=False)

def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    choices = [{
        'id': choice.id,
        'choice_text': choice.choice_text,
        'votes': choice.votes
    } for choice in question.choice_set.all()]
    data = {
        'id': question.id,
        'question_text': question.question_text,
        'pub_date': question.pub_date.isoformat(),
        'end_date': question.end_date.isoformat() if question.end_date else None,
        'choices': choices
    }
    return JsonResponse(data)

def results(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    choices = [{
        'id': choice.id,
        'choice_text': choice.choice_text,
        'votes': choice.votes
    } for choice in question.choice_set.all()]
    data = {
        'id': question.id,
        'question_text': question.question_text,
        'pub_date': question.pub_date.isoformat(),
        'end_date': question.end_date.isoformat() if question.end_date else None,
        'choices': choices
    }
    return JsonResponse(data)

@csrf_exempt
def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        data = json.loads(request.body)
        selected_choice = question.choice_set.get(pk=data['choice'])
    except (KeyError, Choice.DoesNotExist):
        return JsonResponse({'error': "You didn't select a choice."}, status=400)
    else:
        mac_address = get_mac_address(request)
        if Voter.objects.filter(question=question, mac_address=mac_address).exists():
            return JsonResponse({'error': "You have already voted on this poll."}, status=403)
        
        if question.end_date and timezone.now() > question.end_date:
            return JsonResponse({'error': "Voting for this poll has ended."}, status=403)

        selected_choice.votes += 1
        selected_choice.save()
        Voter.objects.create(question=question, mac_address=mac_address)
        return JsonResponse({'message': 'Vote recorded successfully.'}, status=200)

@csrf_exempt
def create_poll(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            question_text = data['question_text']
            choices_text = data.get('choices', [])
            end_date_str = data.get('end_date')
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({'error': 'Invalid JSON data or missing fields.'}, status=400)

        question = Question.objects.create(question_text=question_text, pub_date=timezone.now())
        if end_date_str:
            try:
                question.end_date = timezone.datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
                question.save()
            except ValueError:
                return JsonResponse({'error': 'Invalid end_date format. Use YYYY-MM-DDTHH:MM.'}, status=400)

        for choice_text in choices_text:
            if choice_text.strip():
                question.choice_set.create(choice_text=choice_text)
        
        return JsonResponse({'id': question.id, 'message': 'Poll created successfully.'}, status=201)
    return JsonResponse({'error': 'Only POST requests are allowed.'}, status=405)
