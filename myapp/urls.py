from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import *

# 🚀 CRUD API Router for Models
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'agents', AgentViewSet)
router.register(r'agent-integrations', AgentIntegrationViewSet)
router.register(r'conversations', ConversationViewSet)
router.register(r'chat-messages', ChatMessageViewSet)
router.register(r'token-logs', TokenLogViewSet)
router.register(r'subscriptions', SubscriptionViewSet)
router.register(r'root-memories', RootAgentMemoryViewSet)
router.register(r'api-keys', APIKeyViewSet, basename="api-keys")
router.register(r'agent-feedbacks', AgentFeedbackViewSet)

urlpatterns = [
    # 🔁 Agent APIs
    path('api/root-agent/', RootAgentAPIView.as_view(), name='root_agent'),
    path('api/agent/<str:agent_name>/', AgentAPIView.as_view(), name='agent_api'),

    # 💬 Chat APIs
    path('api/save-chat/', SaveChatAPIView.as_view(), name='save_chat'),

    # List all conversations for the authenticated user (summary only)
    path('api/conversation-history/', ConversationHistoryAPIView.as_view(), name='conversation_history'),

    # Get all messages for a single conversation
    path('api/conversation/<int:conversation_id>/messages/', ConversationMessagesAPIView.as_view(), name='conversation_messages'),

    path('api/conversation/<int:conversation_id>/delete/', DeleteConversationAPIView.as_view(), name='delete_conversation'),



    # Start a new chat with an agent
    path('api/new-chat/', NewChatAPIView.as_view(), name='new_chat'),




    # 🔐 Auth APIs
    path('api/signup/', SignUpView.as_view(), name='signup'),
    path('api/login/', CustomLoginView.as_view(), name='login'),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 🧱 Model CRUD endpoints
    path('api/', include(router.urls)),
    # Default (Python)
    path('api/integration-snippet/<str:agent_name>/', IntegrationSnippetAPIView.as_view(), name='integration_snippet_default'),

    # With language
    path('api/integration-snippet/<str:agent_name>/<str:language>/', IntegrationSnippetAPIView.as_view(), name='integration_snippet'),


    # 🌍 Public endpoints
    path('api/public-agents/', PublicAgentListView.as_view(), name='public-agents'),
    path('api/public-agents/<int:id>/', PublicAgentDetailView.as_view(), name='agent-detail'),
]
