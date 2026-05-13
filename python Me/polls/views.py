"""
views.py - All view functions for the polls application.

Each view is responsible for exactly ONE URL/action (Single Responsibility Principle).
Forms are imported from forms.py.
Helper logic is imported from utils.py.
"""

import json
import csv

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone

from .models import Poll, Question, Choice, Response, Answer
from .forms import (
    UserRegistrationForm,
    PollPasswordForm,
    ResponseFilterForm,
)
from .utils import (
    get_client_ip,
    check_poll_access,
    check_poll_password,
    unlock_poll_in_session,
    compute_poll_statistics,
    build_csv_rows,
)


# ═══════════════════════════════════════════════════════
# AUTHENTICATION VIEWS
# ═══════════════════════════════════════════════════════

def register_view(request):
    """
    Handles new user registration.
    GET  → shows the registration form.
    POST → validates and creates the new user account.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Bienvenue, {user.username} ! Votre compte a été créé avec succès.")
            return redirect('dashboard')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = UserRegistrationForm()

    return render(request, 'registration/register.html', {'form': form})


# ═══════════════════════════════════════════════════════
# PUBLIC / HOME VIEWS
# ═══════════════════════════════════════════════════════

def home_view(request):
    """
    Public homepage showing active polls and reusable templates.
    """
    polls = Poll.objects.filter(
        is_active=True, is_template=False
    ).select_related('creator').order_by('-created_at')

    templates = Poll.objects.filter(
        is_template=True, is_active=True
    ).select_related('creator')

    return render(request, 'polls/home.html', {
        'polls': polls,
        'templates': templates,
    })


# ═══════════════════════════════════════════════════════
# CREATOR DASHBOARD VIEWS
# ═══════════════════════════════════════════════════════

@login_required
def dashboard_view(request):
    """
    Displays the authenticated user's dashboard with all their polls
    and summary statistics.
    """
    if request.user.is_superuser:
        polls = Poll.objects.all().order_by('-created_at')
    else:
        polls = Poll.objects.filter(
            creator=request.user
        ).order_by('-created_at')

    # Dashboard summary stats
    total_polls = polls.count()
    total_responses = sum(p.responses.count() for p in polls)
    active_polls = polls.filter(is_active=True).count()

    return render(request, 'polls/dashboard.html', {
        'polls': polls,
        'total_polls': total_polls,
        'total_responses': total_responses,
        'active_polls': active_polls,
    })


# ═══════════════════════════════════════════════════════
# POLL CREATION VIEW
# ═══════════════════════════════════════════════════════

@login_required
def create_poll(request):
    """
    Handles poll creation via an interactive JSON-based interface.

    GET  → renders the creation interface (optionally pre-filled from a template).
    POST → receives JSON payload and creates Poll + Questions + Choices in the DB.
    """
    if request.method == 'POST':
        return _handle_create_poll_post(request)

    # GET: check if duplicating from a template
    template_id = request.GET.get('from_template')
    template_data = _load_template_data(template_id) if template_id else None

    return render(request, 'polls/create_poll.html', {
        'template_data': json.dumps(template_data) if template_data else None
    })


def _handle_create_poll_post(request):
    """
    Private helper: processes the POST request to create a poll from JSON data.
    Returns a JsonResponse with the new poll ID or an error message.
    """
    try:
        data = json.loads(request.body)

        # 1. Create the Poll object
        poll = Poll.objects.create(
            creator=request.user,
            title=data.get('title', 'Sans titre'),
            description=data.get('description', ''),
            is_anonymous=data.get('is_anonymous', False),
            password=data.get('password', '') or None,
            expires_at=data.get('expires_at') or None,
            limit_per_ip=int(data.get('limit_per_ip', 0)),
            limit_per_user=int(data.get('limit_per_user', 1)),
            is_template=data.get('is_template', False),
            custom_css=data.get('custom_css', '')
        )

        # 2. First pass: create all Questions and their Choices
        questions_created = []
        for q_data in data.get('questions', []):
            question = Question.objects.create(
                poll=poll,
                text=q_data.get('text', ''),
                question_type=q_data.get('question_type', 'text'),
                is_required=q_data.get('is_required', True),
                order=q_data.get('order', 0)
            )
            questions_created.append(question)

            for choice_text in q_data.get('choices', []):
                if choice_text.strip():
                    Choice.objects.create(question=question, text=choice_text.strip())

        # 3. Second pass: apply conditional logic (depends_on)
        for i, q_data in enumerate(data.get('questions', [])):
            depends_on = q_data.get('depends_on')
            if depends_on:
                dep_q_idx = depends_on.get('question_index')
                dep_choice_text = depends_on.get('choice_text')

                if dep_q_idx is not None and dep_q_idx < len(questions_created):
                    dep_question = questions_created[dep_q_idx]
                    dep_choice = Choice.objects.filter(
                        question=dep_question, text=dep_choice_text
                    ).first()

                    current_question = questions_created[i]
                    current_question.depends_on_question = dep_question
                    current_question.depends_on_choice = dep_choice
                    current_question.save()

        return JsonResponse({'status': 'success', 'poll_id': poll.id})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def _load_template_data(template_id):
    """
    Private helper: loads data from an existing template Poll to pre-fill
    the creation form.
    """
    template = get_object_or_404(Poll, id=template_id, is_template=True)
    template_data = {
        'title': template.title,
        'description': template.description,
        'is_anonymous': template.is_anonymous,
        'questions': []
    }
    for q in template.questions.all():
        template_data['questions'].append({
            'text': q.text,
            'question_type': q.question_type,
            'is_required': q.is_required,
            'choices': [c.text for c in q.choices.all()]
        })
    return template_data


# ═══════════════════════════════════════════════════════
# POLL DELETION VIEW
# ═══════════════════════════════════════════════════════

@login_required
def delete_poll(request, poll_id):
    """
    Deletes a poll (and all its data via CASCADE).
    Only the poll creator or staff can delete it.
    Requires POST method for security.
    """
    poll = get_object_or_404(Poll, id=poll_id)

    if poll.creator != request.user and not request.user.is_staff:
        messages.error(request, "Vous n'êtes pas autorisé à supprimer ce sondage.")
        return redirect('dashboard')

    if request.method == 'POST':
        poll_title = poll.title
        poll.delete()
        messages.success(request, f"Le sondage « {poll_title} » a été supprimé.")
    return redirect('dashboard')


# ═══════════════════════════════════════════════════════
# POLL PARTICIPATION VIEWS
# ═══════════════════════════════════════════════════════

def take_poll(request, poll_id):
    """
    Allows a participant to view and answer a poll.

    GET  → validates access, shows the poll form.
    POST → processes and saves the submitted answers.
    """
    poll = get_object_or_404(Poll, id=poll_id, is_active=True)
    ip_address = get_client_ip(request)

    # ── Password check ──
    if not check_poll_password(poll, request):
        if request.method == 'POST' and 'poll_password' in request.POST:
            form = PollPasswordForm(request.POST)
            if form.is_valid():
                entered = form.cleaned_data['poll_password']
                if entered == poll.password:
                    unlock_poll_in_session(poll, request)
                    # Continue to render the poll below
                else:
                    messages.error(request, "Mot de passe incorrect.")
                    return render(request, 'polls/poll_password.html', {
                        'poll': poll,
                        'form': PollPasswordForm()
                    })
        else:
            return render(request, 'polls/poll_password.html', {
                'poll': poll,
                'form': PollPasswordForm()
            })

    # ── Access validation ──
    is_allowed, error_msg = check_poll_access(poll, request)
    if not is_allowed:
        messages.warning(request, error_msg)
        return redirect('home')

    # ── Process submitted answers ──
    if request.method == 'POST' and 'poll_password' not in request.POST:
        return _save_poll_answers(request, poll, ip_address)

    return render(request, 'polls/take_poll.html', {'poll': poll})


def _save_poll_answers(request, poll, ip_address):
    """
    Private helper: saves a participant's submitted answers to the database.
    """
    response_obj = Response.objects.create(
        poll=poll,
        user=request.user if not poll.is_anonymous and request.user.is_authenticated else None,
        ip_address=ip_address
    )

    for question in poll.questions.all():
        answer_key = f'question_{question.id}'

        if question.question_type == 'text':
            val = request.POST.get(answer_key, '').strip()
            if val or not question.is_required:
                Answer.objects.create(
                    response=response_obj, question=question, text_answer=val
                )

        elif question.question_type == 'scale':
            val = request.POST.get(answer_key)
            if val:
                Answer.objects.create(
                    response=response_obj, question=question, text_answer=val
                )

        elif question.question_type == 'choice_single':
            choice_id = request.POST.get(answer_key)
            if choice_id:
                ans = Answer.objects.create(response=response_obj, question=question)
                choice = Choice.objects.filter(id=choice_id, question=question).first()
                if choice:
                    ans.choices.add(choice)

        elif question.question_type == 'choice_multiple':
            choice_ids = request.POST.getlist(answer_key)
            if choice_ids:
                ans = Answer.objects.create(response=response_obj, question=question)
                choices = Choice.objects.filter(id__in=choice_ids, question=question)
                ans.choices.add(*choices)

    messages.success(request, "Merci pour votre participation ! Vos réponses ont bien été enregistrées.")
    return redirect('home')


# ═══════════════════════════════════════════════════════
# RESULTS & STATISTICS VIEWS
# ═══════════════════════════════════════════════════════

@login_required
def poll_results(request, poll_id):
    """
    Displays graphical results and statistics for a poll.
    Only the creator or staff members can view results.
    Supports optional response filtering by date and user type.
    """
    poll = get_object_or_404(Poll, id=poll_id)

    if poll.creator != request.user and not request.user.is_staff:
        messages.error(request, "Vous n'êtes pas autorisé à voir les résultats de ce sondage.")
        return redirect('home')

    filter_form = ResponseFilterForm(request.GET or None)
    results_data, responses_count = compute_poll_statistics(poll)

    # Build share link
    share_link = request.build_absolute_uri(f'/poll/{poll.id}/')

    return render(request, 'polls/poll_results.html', {
        'poll': poll,
        'results_data': results_data,
        'responses_count': responses_count,
        'filter_form': filter_form,
        'share_link': share_link,
    })


# ═══════════════════════════════════════════════════════
# EXPORT VIEWS
# ═══════════════════════════════════════════════════════

@login_required
def export_responses_csv(request, poll_id):
    """
    Exports all responses for a poll as a CSV file.
    Only accessible by the poll creator or staff.
    """
    poll = get_object_or_404(Poll, id=poll_id)

    if poll.creator != request.user and not request.user.is_staff:
        return HttpResponse("Accès refusé.", status=403)

    http_response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    http_response['Content-Disposition'] = (
        f'attachment; filename="sondage_{poll.id}_export.csv"'
    )

    writer = csv.writer(http_response)
    for row in build_csv_rows(poll):
        writer.writerow(row)

    return http_response


# ═══════════════════════════════════════════════════════
# POLL MANAGEMENT ACTIONS
# ═══════════════════════════════════════════════════════

@login_required
def toggle_poll_active(request, poll_id):
    """
    Toggles the is_active status of a poll (activate / deactivate).
    Only the creator or staff can toggle.
    """
    poll = get_object_or_404(Poll, id=poll_id)

    if poll.creator == request.user or request.user.is_staff:
        poll.is_active = not poll.is_active
        poll.save()
        status_str = "activé" if poll.is_active else "désactivé"
        messages.success(request, f"Le sondage « {poll.title} » a été {status_str}.")
    else:
        messages.error(request, "Action non autorisée.")

    return redirect('dashboard')


@login_required
def poll_share(request, poll_id):
    """
    Renders a dedicated sharing page for a poll with the share link,
    an embed code snippet, and QR code generation info.
    Only the poll creator can access this page.
    """
    poll = get_object_or_404(Poll, id=poll_id)

    if poll.creator != request.user and not request.user.is_staff:
        messages.error(request, "Accès refusé.")
        return redirect('dashboard')

    share_link = request.build_absolute_uri(f'/poll/{poll.id}/')
    embed_code = (
        f'<iframe src="{share_link}" width="100%" height="600" '
        f'frameborder="0"></iframe>'
    )

    return render(request, 'polls/poll_share.html', {
        'poll': poll,
        'share_link': share_link,
        'embed_code': embed_code,
    })
