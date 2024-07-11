import os
import requests
import uvicorn
import jwt
from fastapi import Request, FastAPI, Depends
import gradio as gr
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse, JSONResponse
from dotenv import load_dotenv

from openbrain.ob_tuner.main_page import main_block as io
from openbrain.ob_tuner.landing_page import landing_page
load_dotenv()

CUSTOM_PATH = "/gradio"

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")

# if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are defined, unset AWS_PROFILE in the environment
if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
    os.environ.pop("AWS_PROFILE", None)



# @app.get("/")
# def read_main():
#
#     return {"error": str(e)}

@app.get("/health")
def health():
    return {"status": "ok"}


COGNITO_DOMAIN = os.getenv("COGNITO_DOMAIN")
CLIENT_ID = os.getenv("CLIENT_ID")
CALLBACK_URL = os.getenv("CALLBACK_URL")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")


@app.get("/login")
def login():
    # Redirect to the Cognito Hosted UI
    cognito_login_url = (
        f"{COGNITO_DOMAIN}/login?client_id={CLIENT_ID}" f"&response_type=code&scope=email+openid&redirect_uri={CALLBACK_URL}"
    )
    return RedirectResponse(cognito_login_url)


@app.get("/callback")
def callback(request: Request, code: str):
    token_url = f"{COGNITO_DOMAIN}/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": CALLBACK_URL,
    }
    response = requests.post(token_url, headers=headers, data=data)

    if response.status_code == 200:
        url = "/gradio?__theme=dark"
        tokens = response.json()
        id_token = tokens.get("id_token")
        response = RedirectResponse(url)

        response.set_cookie(key="id_token", value=id_token, httponly=True, secure=True)
        return response
    else:
        # Handle error response
        return JSONResponse(status_code=response.status_code, content={"message": "Authentication failed"})


def get_user(request: Request) -> str or None:
    try:
        id_token = request.cookies["id_token"]
    except KeyError:
        id_token = None

    if id_token:
        try:
            # Decode the token. Add 'options={"verify_signature": False}' if you don't want to verify the token's signature
            decoded_token = jwt.decode(id_token, options={"verify_signature": False}, algorithms=["RS256"])
            # Extract the email address and return it
            return decoded_token.get("email")
        except jwt.PyJWTError as e:
            # Handle decoding error (e.g., token is expired or invalid)
            print(f"Token decoding error: {e}")
            return None
    return None

@app.get('/')
def public(user: dict = Depends(get_user)):
    if user:
        return RedirectResponse(url='/gradio')
    else:
        return RedirectResponse(url='/login-demo')


@app.route('/logout')
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')

with gr.Blocks() as login_demo:
    gr.Button("Login", link="/login")

app = gr.mount_gradio_app(app, landing_page, path="/login-demo")

# app  = gr.mount_gradio_app(app, landing_page, path='/')
app = gr.mount_gradio_app(app, io, path=CUSTOM_PATH, auth_dependency=get_user)


if __name__ == "__main__":
    if os.getenv("GRADIO_PORT", False) or os.getenv("GRADIO_HOST", False):
        gradio_host = os.getenv("GRADIO_HOST", '0.0.0.0')
        gradio_port = int(os.getenv("GRADIO_PORT", 8000))
        uvicorn.run(app, host=gradio_host, port=gradio_port)
    else:
        uvicorn.run(app, host="0.0.0.0", port=80)
