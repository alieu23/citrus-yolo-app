import streamlit as st
import boto3
import pandas as pd
from PIL import Image
import io
import time
from datetime import datetime

# --- AWS Configuration ---
REGION = "us-east-2"
INPUT_BUCKET = "orchard-input-raw"
RESULTS_BUCKET = "orchard-results-annotated"
TABLE_NAME = "OrchardYieldMetadata"

s3 = boto3.client('s3', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

st.set_page_config(page_title="Citrus Yield Dashboard", layout="wide")

# --- INITIALIZE SESSION STATE ---
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = []
if 'last_upload_time' not in st.session_state:
    st.session_state.last_upload_time = None

# --- HEADER ---
st.title("🍊 Orchard AI: Citrus Yield Dashboard")

# --- AUTO-UPLOAD LOGIC ---
st.subheader("📸 Upload New Photos")
# Files start uploading as soon as they are dropped here
uploaded_files = st.file_uploader(
    "Drop images here to start AI analysis automatically...",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files='directory'
)

# This block triggers automatically when uploaded_files is not empty
if uploaded_files:
    # Check if we have already processed these specific files in this session
    current_upload_id = str(len(uploaded_files)) + uploaded_files[0].name

    if st.session_state.last_upload_time != current_upload_id:
        with st.status("🚀 Files detected! Uploading for inferencing...", expanded=True) as status:
            for file in uploaded_files:
                st.write(f"Uploading {file.name} to S3...")
                file_name = f"auto_{datetime.now().strftime('%H%M%S')}_{file.name}"
                s3.upload_fileobj(file, INPUT_BUCKET, file_name)

            st.session_state.last_upload_time = current_upload_id
            status.update(label="✅ Upload Complete! Waiting for Lambda inference...", state="complete")

            # Brief pause to allow Lambda to trigger and save to DynamoDB
            time.sleep(5)
            st.rerun()


# --- DATA FETCHING LOGIC ---
def get_latest_results():
    response = table.scan()
    items = response.get('Items', [])

    formatted_data = []
    for item in items:
        img_id = item.get('MediaID') or item.get('ImageID')
        count = int(item.get('Count') or item.get('OrangeCount') or 0)
        timestamp = item.get('Timestamp', 'Unknown')

        # S3 result path
        image_key = f"annotated_{img_id}"

        formatted_data.append({
            'image_name': img_id,
            'estimated_yield': count,
            'track_ids': "YOLO-V11-Live",
            'timestamp': timestamp,
            'image_key': image_key
        })

    # Sort by timestamp so newest is first
    return sorted(formatted_data, key=lambda x: x['timestamp'], reverse=True)


# Fetch data for display
data = get_latest_results()
st.session_state.processed_data = data

# --- MAIN UI TABS ---
if data:
    tab1, tab2 = st.tabs(["Orange Image", "Yield Report"])

    # --- TAB 1: Image Slider ---
    with tab1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("⬅️ Previous") and st.session_state.current_idx > 0:
                st.session_state.current_idx -= 1
        with col2:
            st.write(f"Showing Image {st.session_state.current_idx + 1} of {len(data)}")
        with col3:
            if st.button("Next ➡️") and st.session_state.current_idx < len(data) - 1:
                st.session_state.current_idx += 1

        current_item = data[st.session_state.current_idx]

        c1, c2 = st.columns([1, 1])
        with c1:
            st.metric("Detected Count", f"{current_item['estimated_yield']} Oranges")
        with c2:
            st.write(f"**Timestamp:** {current_item['timestamp']}")

        # Lazy-load the image only when viewing it (saves bandwidth)
        try:
            img_obj = s3.get_object(Bucket=RESULTS_BUCKET, Key=current_item['image_key'])
            visual_img = Image.open(io.BytesIO(img_obj['Body'].read()))
            st.image(visual_img, use_container_width=True)
        except:
            st.warning("🔄 Analysis in progress... The annotated image will appear here in a few seconds.")

    # --- TAB 2: Results Table ---
    with tab2:
        st.subheader("Yield Summary")

        report_df = pd.DataFrame([
            {'Image Name': item['image_name'], 'Estimated Yield': item['estimated_yield'], 'Date': item['timestamp']}
            for item in data
        ])

        total_oranges = report_df['Estimated Yield'].sum()
        avg_oranges = report_df['Estimated Yield'].mean()

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Yield", f"{total_oranges} Oranges")
        m2.metric("Avg. Yield / Tree", f"{avg_oranges:.1f}")
        m3.metric("Surveyed Units", len(report_df))

        st.markdown("---")
        st.write("#### Detailed Inventory")
        st.dataframe(report_df, use_container_width=True)
else:
    st.info("👋 Welcome! Please upload images above to start the automated AI analysis.")