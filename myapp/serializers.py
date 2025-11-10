from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from .models import *
import secrets

User = get_user_model()

# --- User Serializers ---

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'phone', 'password', 'created_at')
        read_only_fields = ('id', 'created_at')

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            phone=validated_data['phone'],
            # name=validated_data.get('name', ''),
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data.update({
            'message': 'Login successful!',
            'access': data.get('access'),
            'refresh': data.get('refresh'),
            'user_id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            # 'name': self.user.name,
        })
        return data



# --- Agent Related Serializers ---

class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = '__all__'


class AgentIntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentIntegration
        fields = '__all__'


# --- Chat System Serializers ---

class ConversationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Conversation
        fields = '__all__'

        
class ChatMessageSerializer(serializers.ModelSerializer):
    conversation = ConversationSerializer(read_only=True)
    agent = AgentSerializer(read_only=True)

    class Meta:
        model = ChatMessage
        fields = '__all__'


# --- Token and Subscription Serializers ---

class TokenLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    message = ChatMessageSerializer(read_only=True)

    class Meta:
        model = TokenLog
        fields = '__all__'


class SubscriptionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = '__all__'


# --- Other Models ---

class RootAgentMemorySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = RootAgentMemory
        fields = '__all__'



class APIKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = APIKey
        fields = "__all__"
        read_only_fields = ["id", "key", "user", "created_at"]

    def create(self, validated_data):
        # Generate a random secure API key
        validated_data["key"] = "sk_" + secrets.token_hex(16)
        return super().create(validated_data)



class AgentFeedbackSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    agent = AgentSerializer(read_only=True)

    class Meta:
        model = AgentFeedback
        fields = '__all__'
