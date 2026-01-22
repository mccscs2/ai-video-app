import streamlit as st
import os
import fal_client
from PIL import Image
import io
import requests

# Set up page
st.set_page_config(
    page_title="AI Character Animation Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("🎬 AI Character Animation Studio")
st.markdown("Create character animations, modify images, and generate videos—all with artist control")

# Load the FAL API key from Streamlit Secrets
fal_api_key = st.secrets.get("fal_api_key")

if not fal_api_key:
    st.error("❌ FAL API key not found in Streamlit Secrets!")
    st.stop()

# Set it as environment variable so fal_client can find it
os.environ["FAL_KEY"] = fal_api_key

# ============================================================================
# SIDEBAR: Settings & Safety Toggle
# ============================================================================
with st.sidebar:
    st.header("⚙️ Settings & Safety")
    
    # Safety toggle
    safety_enabled = st.checkbox("🛡️ Safety Features (Moderate)", value=True)
    safety_level = st.select_slider(
        "Safety Level (if enabled)",
        options=["Strict", "Moderate", "Creative"],
        value="Moderate"
    )
    
    if safety_enabled and safety_level == "Strict":
        safety_tolerance = 0.5
    elif safety_enabled and safety_level == "Moderate":
        safety_tolerance = 0.7
    else:  # Creative or disabled
        safety_tolerance = 0.9
    
    st.markdown(f"**Active Safety Level:** `{safety_level}`")
    st.info(
        "💡 **Artist Override:** Creative mode gives maximum freedom. "
        "Use 'Strict' for family-friendly content.",
        icon="ℹ️"
    )
    
    # Video duration
    st.markdown("---")
    st.subheader("🎞️ Video Settings")
    video_duration = st.select_slider(
        "Video Duration (seconds)",
        options=[5, 7, 10, 12, 15],
        value=7
    )
    
    # Advanced options
    st.markdown("---")
    show_advanced = st.checkbox("Show Advanced Options", value=False)


# ============================================================================
# MAIN TABS
# ============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🎨 Text-to-Image",
    "📸 Image Editor",
    "🎭 Character Animation",
    "📹 Video Generator"
])


# ============================================================================
# TAB 1: TEXT-TO-IMAGE
# ============================================================================
with tab1:
    st.header("🎨 Generate Images from Text")
    st.markdown("Describe what you want to create, and Flux 2 will generate it.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        prompt = st.text_area(
            "Describe your image",
            placeholder="e.g., 'A serene mountain landscape at sunset with golden light'",
            height=100
        )
    
    with col2:
        aspect_ratio = st.selectbox(
            "Aspect Ratio",
            ["1:1 (Square)", "16:9 (Landscape)", "9:16 (Portrait)"]
        )
        aspect_map = {
            "1:1 (Square)": "1:1",
            "16:9 (Landscape)": "16:9",
            "9:16 (Portrait)": "9:16"
        }
    
    if st.button("✨ Generate Image", key="gen_image"):
        if not prompt.strip():
            st.error("Please enter a prompt")
        else:
            with st.spinner("🔮 Generating image..."):
                try:
                    result = fal_client.run_sync(
                     "fal-ai/flux-pro/v1.1",
                        arguments={
                            "prompt": prompt,
                            "aspect_ratio": aspect_map[aspect_ratio],
                            "safety_tolerance": safety_tolerance if safety_enabled else 0.9,
                            "seed": 42,
                        }
                    )
                    
                    # Display result
                    image_url = result["images"][0]["url"]
                    st.image(image_url, caption=prompt, use_column_width=True)
                    
                    # Store in session for Image Editor tab
                    st.session_state.last_generated_image_url = image_url
                    
                    # Download button
                    response = requests.get(image_url)
                    st.download_button(
                        "📥 Download Image",
                        data=response.content,
                        file_name="generated_image.png",
                        mime="image/png"
                    )
                except Exception as e:
                    st.error(f"❌ Error generating image: {str(e)}")
                    st.info("💡 Tip: Check that your FAL API key is valid and has credits remaining.")




# ============================================================================
# TAB 2: IMAGE EDITOR
# ============================================================================
with tab2:
    st.header("📸 Image Editor - Modify Images")
    st.markdown("Upload an image and describe changes you want to make.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload image to edit",
            type=["png", "jpg", "jpeg"],
            key="edit_uploader"
        )
    
    with col2:
        if "last_generated_image_url" in st.session_state:
            if st.button("📎 Use Last Generated Image"):
                st.session_state.use_generated = True
                st.rerun()
    
    if uploaded_file or st.session_state.get("use_generated", False):
        # Display uploaded image
        if st.session_state.get("use_generated", False):
            st.image(st.session_state.last_generated_image_url, caption="Original Image", width=300)
            st.session_state.use_generated = False
        else:
            image_data = Image.open(uploaded_file)
            st.image(image_data, caption="Original Image", width=300)
        
        # Edit prompt
        st.markdown("---")
        edit_prompt = st.text_area(
            "What would you like to change? (e.g., 'Change the sky to purple', 'Add a rainbow')",
            height=80
        )
        
        if st.button("🎨 Apply Edits", key="apply_edits"):
            if not edit_prompt.strip():
                st.error("Please describe the changes you want")
            else:
                with st.spinner("🎨 Editing image..."):
                    try:
                        result = fal_client.run_sync(
                            "fal-ai/flux-pro/v1.1",
                            arguments={
                                "prompt": edit_prompt,
                                "safety_tolerance": safety_tolerance if safety_enabled else 0.9,
                                "num_inference_steps": 4,
                            }
                        )
                        
                        # Display result
                        edited_image_url = result["images"][0]["url"]
                        st.image(edited_image_url, caption="Edited Image", use_column_width=True)
                        
                        # Download button
                        response = requests.get(edited_image_url)
                        st.download_button(
                            "📥 Download Edited Image",
                            data=response.content,
                            file_name="edited_image.png",
                            mime="image/png"
                        )

                    except Exception as e:
                        st.error(f"❌ Error editing image: {str(e)}")
                        st.info("💡 Tip: Ensure your image is clear and the edit description is detailed.")




# ============================================================================
# TAB 3: CHARACTER ANIMATION
# ============================================================================
with tab3:
    st.header("🎭 Character Animation - Bring Characters to Life")
    st.markdown("Choose animation style for your character.")
    
    animation_style = st.selectbox(
        "Animation Style",
        [
            "Talking Avatar (Kling Avatar v2)",
            "Motion Transfer (Copy a dance/action)",
            "Full Character Animation"
        ]
    )
    
    if animation_style == "Talking Avatar (Kling Avatar v2)":
        st.subheader("Create a Talking Avatar")
        st.markdown("Upload a portrait, add audio, and create a talking avatar video.")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**Step 1: Upload Portrait**")
            portrait = st.file_uploader(
                "Upload portrait image (square, 1080x1080 recommended)",
                type=["png", "jpg", "jpeg"],
                key="avatar_portrait"
            )
            
            if portrait:
                img = Image.open(portrait)
                st.image(img, caption="Your Avatar Portrait", width=200)
        
        with col2:
            st.markdown("**Step 2: Upload Audio**")
            audio = st.file_uploader(
                "Upload audio file (MP3, WAV)",
                type=["mp3", "wav", "m4a"],
                key="avatar_audio"
            )
            
            if audio:
                st.audio(audio)
        
        if st.button("🎬 Generate Talking Avatar", key="gen_avatar"):
            if not portrait or not audio:
                st.error("Please upload both portrait and audio")
            else:
                st.info("⏳ Processing: This uses Kling Avatar v2 API. Please wait...")
                st.warning(
                    "Note: Full implementation requires uploading files to cloud storage (S3, etc). "
                    "For testing, use FAL's web UI at https://fal.ai/models/fal-ai/kling-video/ai-avatar/v2/pro"
                )
    
    elif animation_style == "Motion Transfer (Copy a dance/action)":
        st.subheader("Transfer Motion from Reference Video")
        st.markdown("Upload a character portrait and a reference video with the motion you want.")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**Character Image**")
            char_image = st.file_uploader(
                "Upload character/portrait",
                type=["png", "jpg", "jpeg"],
                key="motion_char"
            )
            if char_image:
                st.image(char_image, caption="Character", width=200)
        
        with col2:
            st.markdown("**Reference Motion Video**")
            ref_video = st.file_uploader(
                "Upload reference video (dance, action, etc.)",
                type=["mp4", "mov"],
                key="motion_ref"
            )
            if ref_video:
                st.video(ref_video)
        
        motion_type = st.selectbox(
            "Motion Type",
            ["video (full motion - max 30s)", "image (camera movement - max 10s)"]
        )
        
        if st.button("🎭 Transfer Motion", key="transfer_motion"):
            if not char_image or not ref_video:
                st.error("Please upload both character image and reference video")
            else:
                st.warning(
                    "⚠️ Full implementation requires uploading files to FAL storage. "
                    "Use FAL.ai directly: https://fal.ai/models/fal-ai/kling-video/v2.6/standard/motion-control"
                )


# ============================================================================
# TAB 4: VIDEO GENERATOR
# ============================================================================
with tab4:
    st.header("📹 Video Generator")
    st.markdown("Generate short videos from images or text prompts.")
    
    video_type = st.selectbox(
        "What would you like to create?",
        ["Image-to-Video (cinematic motion)", "Text-to-Video (full generation)"]
    )
    
    if video_type == "Image-to-Video (cinematic motion)":
        st.subheader("Transform Image into Video")
        st.markdown("Upload an image and describe the motion you want.")
        
        uploaded_img = st.file_uploader(
            "Upload image",
            type=["png", "jpg", "jpeg"],
            key="i2v_image"
        )
        
        if uploaded_img:
            st.image(uploaded_img, caption="Your Image", width=300)
            
            motion_prompt = st.text_area(
                "Describe the motion (e.g., 'Camera pans left, slow gentle motion')",
                height=80
            )
            
            if st.button("🎬 Generate Video", key="gen_i2v"):
                if not motion_prompt.strip():
                    st.error("Please describe the motion")
                else:
                    st.warning(
                        "⚠️ Video generation requires FAL credit usage. "
                        "This would cost ~0.5-2 credits per video (free tier: $10/mo = ~50 videos)"
                    )
                    st.info(
                        "Test at: https://fal.ai/models/fal-ai/kling-video/v2.6/standard\n"
                        "Upload your image and prompt!"
                    )
    
    else:
        st.subheader("Generate Video from Text")
        st.markdown("Describe a video and Kling will generate it.")
        
        text_prompt = st.text_area(
            "Describe your video",
            placeholder="e.g., 'A cat walking through a sunny garden, slow cinematic motion'",
            height=100
        )
        
        if st.button("🎬 Generate Video", key="gen_t2v"):
            if not text_prompt.strip():
                st.error("Please enter a video description")
            else:
                st.warning(
                    "⚠️ Text-to-video generation requires FAL credit usage."
                )
                st.info(
                    "📌 Test with Kling 2.6 at: https://fal.ai/models/fal-ai/kling-video/v2.6/standard"
                )


# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        "**Free Credits:** $10/month from FAL.ai\n"
        "**Est. Videos:** ~20-50 per month (depending on length)"
    )

with col2:
    st.markdown(
        "**Safety Features:** ✓ Built-in to FAL APIs\n"
        "**Artist Control:** ✓ Safety toggle in sidebar"
    )

with col3:
    st.markdown(
        "**Need Help?**\n"
        "- FAL.ai: https://fal.ai/docs\n"
        "- Streamlit: https://docs.streamlit.io"
    )

st.markdown(
    """
    <div style='text-align: center; padding: 20px; color: #666;'>
    <p>🎬 AI Character Animation Studio | Powered by FAL.ai + Streamlit | Built for Artists</p>
    </div>
    """,
    unsafe_allow_html=True
)
