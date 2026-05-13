from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Poll(models.Model):
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='polls')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_anonymous = models.BooleanField(default=False, help_text="Si vrai, les réponses ne sont pas liées à l'utilisateur.")
    password = models.CharField(max_length=128, blank=True, null=True, help_text="Optionnel: mot de passe pour accéder au sondage.")
    expires_at = models.DateTimeField(blank=True, null=True, help_text="Date limite pour répondre.")
    limit_per_ip = models.IntegerField(default=0, help_text="0 pour illimité.")
    limit_per_user = models.IntegerField(default=1, help_text="0 pour illimité.")
    is_template = models.BooleanField(default=False, help_text="Si vrai, sert de modèle pour créer d'autres sondages.")
    custom_css = models.TextField(blank=True, help_text="CSS personnalisé pour le design.")

    def __str__(self):
        return self.title

    @property
    def is_expired(self):
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        return False

class Question(models.Model):
    TYPE_CHOICES = [
        ('text', 'Texte libre'),
        ('choice_single', 'Choix unique'),
        ('choice_multiple', 'Choix multiple'),
        ('scale', 'Échelle (1-5)'),
    ]
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=500)
    question_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    is_required = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    # Logique conditionnelle
    depends_on_question = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='dependent_questions')
    depends_on_choice = models.ForeignKey('Choice', on_delete=models.SET_NULL, null=True, blank=True, related_name='dependent_questions_by_choice')

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.poll.title} - {self.text}"

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=255)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.text

class Response(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='poll_responses')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response to {self.poll.title} at {self.created_at}"

class Answer(models.Model):
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text_answer = models.TextField(blank=True, null=True)
    choices = models.ManyToManyField(Choice, blank=True)

    def __str__(self):
        return f"Answer to {self.question.text}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username} - Read: {self.is_read}"
