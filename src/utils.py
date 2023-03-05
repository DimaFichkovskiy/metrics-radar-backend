import jwt
from src.config import Config


class VerifyToken:
    def __init__(self, token):
        self.token = token
        self.config = Config
        self.signing_key = None

        jwks_url = f'https://{self.config.set_up_auth0()["DOMAIN"]}/.well-known/jwks.json'
        self.jwks_client = jwt.PyJWKClient(jwks_url)

    async def verify_token_from_auth0(self):
        try:
            self.signing_key = self.jwks_client.get_signing_key_from_jwt(self.token).key

        except jwt.exceptions.PyJWKClientError as error:
            return {"status": "error", "msg": error.__str__()}

        except jwt.exceptions.DecodeError as error:
            return {"status": "error", "msg": error.__str__()}

        try:
            payload = jwt.decode(
                self.token,
                self.signing_key,
                algorithms=self.config.set_up_auth0()["ALGORITHMS"],
                audience=self.config.set_up_auth0()["API_AUDIENCE"],
                issuer=self.config.set_up_auth0()["ISSUER"],
            )
        except Exception as e:
            return {"status": "error", "message": str(e)}

        return payload

    async def verify_token_from_me(self):
        try:
            payload = jwt.decode(
                self.token,
                self.config.SECRET_KEY,
                algorithms=[self.config.ENCODE_ALGORITHM]
            )
        except Exception as e:
            return {"status": "error", "message": str(e)}

        return payload
