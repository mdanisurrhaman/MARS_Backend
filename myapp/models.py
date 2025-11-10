from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
import secrets
from django.conf import settings

# Extended User model
class User(AbstractUser):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # keep username for compatibility

    def __str__(self):
        return self.email


# Agent model for AI microservices
class Agent(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    sample_code = models.TextField(blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# Each agent can have an API integration
class AgentIntegration(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='integrations')
    url = models.URLField()
    method = models.CharField(max_length=10)
    body = models.JSONField()
    headers = models.JSONField()

    def __str__(self):
        return f"Integration for {self.agent.name}"


# A user can have multiple conversations
class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="conversations")
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name="conversations")
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_root_agent = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.title:
            self.title = "New Chat"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} - {self.title}"


# Messages inside a conversation
class ChatMessage(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, related_name="chat_messages")
    sender = models.CharField(max_length=50, choices=(("user", "User"), ("agent", "Agent")), default="user")
    message = models.TextField()
    response = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='chat_files/', null=True, blank=True)
    tokens_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message {self.id} in {self.conversation}"



# Log of tokens consumed by user per message
class TokenLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='token_logs')
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='token_logs')
    tokens_used = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} used {self.tokens_used} tokens"


# User subscription for token limits
class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan_type = models.CharField(max_length=50)
    token_limit = models.IntegerField()
    tokens_used = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"{self.user.email} - {self.plan_type}"


# Store what the root agent routed
class RootAgentMemory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='root_agent_memories')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, null=True, blank=True, related_name='root_memories')
    user_input = models.TextField()
    routed_response = models.TextField()
    used_agents = models.JSONField()  # ✅ Easier querying
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Memory of {self.user.email}"


class APIKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    key = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    label = models.CharField(max_length=100, blank=True, default="")
    
    # Per-agent permissions
    allow_qna = models.BooleanField(default=False)
    allow_data = models.BooleanField(default=False)
    allow_talent = models.BooleanField(default=False)
    allow_stock = models.BooleanField(default=False)
    allow_resume = models.BooleanField(default=False)
    allow_sentiment = models.BooleanField(default=False)
    allow_auto = models.BooleanField(default=False)
    allow_rag = models.BooleanField(default=False)
    
    # ✅ Add this field
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.email} - {self.key[:6]}…"

# Label: [ My API Key ]
# [✔] QnA  
# [✔] Resume  
# [ ] Stock  
# [✔] RAG  
# ...
# [Generate Key]

# ---------------------------------------------------------------------
# User feedback about agents
class AgentFeedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='feedbacks')
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback by {self.user.email} on {self.agent.name}"
