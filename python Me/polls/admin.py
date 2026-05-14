"""
admin.py - Django Admin configuration for the polls application.
Registers all models with rich admin interfaces.
"""

from django.contrib import admin
from .models import Poll, Question, Choice, Response, Answer


# ─────────────────────────────────────────────
# Inline Admin Classes
# ─────────────────────────────────────────────

class ChoiceInline(admin.TabularInline):
    """Allows editing choices directly inside the Question admin page."""
    model = Choice
    extra = 2
    fields = ['text', 'order']
    ordering = ['order']


class QuestionInline(admin.StackedInline):
    """Allows editing questions directly inside the Poll admin page."""
    model = Question
    extra = 1
    fields = ['text', 'question_type', 'is_required', 'order']
    ordering = ['order']
    show_change_link = True


class AnswerInline(admin.TabularInline):
    """Allows viewing answers directly inside the Response admin page."""
    model = Answer
    extra = 0
    readonly_fields = ['question', 'text_answer', 'choices']
    can_delete = False


# ─────────────────────────────────────────────
# Model Admin Classes
# ─────────────────────────────────────────────

@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    """Admin interface for the Poll (Sondage) model."""
    list_display = [
        'title', 'creator', 'is_active', 'is_anonymous',
        'is_template', 'response_count', 'created_at', 'expires_at'
    ]
    list_filter = ['is_active', 'is_anonymous', 'is_template']
    search_fields = ['title', 'description', 'creator__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = None
    # inlines = [QuestionInline]  # Temporarily commented out to check if this causes the error

    fieldsets = (
        ('Informations générales', {
            'fields': ('title', 'description', 'creator')
        }),
        ('Paramètres d\'accès', {
            'fields': ('is_active', 'is_anonymous', 'password', 'expires_at')
        }),
        ('Limites de réponses', {
            'fields': ('limit_per_ip', 'limit_per_user'),
            'classes': ('collapse',)
        }),
        ('Personnalisation', {
            'fields': ('is_template', 'custom_css'),
            'classes': ('collapse',)
        }),
        ('Horodatage', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def response_count(self, obj):
        """Custom column showing number of responses."""
        return obj.responses.count()
    response_count.short_description = 'Réponses'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin interface for the Question model."""
    list_display = ['text', 'poll', 'question_type', 'is_required', 'order']
    list_filter = ['question_type', 'is_required']
    search_fields = ['text', 'poll__title']
    # inlines = [ChoiceInline]  # Temporarily commented out
    ordering = ['poll', 'order']


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    """Admin interface for the Choice model."""
    list_display = ['text', 'question', 'order']
    search_fields = ['text', 'question__text']
    ordering = ['question', 'order']


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    """Admin interface for the Response model."""
    list_display = ['id', 'poll', 'user', 'ip_address', 'created_at']
    list_filter = ['poll']
    search_fields = ['poll__title', 'user__username', 'ip_address']
    readonly_fields = ['poll', 'user', 'ip_address', 'created_at']
    date_hierarchy = None
    # inlines = [AnswerInline]  # Temporarily commented out to check if this causes the error


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    """Admin interface for the Answer model."""
    list_display = ['id', 'question', 'text_answer', 'response']
    search_fields = ['question__text', 'text_answer']
    # filter_horizontal = ['choices']  # Temporarily commented out
