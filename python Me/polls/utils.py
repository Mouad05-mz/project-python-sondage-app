"""
utils.py - Utility / helper functions for the polls application.
Separated to keep views.py clean and avoid code duplication.
"""

import uuid
from django.utils import timezone
from .models import Response


# ─────────────────────────────────────────────
# Network Helpers
# ─────────────────────────────────────────────

def get_client_ip(request):
    """
    Extracts the real IP address of the client from the request,
    handling proxies via the X-Forwarded-For header.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ─────────────────────────────────────────────
# Poll Access / Validation Helpers
# ─────────────────────────────────────────────

def check_poll_access(poll, request):
    """
    Validates whether a user/IP can access and respond to a poll.

    Returns a tuple: (is_allowed: bool, error_message: str or None)
    """
    ip_address = get_client_ip(request)

    # 1. Check if the poll has expired
    if poll.is_expired:
        return False, "Ce sondage a expiré et n'accepte plus de réponses."

    # 2. Check per-user response limit
    if poll.limit_per_user > 0 and request.user.is_authenticated:
        user_response_count = Response.objects.filter(
            poll=poll, user=request.user
        ).count()
        if user_response_count >= poll.limit_per_user:
            return False, "Vous avez déjà atteint la limite de réponses pour ce sondage."

    # 3. Check per-IP response limit
    if poll.limit_per_ip > 0:
        ip_response_count = Response.objects.filter(
            poll=poll, ip_address=ip_address
        ).count()
        if ip_response_count >= poll.limit_per_ip:
            return False, "La limite de réponses pour votre adresse IP a été atteinte."

    return True, None


def check_poll_password(poll, request):
    """
    Checks if a password-protected poll has been unlocked in the session.

    Returns True if access is granted, False if password required.
    """
    if not poll.password:
        return True  # No password needed

    session_key = f'poll_unlocked_{poll.id}'
    entered = request.session.get(session_key)
    return entered == poll.password


def unlock_poll_in_session(poll, request):
    """
    Stores the correct poll password in the session to grant access.
    """
    session_key = f'poll_unlocked_{poll.id}'
    request.session[session_key] = poll.password


# ─────────────────────────────────────────────
# Statistics Helpers
# ─────────────────────────────────────────────

def compute_poll_statistics(poll):
    """
    Computes aggregated statistics for each question in a poll.

    Returns a list of dicts, one per question, with computed stats
    ready to pass to templates / Chart.js.
    """
    from .models import Answer  # local import to avoid circular imports

    responses_count = poll.responses.count()
    results_data = []

    for question in poll.questions.all():
        stats = {
            'question': question,
            'type': question.question_type,
            'responses_count': responses_count,
        }

        if question.question_type in ['choice_single', 'choice_multiple']:
            choices_stats = []
            for choice in question.choices.all():
                count = Answer.objects.filter(
                    question=question, choices=choice
                ).count()
                percentage = round((count / responses_count * 100), 1) if responses_count > 0 else 0
                choices_stats.append({
                    'text': choice.text,
                    'count': count,
                    'percentage': percentage,
                })
            stats['choices'] = choices_stats

        elif question.question_type == 'scale':
            scale_stats = []
            total_answers = 0
            total_value = 0
            for i in range(1, 6):
                count = Answer.objects.filter(
                    question=question, text_answer=str(i)
                ).count()
                percentage = round((count / responses_count * 100), 1) if responses_count > 0 else 0
                scale_stats.append({'value': i, 'count': count, 'percentage': percentage})
                total_answers += count
                total_value += count * i
            avg = round(total_value / total_answers, 2) if total_answers > 0 else 0
            stats['scale'] = scale_stats
            stats['scale_avg'] = avg

        elif question.question_type == 'text':
            text_answers = Answer.objects.filter(
                question=question
            ).exclude(text_answer='').values_list('text_answer', flat=True)[:50]
            stats['texts'] = list(text_answers)

        results_data.append(stats)

    return results_data, responses_count


# ─────────────────────────────────────────────
# Export Helpers
# ─────────────────────────────────────────────

def build_csv_rows(poll):
    """
    Generator that yields one row (list) at a time for CSV export.
    First yields the header row, then one row per response.
    """
    from .models import Answer  # local import

    questions = list(poll.questions.all())

    # Header row
    header = ['ID Réponse', 'Date', 'Utilisateur', 'IP']
    for q in questions:
        header.append(q.text)
    yield header

    # Data rows
    for res in poll.responses.select_related('user').all():
        row = [
            res.id,
            res.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            res.user.username if res.user else 'Anonyme',
            res.ip_address or '',
        ]
        for q in questions:
            ans = Answer.objects.filter(response=res, question=q).first()
            if not ans:
                row.append('')
            elif q.question_type == 'text':
                row.append(ans.text_answer or '')
            elif q.question_type == 'scale':
                row.append(ans.text_answer or '')
            elif q.question_type == 'choice_single':
                c = ans.choices.first()
                row.append(c.text if c else '')
            elif q.question_type == 'choice_multiple':
                row.append(', '.join(c.text for c in ans.choices.all()))
            else:
                row.append('')
        yield row
