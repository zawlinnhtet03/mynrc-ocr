import io
import os
import time

import requests
import streamlit as st
from PIL import Image, ImageDraw
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


def _normalize_bbox_xyxy(bbox, img_w: int, img_h: int):
    """Return bbox as xyxy in pixel space, handling normalized and xywh inputs."""
    x1, y1, x2, y2 = [float(v) for v in bbox]

    # Handle normalized coordinates.
    if max(abs(x1), abs(y1), abs(x2), abs(y2)) <= 1.5:
        x1 *= img_w
        x2 *= img_w
        y1 *= img_h
        y2 *= img_h

    # Handle xywh format.
    if x2 <= x1 or y2 <= y1:
        x2 = x1 + x2
        y2 = y1 + y2

    # Ensure ordered coordinates.
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1

    # Clamp to image bounds.
    x1 = max(0.0, min(x1, float(img_w)))
    y1 = max(0.0, min(y1, float(img_h)))
    x2 = max(0.0, min(x2, float(img_w)))
    y2 = max(0.0, min(y2, float(img_h)))

    return x1, y1, x2, y2


def _rotate_point_ccw(x: float, y: float, w: int, h: int, steps: int):
    steps = steps % 4
    if steps == 0:
        return x, y
    if steps == 1:
        return y, (w - 1) - x
    if steps == 2:
        return (w - 1) - x, (h - 1) - y
    return (h - 1) - y, x


def _rotate_bbox_ccw_xyxy(x1: float, y1: float, x2: float, y2: float, w: int, h: int, steps: int):
    """Rotate an xyxy bbox around image origin for k*90deg CCW and return xyxy."""
    steps = steps % 4
    if steps == 0:
        return x1, y1, x2, y2

    corners = [
        _rotate_point_ccw(x1, y1, w, h, steps),
        _rotate_point_ccw(x2, y1, w, h, steps),
        _rotate_point_ccw(x1, y2, w, h, steps),
        _rotate_point_ccw(x2, y2, w, h, steps),
    ]
    xs = [pt[0] for pt in corners]
    ys = [pt[1] for pt in corners]
    return min(xs), min(ys), max(xs), max(ys)

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
        original_img = Image.open(io.BytesIO(uploaded.getvalue())).convert("RGB")
        img = original_img.copy()

        # Resize image
        if max(img.size) > MAX_IMAGE_SIZE:
            img.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE))

        st.image(img, caption="Input Image", use_column_width=True)

        # Store uploaded file and img in session state for use in col2
        st.session_state["uploaded_file"] = uploaded
        st.session_state["img"] = img
        st.session_state["api_request_size"] = original_img.size

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
        fields = res.get("field_texts", {})
        st.json(fields)

        rotation_steps_raw = res.get("rotation_ccw_steps", None)
        if rotation_steps_raw is None:
            st.warning("Backend did not return 'rotation_ccw_steps'. Redeploy the Modal backend or verify you're calling the updated endpoint.")
        else:
            st.caption(f"rotation_ccw_steps: {rotation_steps_raw}")

        if res.get("detection_image_size"):
            st.caption(f"detection_image_size: {res.get('detection_image_size')}")
        if res.get("detector_source"):
            st.caption(f"detector_source: {res.get('detector_source')}")

        # 2️⃣ Bounding box visualization
        if "img" in st.session_state and "detections" in res:
            debug_img = st.session_state["img"].copy()
            rotation_steps = int(res.get("rotation_ccw_steps") or 0)
            rotation_steps = rotation_steps % 4
            if rotation_steps:
                debug_img = debug_img.rotate(90 * rotation_steps, expand=True)
            draw = ImageDraw.Draw(debug_img)

            source_width, source_height = st.session_state.get(
                "api_request_size", st.session_state["img"].size
            )

            detection_image_size = res.get("detection_image_size")
            if (
                isinstance(detection_image_size, list)
                and len(detection_image_size) == 2
                and detection_image_size[0]
                and detection_image_size[1]
            ):
                request_width = float(detection_image_size[0])
                request_height = float(detection_image_size[1])
            else:
                request_width, request_height = source_width, source_height
                if rotation_steps % 2 == 1:
                    request_width, request_height = request_height, request_width

            scale_x = debug_img.width / request_width if request_width else 1.0
            scale_y = debug_img.height / request_height if request_height else 1.0

            for det in res["detections"]:
                x1, y1, x2, y2 = det["bbox"]
                x1, y1, x2, y2 = _normalize_bbox_xyxy(
                    (x1, y1, x2, y2), int(request_width), int(request_height)
                )

                sx1 = int(round(x1 * scale_x))
                sy1 = int(round(y1 * scale_y))
                sx2 = int(round(x2 * scale_x))
                sy2 = int(round(y2 * scale_y))

                draw.rectangle([sx1, sy1, sx2, sy2], outline="red", width=3)
                draw.text((sx1, sy1), det["label"], fill="red")

            st.image(
                debug_img,
                caption="Server Vision Debug",
                use_column_width=True
            )
