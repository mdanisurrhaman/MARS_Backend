from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework import generics, status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.conf import settings
from django.shortcuts import get_object_or_404
# from rest_framework.authentication import BasicAuthentication
from rest_framework.exceptions import PermissionDenied
from .models import *
from .serializers import *
from .services.ai_gateway import call_ai_agent
from .services.code_snippet_generator import generate_code_snippet
from .authentication import APIKeyAuthentication


import os

User = get_user_model()

# ==================== Root Agent View ====================
class RootAgentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        query = request.data.get("query") or request.data.get("message")  # support both keys
        file = request.FILES.get("file")
        conversation_id = request.data.get("conversation_id")
        user = request.user

        if not query and not file:
            return Response({"error": "query or file is required"}, status=400)

        # Handle temp file saving
        file_path = None
        if file:
            os.makedirs('temp', exist_ok=True)
            file_path = f"temp/{file.name}"
            with open(file_path, 'wb+') as dest:
                for chunk in file.chunks():
                    dest.write(chunk)

        # Get root agent
        root_agent, _ = Agent.objects.get_or_create(
            name="root",
            defaults={"description": "Root Orchestrator Agent"}
        )

        # Normalize conversation_id: convert to int if possible, otherwise None
        try:
            conversation_id = int(conversation_id)
        except (TypeError, ValueError):
            conversation_id = None

        # Get or create conversation
        if conversation_id:
            conversation = get_object_or_404(Conversation, id=conversation_id, user=user)
            if conversation.agent != root_agent:
                return Response({"error": "Conversation agent mismatch"}, status=403)
        else:
            conversation = Conversation.objects.create(
                user=user,
                agent=root_agent,
                title=f"Chat with {root_agent.name}"
            )

        # Save user message
        user_message_text = query if query else "[File uploaded]"
        user_tokens = len(user_message_text.split()) if query else 0

        ChatMessage.objects.create(
            conversation=conversation,
            agent=root_agent,
            sender="user",
            message=user_message_text,
            tokens_used=user_tokens,
            file=file if file else None
        )

        # Call AI agent
        result = call_ai_agent("root", query, file_path)

        # Normalize AI reply text
        if isinstance(result, dict):
            ai_reply_text = result.get('text') or result.get('answer') or str(result)
        else:
            ai_reply_text = str(result)

        # Save AI reply
        agent_tokens = len(ai_reply_text.split())
        ChatMessage.objects.create(
            conversation=conversation,
            agent=root_agent,
            sender="agent",
            message=ai_reply_text,
            tokens_used=agent_tokens
        )

        # Clean up temp file
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

        return Response({
            "conversation_id": conversation.id,
            "user_message": user_message_text,
            "ai_reply": ai_reply_text
        }, status=200)



# ==================== Individual Agent View ====================
def save_uploaded_file(uploaded_file, folder="temp"):
    if uploaded_file:
        os.makedirs(folder, exist_ok=True)
        saved_path = os.path.join(folder, uploaded_file.name)
        with open(saved_path, "wb+") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        return saved_path
    return None


class AgentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, agent_name):
        query = request.data.get("query")
        file = request.FILES.get("file")
        csv = request.FILES.get("csv")
        print("query :", query)
        print("file :", file)
        # csv_file = request.FILES.get("csv")
        agent_name = agent_name or request.data.get("agent_name")
        user = request.user

        # ✅ If talent agent, use the whole request.data dict
        if agent_name == "talent":
            query = request.data  

        file_path = save_uploaded_file(file)
        csv_file_path = save_uploaded_file(csv)


        # # If using API Key
        # auth_header = request.headers.get("Authorization", "")
        # if "Bearer " in auth_header:
        #     key = auth_header.split("Bearer ")[1]
        #     try:
        #         api_key = APIKey.objects.get(key=key, is_active=True)
        #     except APIKey.DoesNotExist:
        #         return Response({"error": "Invalid API key"}, status=403)

        #     # Check if agent allowed
        #     if not api_key.allowed_agents.filter(name=agent_name).exists():
        #         return Response({"error": "This API key does not allow access to this agent."}, status=403)


        result = call_ai_agent(agent_name, query, file_path, csv_file=csv_file_path)

        # Clean up files after processing
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        if csv_file_path and os.path.exists(csv_file_path):
            os.remove(csv_file_path)

        return Response({
            "response": result,
            "used_agent": agent_name
        })

# ==================== CRUD ViewSets ====================
class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class AgentViewSet(ModelViewSet):
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer
    permission_classes = [IsAuthenticated]


class AgentIntegrationViewSet(ModelViewSet):
    queryset = AgentIntegration.objects.all()
    serializer_class = AgentIntegrationSerializer
    permission_classes = [IsAuthenticated]


class ConversationViewSet(ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChatMessageViewSet(ModelViewSet):
    queryset = ChatMessage.objects.all()
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatMessage.objects.filter(conversation__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save()


class TokenLogViewSet(ModelViewSet):
    queryset = TokenLog.objects.all()
    serializer_class = TokenLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TokenLog.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SubscriptionViewSet(ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RootAgentMemoryViewSet(ModelViewSet):
    queryset = RootAgentMemory.objects.all()
    serializer_class = RootAgentMemorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RootAgentMemory.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class APIKeyViewSet(ModelViewSet):
    serializer_class = APIKeySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only return keys owned by logged-in user
        return APIKey.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        if instance.user == self.request.user:
            instance.delete()




class AgentFeedbackViewSet(ModelViewSet):
    queryset = AgentFeedback.objects.all()
    serializer_class = AgentFeedbackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AgentFeedback.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PublicAgentListView(ListAPIView):
    queryset = Agent.objects.filter(is_featured=True).order_by('display_order')
    serializer_class = AgentSerializer
    permission_classes = [AllowAny]


class PublicAgentDetailView(RetrieveAPIView):
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'  # or use 'name' if URLs use names

# ==================== Auth: SignUp, Login, Logout ====================
from rest_framework.response import Response
from rest_framework import status

class SignUpView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({"message": "Account created successfully!"}, status=status.HTTP_201_CREATED)


class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        # Get tokens from serializer
        data = serializer.validated_data
        return Response({
            "message": "Login successful!",
            "access": data["access"],
            "refresh": data["refresh"]
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful."}, status=205)
        except Exception as e:
            return Response({"error": str(e)}, status=400)



class IntegrationSnippetAPIView(APIView):
    permission_classes = [IsAuthenticated]  # ✅ only logged-in users

    def get(self, request, agent_name, language="python"):
        user = request.user

        # Get agent
        agent = get_object_or_404(Agent, name=agent_name)

        # Get agent integration info
        integration = AgentIntegration.objects.filter(agent=agent).first()
        if not integration:
            return Response({"error": "Integration details not found."}, status=404)

        # ✅ Instead of looking up APIKey, just insert placeholder
        snippet = generate_code_snippet(
            agent_name=agent.name,
            api_key="<YOUR_API_KEY>",  # placeholder for user to replace later
            url=integration.url,
            method=integration.method,
            body=integration.body,
            language=language
        )

        return Response({
            "agent": agent.name,
            "description": agent.description,
            "language": language,
            "integration_snippet": snippet,
            "note": "Replace <YOUR_API_KEY> with a valid API key when using this code outside."
        }, status=200)




# ==================== Chat History APIs ====================

class SaveChatAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        conversation_id = request.data.get("conversation_id")
        message = request.data.get("message")
        sender = request.data.get("sender", "user")

        if not message:
            return Response({"error": "message is required"}, status=400)

        root_agent = get_object_or_404(Agent, name="root")

        # Get or create conversation with root agent
        if conversation_id:
            conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
            if conversation.agent != root_agent:
                return Response({"error": "Conversation agent mismatch"}, status=403)
        else:
            conversation = Conversation.objects.create(
                user=request.user,
                agent=root_agent,
                title=f"Chat with {root_agent.name}"
            )

        # Save message with agent set to root agent
        ChatMessage.objects.create(
            conversation=conversation,
            agent=root_agent,
            sender=sender,
            message=message,
            tokens_used=len(message.split())
        )

        return Response({
            "conversation_id": conversation.id,
            "message": "Message saved successfully."
        }, status=201)



class ConversationHistoryAPIView(APIView):
    """
    Get all conversations for the authenticated user only with the root agent.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        root_agent = get_object_or_404(Agent, name="root")
        conversations = Conversation.objects.filter(user=request.user, agent=root_agent).order_by("-created_at")
        data = []

        for convo in conversations:
            last_message = ChatMessage.objects.filter(conversation=convo).order_by("-created_at").first()
            data.append({
                "conversation_id": convo.id,
                "title": convo.title,
                "agent": convo.agent.name if convo.agent else None,
                "last_message": last_message.message if last_message else None,
                "updated_at": last_message.created_at if last_message else convo.created_at
            })

        return Response(data, status=200)


class ConversationMessagesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
        if conversation.agent.name != "root":
            return Response({"error": "This conversation is not with the root agent."}, status=403)

        messages = ChatMessage.objects.filter(conversation=conversation).order_by("created_at")
        data = [{
            "sender": msg.sender,
            "message": msg.message,
            "created_at": msg.created_at,
            "tokens_used": msg.tokens_used
        } for msg in messages]

        return Response(data, status=200)



# ----------------------------------------------------------------



class NewChatAPIView(APIView):
    """
    Start a completely new conversation with the root agent only.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        root_agent = get_object_or_404(Agent, name="root")

        conversation = Conversation.objects.create(
            user=request.user,
            agent=root_agent,
            title=f"Chat with {root_agent.name}"
        )

        return Response({
            "conversation_id": conversation.id,
            "title": conversation.title,
            "agent": root_agent.name
        }, status=201)




class DeleteConversationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, conversation_id):
        # Fetch the conversation that belongs to the user
        conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
        conversation.delete()
        return Response({"message": "Conversation deleted successfully."}, status=status.HTTP_204_NO_CONTENT)




def check_agent_permission(api_key, agent_name):
    mapping = {
        "qna": api_key.allow_qna,
        "data": api_key.allow_data,
        "talent": api_key.allow_talent,
        "stock": api_key.allow_stock,
        "resume": api_key.allow_resume,
        "sentiment": api_key.allow_sentiment,
        "auto": api_key.allow_auto,
        "rag": api_key.allow_rag,
    }

    if agent_name not in mapping or not mapping[agent_name]:
        raise PermissionDenied(f"Your API key is not authorized to access the {agent_name} agent.")
