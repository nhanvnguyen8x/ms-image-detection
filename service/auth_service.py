from flask import current_app


class AuthService:
    def validate_api_key(self, api_key: str) -> bool:
        return api_key == current_app.config['API_KEY']