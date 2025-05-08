import streamlit as st
import os
import base64
from openai import OpenAI
from PIL import Image
import io  # <--- Import io


# Initialize OpenAI client
client = OpenAI(api_key='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'
)

# --- Image Processing Function ---
# Takes a PIL Image object and the prompt, returns the text result
def process_image(pil_image, prompt):
    """
    Converts a PIL Image to base64, sends it to GPT-4 Vision with a prompt,
    and returns the text response.
    """
    try:
        # Convert PIL Image to bytes (using JPEG format)
        with io.BytesIO() as img_byte_arr:
            if pil_image.mode == 'RGBA':
                pil_image = pil_image.convert('RGB')
            pil_image.save(img_byte_arr, format='JPEG')
            img_bytes = img_byte_arr.getvalue()

        # Convert bytes to base64
        base64_image = base64.b64encode(img_bytes).decode("utf-8")
        data_url = f"data:image/jpeg;base64,{base64_image}"

        # Prepare the message for the API
        message = {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_url}}
            ]
        }

        # Call the OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o", # Or use "gpt-4o" which is newer and generally better/cheaper
            messages=[message],
            max_tokens=10024, # Increased max_tokens slightly for potentially larger outputs like CSV
        )
        return response.choices[0].message.content

    except Exception as e:
        st.error(f"An error occurred during image processing: {e}")
        return None

# --- Streamlit App UI ---
st.set_page_config(layout="wide") # Use wider layout
st.title("🖼️ Likh.AI - Image Text Extractor")

# Create tabs for different input methods
tab1, tab2 = st.tabs(["📷 Camera Input", "⬆️ File Upload"])

# --- Camera Input Tab ---
with tab1:
    st.header("Use Your Camera")
    camera_image_file = st.camera_input("Take a picture", key="camera_input", help="Allow access to your camera and take a picture.")

    # --- MODIFIED: Checkbox Logic ---
    format_csv_camera = st.checkbox("Format output as CSV?", key="format_csv_camera")
    is_structured_bill_camera = False # Default to False

    # Only show the structured bill checkbox if format_csv is checked
    if format_csv_camera:
        is_structured_bill_camera = st.checkbox("Is this a structured bill/invoice?", key="structured_bill_camera")
    # --- END MODIFIED ---

    process_camera_button = st.button("Process Camera Image", key="process_camera", use_container_width=True)

    if process_camera_button:
        # Capture latest state of checkboxes *when button is clicked*
        should_format_csv_camera = format_csv_camera
        should_be_structured_camera = is_structured_bill_camera if should_format_csv_camera else False

        if camera_image_file is not None:
            with st.spinner("Processing camera image... 🧠"):
                try:
                    pil_image = Image.open(camera_image_file)

                    # Determine the prompt based on captured states
                    if should_format_csv_camera:
                        if should_be_structured_camera:
                             # Use your specific prompt for structured bills formatted as CSV
                            prompt = "Extract the following fields from the attached invoice image into a structured CSV format with these columns: " \
                            "Date,Invoice No.,Particulars (name of originator) ,Location (of originator) ,GSTIN,Party Name,Party GSTIN,Item,MRP,Qty,Rate,Amount,Total Amount,Disc Amt.,IGST Payable,Grand Total. Each product entry in the invoice should be a separate row. For each row, fill in the shared invoice information (date, invoice no., etc.) along with the corresponding product details (Item, MRP, Qty, Rate, Amount). The final 'Total Amount', 'Disc Amt.', 'IGST Payable', and 'Grand Total' can be extracted from the summary section of the invoice and repeated or listed once as required. " \
                            "Use the image attached to extract the data. Striclty return the csv format. Nothing else, no words or any other charecters." # <--- REPLACE THIS
                        else:
                            # Use the unstructured CSV formatting prompt
                            prompt = "Extract all text content from this image and format it strictly as CSV. Treat it as unstructured text unless an obvious table is present. Structure lists/paragraphs reasonably within CSV rows."
                    else:
                        # Use the default plain text extraction prompt
                        prompt = "Extract all text content from this image exactly as it appears."

                    result = process_image(pil_image, prompt)

                    if result:
                        st.subheader("Extracted Text:")
                        st.markdown(result) # Use markdown for better display

                        # Show download button if CSV format was requested
                        if should_format_csv_camera:
                             # Dynamically change filename based on structured/unstructured
                            file_label = "structured_bill" if should_be_structured_camera else "unstructured_data"
                            st.download_button(
                                label="Download CSV",
                                data=result,
                                file_name=f"{file_label}_camera.csv",
                                mime="text/csv",
                                key=f"download_btn_camera_{file_label}" # Dynamic key
                            )

                except Exception as e:
                    st.error(f"Failed to open or process camera image: {e}")
        else:
            st.warning("Please take a picture first.")

# --- File Upload Tab ---
with tab2:
    st.header("Upload an Image File")
    uploaded_file = st.file_uploader(
        "Choose an image file",
        type=["jpg", "jpeg", "png", "webp"],
        key="file_uploader",
        help="Upload an image file (JPG, PNG, WEBP)."
    )

    # --- MODIFIED: Checkbox Logic ---
    format_csv_upload = st.checkbox("Format output as CSV?", key="format_csv_upload")
    is_structured_bill_upload = False # Default to False

    # Only show the structured bill checkbox if format_csv is checked
    if format_csv_upload:
        is_structured_bill_upload = st.checkbox("Is this a structured bill/invoice?", key="structured_bill_upload")
    # --- END MODIFIED ---

    process_upload_button = st.button("Process Uploaded Image", key="process_upload", use_container_width=True)

    if process_upload_button:
        # Capture latest state of checkboxes *when button is clicked*
        should_format_csv_upload = format_csv_upload
        should_be_structured_upload = is_structured_bill_upload if should_format_csv_upload else False

        if uploaded_file is not None:
            with st.spinner("Processing uploaded image... 🧠"):
                try:
                    pil_image = Image.open(uploaded_file)

                    # Determine the prompt based on captured states
                    if should_format_csv_upload:
                        if should_be_structured_upload:
                             # Use your specific prompt for structured bills formatted as CSV
                            prompt = "Extract the following fields from the attached invoice image into a structured CSV format with these columns: " \
                            "Date,Invoice No.,Particulars (name of originator) ,Location (of originator) ,GSTIN,Party Name,Party GSTIN,Item,MRP,Qty,Rate,Amount,Total Amount,Disc Amt.,IGST Payable,Grand Total. Each product entry in the invoice should be a separate row. For each row, fill in the shared invoice information (date, invoice no., etc.) along with the corresponding product details (Item, MRP, Qty, Rate, Amount). The final 'Total Amount', 'Disc Amt.', 'IGST Payable', and 'Grand Total' can be extracted from the summary section of the invoice and repeated or listed once as required. " \
                            "Use the image attached to extract the data. Striclty return the csv format. Nothing else, no words or any other charecters." # <--- REPLACE THIS
                        else:
                            # Use the unstructured CSV formatting prompt
                            prompt = "Extract all text content from this image, if transcription is difficult, attempt manual transcription for clarity, then format it strictly as CSV. Treat it as unstructured text unless an obvious table is present. Structure lists/paragraphs reasonably within CSV rows."
                    else:
                        # Use the default plain text extraction prompt
                        prompt = "Extract all text content from this image exactly as it appears, if transcription is difficult, attempt manual transcription for clarity."

                    result = process_image(pil_image, prompt)

                    if result:
                        st.subheader("Extracted Text:")
                        st.text_area("Result", result, height=300)

                        # Show download button if CSV format was requested
                        if should_format_csv_upload:
                             # Dynamically change filename based on structured/unstructured
                            file_label = "structured_bill" if should_be_structured_upload else "unstructured_data"
                            st.download_button(
                                label="Download CSV",
                                data=result,
                                file_name=f"{file_label}_upload.csv",
                                mime="text/csv",
                                key=f"download_btn_upload_{file_label}" # Dynamic key
                            )

                except Exception as e:
                    st.error(f"Failed to open or process uploaded file: {e}")
        else:
            st.warning("Please upload an image file first.")

st.markdown("---")
st.caption("Powered by OpenAI GPT-4 Vision & GPT-4o")