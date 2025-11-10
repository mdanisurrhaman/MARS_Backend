from rest_framework.renderers import JSONRenderer

class CustomJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response", None)
        success = response is not None and response.status_code < 400

        # Base response format
        response_format = {
            "meta": {},
            "message": None,
            "error": not success
        }

        if success:
            # If dict, keep as meta; else wrap
            if isinstance(data, dict):
                response_format["meta"] = data
            else:
                response_format["meta"] = {"data": data}

            # Prefer explicit message key in views if provided
            if "message" in data:
                response_format["message"] = data.pop("message")
            else:
                response_format["message"] = "Success"
            response_format["error"] = False

        else:
            # Error case
            detail = None
            if isinstance(data, dict):
                detail = data.get("detail") or data.get("message") or data
            response_format["message"] = detail or "An error occurred"
            response_format["error"] = True
            response_format["meta"] = {}

        return super().render(response_format, accepted_media_type, renderer_context)
