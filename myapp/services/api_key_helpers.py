# myapp/services/api_key_helpers.py
from typing import Optional
from django.contrib.auth import get_user_model
from ..models import APIKey

User = get_user_model()

# Map agent name -> APIKey boolean field name
AGENT_FLAG_MAP = {
    "qna": "allow_qna",
    "data": "allow_data",
    "talent": "allow_talent",
    "stock": "allow_stock",
    "resume": "allow_resume",
    "sentiment": "allow_sentiment",
    "auto": "allow_auto",
    "rag": "allow_rag",
    # add more if needed
}

def get_api_key_obj_by_key(key: str) -> Optional[APIKey]:
    if not key:
        return None
    return APIKey.objects.filter(key=key, is_active=True).first()

def api_key_allows_agent(api_key_obj: APIKey, agent_name: str) -> bool:
    if not api_key_obj:
        return False
    flag = AGENT_FLAG_MAP.get(agent_name.lower())
    if not flag:
        return False
    return bool(getattr(api_key_obj, flag, False))

def get_user_api_key_for_agent(user: User, agent_name: str) -> Optional[APIKey]:
    """
    Find an active APIKey belonging to `user` that allows `agent_name`.
    Returns the APIKey object or None.
    """
    flag = AGENT_FLAG_MAP.get(agent_name.lower())
    if not flag:
        return None
    return APIKey.objects.filter(user=user, is_active=True, **{flag: True}).order_by('-created_at').first()
