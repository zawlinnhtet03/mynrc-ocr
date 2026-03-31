import io
import os
import time

import requests
import streamlit as st
from PIL import Image
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

st.set_page_config(page_title="KYC API Tester", layout="wide")

API_URL = os.getenv("API_URL")
API_KEY = os.getenv("OCR_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not API_URL:
    st.error(
        "API_URL environment variable is not set. Please configure it before running the app."
    )
    st.stop()

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    st.error(
        "Supabase credentials (SUPABASE_URL and SUPABASE_ANON_KEY) are required to use this app."
    )
    st.stop()

if API_KEY is None or str(API_KEY).strip() == "":
    st.error(
        "OCR_API_KEY environment variable is not set. Configure it before calling the API."
    )
    st.stop()


@st.cache_resource
def get_supabase_client(url: str, key: str) -> Client:
    return create_client(url, key)


supabase: Client = get_supabase_client(SUPABASE_URL, SUPABASE_ANON_KEY)

if "auth_user" not in st.session_state:
    st.session_state["auth_user"] = None


def ensure_authenticated() -> None:
    """Render Supabase login form and block the rest of the app until success."""
    if st.session_state["auth_user"]:
        return

    # st.header("Restricted Access")
    # st.write("Sign in with your authorized admin account to test the API.")
    # st.write("For academic verification or reproducibility access,")
    # st.write("please request test credentials from the author at: zawlinnhtet@dinger.asia, zaw.linn.htet03@gmail.com")

    st.header("Restricted Access")
    st.write("Sign in with your authorized admin account to test the API.")

    # Use st.info to make this stand out as a "Notice" box
    st.info(
        "**Note for Reviewers:** For academic verification or reproducibility access, "
        "please request test credentials from the author at:\n\n"
        "📧 `zawlinnhtet@dinger.asia` / `zaw.linn.htet03@gmail.com`"
    )

    with st.form("login_form"):
        email = st.text_input("Email", placeholder="name@dinger.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In")

    if submitted:
        if not email or not password:
            st.warning("Please provide both email and password.")
        else:
            try:
                auth_response = supabase.auth.sign_in_with_password(
                    {"email": email, "password": password}
                )
                user_email = getattr(getattr(auth_response, "user", None), "email", email)
                st.session_state["auth_user"] = {"email": user_email}
                st.success(f"Signed in as {user_email}")
                st.rerun()
            except Exception:
                st.error("Authentication failed. Please verify your correct credentials.")

    st.stop()


def sign_out() -> None:
    """Sign out the current user and clear any cached UI state."""
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state["auth_user"] = None
    st.session_state.pop("results", None)
    st.experimental_rerun()

# Image size limit 
MAX_IMAGE_SIZE = 1024  # px
REQUEST_TIMEOUT = 60   # seconds
RETRIES = 2

st.title("Dinger KYC • API Integration Test")

ensure_authenticated()

with st.sidebar:
    st.caption("API key: configured" if API_KEY else "API key: missing")
    st.caption(
        f"Signed in as **{st.session_state['auth_user']['email']}**"
        if st.session_state["auth_user"]
        else "Not authenticated"
    )
    if st.button("Sign Out"):
        sign_out()

col1, col2 = st.columns(2)

def call_modal_api(payload):
    headers = {
        "Content-Type": "application/octet-stream"
    }
    if API_KEY is not None and str(API_KEY).strip() != "":
        headers["Authorization"] = f"Bearer {API_KEY}"

    for attempt in range(RETRIES + 1):
        try:
            response = requests.post(
                API_URL,
                data=payload,
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )
            return response
        except requests.exceptions.RequestException as e:
            if attempt < RETRIES:
                time.sleep(3)
            else:
                raise e

with col1:
    st.subheader("Client Side")
    uploaded = st.file_uploader("Upload NRC", type=["jpg", "png", "jpeg"])

    if uploaded:
        img = Image.open(uploaded).convert("RGB")
        orig_w, orig_h = img.size

        # Resize image
        if max(img.size) > MAX_IMAGE_SIZE:
            img.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE))

        st.image(img, caption="Input Image", use_column_width=True)

        # Store uploaded file and img in session state for use in col2
        st.session_state["uploaded_file"] = uploaded
        st.session_state["img"] = img
        st.session_state["orig_size"] = (orig_w, orig_h)

        # Run simulation automatically on upload
        payload = uploaded.getvalue()

        st.write(f"Payload size: {len(payload) / 1024:.1f} KB")

        with st.spinner("Sending request to API..."):
            try:
                response = call_modal_api(payload)

                if response.status_code == 200:
                    data = response.json()
                    st.session_state["results"] = data
                    st.success(
                        f"Success! Time: {response.elapsed.total_seconds():.2f}s"
                    )
                else:
                    st.error(
                        f"API Error {response.status_code}: {response.text}"
                    )

            except Exception as e:
                st.error("Connection to API failed")
                st.exception(e)

        # --- Commented out Simulate Button ---
        # if st.button("Simulate Request"):
        #     img_byte_arr = io.BytesIO()
        #     img.save(img_byte_arr, format="JPEG", quality=85)
        #     payload = img_byte_arr.getvalue()
        #
        #     st.write(f"Payload size: {len(payload) / 1024:.1f} KB")
        #
        #     with st.spinner("Sending request to API..."):
        #         try:
        #             response = call_modal_api(payload)
        #
        #             if response.status_code == 200:
        #                 data = response.json()
        #                 st.session_state["results"] = data
        #                 st.success(
        #                     f"Success! Time: {response.elapsed.total_seconds():.2f}s"
        #                 )
        #             else:
        #                 st.error(
        #                     f"API Error {response.status_code}: {response.text}"
        #                 )
        #
        #         except Exception as e:
        #             st.error("Connection to API failed")
        #             st.exception(e)

with col2:
    st.subheader("Server Response (API Output)")

    if "results" in st.session_state:
        res = st.session_state["results"]

        # 1️⃣ Parsed fields
        fields = res.get("field_texts", {}) or {}
        display_fields = {
            "id": fields.get("id"),
            "name": fields.get("name"),
            "father": fields.get("father"),
            "dob": fields.get("dob"),
        }
        st.json(display_fields)

        rotation_steps_raw = res.get("rotation_ccw_steps", None)
        if rotation_steps_raw is None:
            st.warning("Backend did not return 'rotation_ccw_steps'. Redeploy the Modal backend or verify you're calling the updated endpoint.")
        else:
            st.caption(f"rotation_ccw_steps: {rotation_steps_raw}")

        # 2️⃣ Server image preview (no bounding boxes)
        if "img" in st.session_state:
            debug_img = st.session_state["img"].copy()
            rotation_steps = int(res.get("rotation_ccw_steps") or 0)
            rotation_steps = rotation_steps % 4
            if rotation_steps:
                debug_img = debug_img.rotate(90 * rotation_steps, expand=True)

            st.image(
                debug_img,
                caption="Server Image (No Bounding Boxes)",
                use_column_width=True
            )
