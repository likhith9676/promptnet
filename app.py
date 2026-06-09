import streamlit as st
import fal_client
from supabase import create_client
import os

# 1. Page Configuration
st.set_page_config(page_title="PromptNet MVP", page_icon="📸", layout="centered")

# 2. Hardcoded Credentials Bypass
SUPABASE_URL = "https://eqygmwwxkgxsjlygqxtz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVxeWdtd3d4a2d4c2pseWdxeHR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEwMzczNDMsImV4cCI6MjA5NjYxMzM0M30.UMo9yeblREC7WekrLLEv29SJltz6NkIYyw4WaGjt688"

# Explicitly set the environment variable for the Fal AI client
os.environ["FAL_KEY"] = "ba97bcc4-bcfd-4a64-95e9-d8b771732fae:0bac747c0bd994478367cdd66a5eed1b"

# Create database connection safely
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Failed to initialize database client connection: {e}")
    st.stop()

st.title("📸 PromptNet")
st.caption("Type an idea, generate a stunning AI image, and share it with the world.")

# Create top tabs for navigation like a social media network
tab_create, tab_feed = st.tabs(["✨ Create Image", "🔥 Public Feed"])

# --- TAB 1: THE GENERATOR ---
with tab_create:
    st.subheader("What's on your mind?")
    user_prompt = st.text_input(
        "Describe your image:", 
        placeholder="A cinematic drone shot of a futuristic cyberpunk city floating in clouds..."
    )
    
    if st.button("Generate & Post to Feed", type="primary"):
        if not user_prompt:
            st.warning("Please type a prompt first!")
        else:
            with st.spinner("🤖 AI is painting your image (takes about 2 seconds)..."):
                try:
                    # Using Flux Schnell (Ultra-fast, beautiful, and practically free)
                    handler = fal_client.submit(
                        "fal-ai/flux/schnell",
                        arguments={
                            "prompt": user_prompt,
                            "image_size": "square_hd", # Options: square_hd, landscape_hd, portrait_hd
                            "num_inference_steps": 4,
                            "sync_mode": True
                        }
                    )
                    result = handler.get()
                    image_url = result["images"][0]["url"]
                    
                    # Insert the new image asset directly into your Supabase global table
                    # Note: We reuse the 'video_url' column to hold the image URL so your DB schema doesn't break!
                    supabase.table("posts").insert({
                        "prompt": user_prompt,
                        "video_url": image_url,
                        "likes": 0
                    }).execute()
                    
                    st.success("🎉 Successfully generated and posted!")
                    st.image(image_url, use_column_width=True)
                    
                except Exception as e:
                    st.error(f"Generation failed: {e}")

# --- TAB 2: THE SOCIAL FEED ---
with tab_feed:
    st.subheader("Community Masterpieces")
    
    try:
        # Fetch the latest posts from database (newest first)
        response = supabase.table("posts").select("*").order("created_at", desc=True).execute()
        posts = response.data
        
        if not posts:
            st.info("The feed is empty! Be the first to generate an image.")
        
        for post in posts:
            # Container card layout for each social media post
            with st.container(border=True):
                st.markdown(f"💡 **\"{post['prompt']}\"**")
                
                # Render as an image instead of a video
                st.image(post['video_url'], use_column_width=True)
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    # Interactive Like system updates the row count in real-time
                    if st.button(f"❤️ {post['likes']}", key=f"like_{post['id']}"):
                        new_likes = post['likes'] + 1
                        supabase.table("posts").update({"likes": new_likes}).eq("id", post['id']).execute()
                        st.rerun()
                with col2:
                    st.caption(f"Posted on {post['created_at'][:10]}")
                    
    except Exception as e:
        st.error(f"Could not load feed: {e}")
