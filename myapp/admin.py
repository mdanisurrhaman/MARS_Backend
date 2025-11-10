from django.contrib import admin
from .models import *

admin.site.register(User)
admin.site.register(Agent)
admin.site.register(AgentIntegration)
admin.site.register(Conversation)
admin.site.register(ChatMessage)
admin.site.register(TokenLog)
admin.site.register(Subscription)
admin.site.register(RootAgentMemory)
admin.site.register(APIKey)
admin.site.register(AgentFeedback)
