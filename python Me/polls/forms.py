"""
forms.py - All Django Form classes for the polls application.
Separated from views.py to follow Django's MVT best practices.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Poll, Question, Choice


# ─────────────────────────────────────────────
# User Authentication Forms
# ─────────────────────────────────────────────

class UserRegistrationForm(UserCreationForm):
    """
    Extended user registration form with email field.
    Inherits from Django's built-in UserCreationForm.
    """
    email = forms.EmailField(
        required=True,
        label="Adresse e-mail",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'votre@email.com'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


# ─────────────────────────────────────────────
# Poll Management Forms
# ─────────────────────────────────────────────

class PollForm(forms.ModelForm):
    """
    Form for creating and editing a Poll (Sondage).
    Used by the create/edit poll views.
    """
    expires_at = forms.DateTimeField(
        required=False,
        label="Date limite",
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        input_formats=['%Y-%m-%dT%H:%M']
    )

    class Meta:
        model = Poll
        fields = [
            'title', 'description', 'is_anonymous',
            'password', 'expires_at', 'limit_per_ip',
            'limit_per_user', 'is_template', 'custom_css'
        ]
        labels = {
            'title': 'Titre du sondage',
            'description': 'Description',
            'is_anonymous': 'Sondage anonyme',
            'password': 'Mot de passe (optionnel)',
            'expires_at': 'Date limite',
            'limit_per_ip': 'Limite par adresse IP (0 = illimité)',
            'limit_per_user': 'Limite par utilisateur (0 = illimité)',
            'is_template': 'Enregistrer comme modèle',
            'custom_css': 'CSS personnalisé',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre de votre sondage'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description du sondage...'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Laisser vide si aucun mot de passe'}, render_value=True),
            'limit_per_ip': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'limit_per_user': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'custom_css': forms.Textarea(attrs={'class': 'form-control font-monospace', 'rows': 5, 'placeholder': '/* Votre CSS personnalisé ici */'}),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_template': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class QuestionForm(forms.ModelForm):
    """
    Form for a single Question within a poll.
    Used inline within poll creation/editing.
    """
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'is_required', 'order']
        labels = {
            'text': 'Texte de la question',
            'question_type': 'Type de question',
            'is_required': 'Obligatoire',
            'order': 'Ordre',
        }
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre question...'}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


class ChoiceForm(forms.ModelForm):
    """
    Form for a single Choice option within a question.
    """
    class Meta:
        model = Choice
        fields = ['text', 'order']
        labels = {
            'text': 'Texte du choix',
            'order': 'Ordre',
        }
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option de réponse...'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


# ─────────────────────────────────────────────
# Poll Taking Form (for participants)
# ─────────────────────────────────────────────

class PollPasswordForm(forms.Form):
    """
    Simple form to unlock a password-protected poll.
    """
    poll_password = forms.CharField(
        label="Mot de passe du sondage",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez le mot de passe'
        })
    )


# ─────────────────────────────────────────────
# Export / Filter Forms
# ─────────────────────────────────────────────

class ResponseFilterForm(forms.Form):
    """
    Form for filtering/segmenting responses on the results page.
    """
    date_from = forms.DateField(
        required=False,
        label="Du",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        label="Au",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    user_type = forms.ChoiceField(
        required=False,
        label="Type d'utilisateur",
        choices=[
            ('', 'Tous'),
            ('authenticated', 'Connectés'),
            ('anonymous', 'Anonymes'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
