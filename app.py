import streamlit as st
import os
import base64
import io
from openai import OpenAI
from PIL import Image

# -------------------------------
# Initialization
# -------------------------------
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")

client = OpenAI(api_key=api_key)
st.set_page_config(layout="wide")
st.title("🖼️ Likh.AI - Image Text Extractor")


# -------------------------------
# Helper Functions
# -------------------------------
def image_to_base64(pil_image: Image.Image) -> str:
    """Converts a PIL image to a base64 data URL."""
    with io.BytesIO() as buffer:
        if pil_image.mode == 'RGBA':
            pil_image = pil_image.convert('RGB')
        pil_image.save(buffer, format='JPEG')
        base64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{base64_str}"


def get_prompt(format_csv: bool, is_structured: bool) -> str:
    """Returns an appropriate prompt based on checkbox options."""
    if format_csv:
        if is_structured:
            return (
                "Extract the following fields from the attached invoice image into a structured CSV format with these columns: "
                "Date,Invoice No.,Particulars (name of originator),Location (of originator),GSTIN,Party Name,Party GSTIN,"
                "Item,MRP,Qty,Rate,Amount,Total Amount,Disc Amt.,IGST Payable,Grand Total. "
                "Each product entry should be a separate row. Reuse invoice-level fields for each row. "
                "Output strictly as CSV. No additional text or explanation."
            )
        else:
            return (
                "Extract all text content from this image and format it strictly as CSV. "
                "Treat it as unstructured unless obvious tabular data exists. Structure lists/paragraphs reasonably in CSV rows."
            )
    return "Extract all text content from this image exactly as it appears."


def process_image(pil_image: Image.Image, prompt: str) -> str:
    """Sends the image and prompt to OpenAI Vision API and returns the response."""
    try:
        data_url = image_to_base64(pil_image)
        message = {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[message],
            max_tokens=10024,
        )
        return response.choices[0].message.content

    except Exception as e:
        st.error(f"Image processing failed: {e}")
        return None


def render_extraction_ui(image_file, format_csv, is_structured, source: str):
    """Handles image processing logic and renders the result."""
    if image_file is not None:
        with st.spinner(f"Processing {source} image... 🧠"):
            try:
                pil_image = Image.open(image_file)
                prompt = get_prompt(format_csv, is_structured)
                result = process_image(pil_image, prompt)

                if result:
                    st.subheader("Extracted Text:")
                    st.text_area("Result", result, height=300)

                    if format_csv:
                        file_type = "structured_bill" if is_structured else "unstructured_data"
                        st.download_button(
                            label="Download CSV",
                            data=result,
                            file_name=f"{file_type}_{source}.csv",
                            mime="text/csv",
                            key=f"download_btn_{source}_{file_type}",
                        )
            except Exception as e:
                st.error(f"Failed to process image: {e}")
    else:
        st.warning(f"Please provide a {source} image first.")


# -------------------------------
# Streamlit Tabs
# -------------------------------
tab_camera, tab_upload = st.tabs(["📷 Camera Input", "⬆️ File Upload"])

# --- Camera Input Tab ---
with tab_camera:
    st.header("Capture an Image")
    camera_image = st.camera_input("Take a picture", key="camera_input")

    format_csv_cam = st.checkbox("Format output as CSV?", key="csv_camera")
    is_structured_cam = st.checkbox("Structured bill/invoice?", key="structured_camera") if format_csv_cam else False

    if st.button("Process Camera Image", use_container_width=True, key="process_camera"):
        render_extraction_ui(camera_image, format_csv_cam, is_structured_cam, "camera")

# --- File Upload Tab ---
with tab_upload:
    st.header("Upload an Image File")
    uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png", "webp"], key="file_uploader")

    format_csv_file = st.checkbox("Format output as CSV?", key="csv_upload")
    is_structured_file = st.checkbox("Structured bill/invoice?", key="structured_upload") if format_csv_file else False

    if st.button("Process Uploaded Image", use_container_width=True, key="process_upload"):
        render_extraction_ui(uploaded_file, format_csv_file, is_structured_file, "upload")

# Footer
st.markdown("---")
st.caption("🔗 Powered by OpenAI GPT-4o Vision | Built with ❤️ using Streamlit")
