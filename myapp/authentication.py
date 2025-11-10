from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import APIKey

class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        key = auth_header.split("Bearer ")[1].strip()
        try:
            api_key = APIKey.objects.get(key=key, is_active=True)
        except APIKey.DoesNotExist:
            raise AuthenticationFailed("Invalid or inactive API Key.")

        # Attach api_key object to request so views can check per-agent permissions
        request.api_key = api_key  
        return (api_key.user, None)

    @staticmethod
    def check_agent_permission(request, agent_name: str):
        """
        Check if the API key allows access to the requested agent.
        """
        api_key = getattr(request, "api_key", None)
        if not api_key:
            raise AuthenticationFailed("API Key missing in request.")

        agent_map = {
            "qna": api_key.allow_qna,
            "data": api_key.allow_data,
            "talent": api_key.allow_talent,
            "stock": api_key.allow_stock,
            "resume": api_key.allow_resume,
            "sentiment": api_key.allow_sentiment,
            "auto": api_key.allow_auto,
            "rag": api_key.allow_rag,
        }

        if agent_name not in agent_map:
            raise AuthenticationFailed(f"Unknown agent: {agent_name}")

        if not agent_map[agent_name]:
            raise AuthenticationFailed(f"API Key not allowed to use {agent_name} agent.")

        return True
