"""Google OAuth integration бо Authlib."""
from authlib.integrations.flask_client import OAuth

oauth = OAuth()


def init_google_oauth(app):
    """Google OAuth-ро бо app сабт мекунад."""
    oauth.init_app(app)
    oauth.register(
        name="google",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
    return oauth
