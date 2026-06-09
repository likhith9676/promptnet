import streamlit as st
import fal_client
from supabase import create_client
import os

# 1. Page Configuration
st.set_page_config(page_title="PromptNet MVP", page_icon="🎬", layout="centered")

# 2. Hardcoded Credentials Bypass
SUPABASE_URL = "https://eqygmwwxkgxsjlygqxtz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVxeWdtd3d4a2d4c2pseWdxeHR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEwMzczNDMsImV4cCI6MjA5NjYxMzM0M30.UMo9yeblREC7WekrLLEv29SJltz6NkIYyw4WaGjt688"

# Explicitly set the environment variable for the Fal AI client
os.environ["FAL_KEY"] = "ba97bcc4-bcfd-4a64-95e9-d8b771732fae:0bac747c0bd994478367cdd66a5eed1b"

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Failed to initialize database: {e}")
    st.stop()

st.title("🎬 PromptNet")
st.caption("Type an idea, generate a short video, and share it with the world.")

# Create top tabs for navigation like a social media network
tab_create, tab_feed = st.tabs(["✨ Create Video", "🔥 Public Feed"])

# --- TAB 1: THE GENERATOR ---
with tab_create:
    st.subheader("What's on your mind?")
    user_prompt = st.text_input(
        "Describe your short video:", 
        placeholder="A cinematic drone shot of a futuristic cyberpunk city floating in clouds..."
    )
    
    # We set a simple text password here directly in the code
    access_password = st.text_input("Enter creator password to post:", type="password")
    
    if st.button("Generate & Post to Feed", type="primary"):
        if not user_prompt:
            st.warning("Please type a prompt first!")
        elif access_password != "create123":  # <--- YOUR PASSWORD IS NOW EXPLICITLY: create123
            st.error("Incorrect creator password. You can still view the Public Feed tab!")
        else:
            with st.spinner("🤖 AI is processing your video (takes about 15-20 seconds)..."):
                try:
                    # Using Wan 2.6 text-to-video (high quality and ultra-budget cost)
                    handler = fal_client.submit(
                        "fal-ai/wan/2.6/text-to-video",
                        arguments={
                            "prompt": user_prompt,
                            "size": "480x854" # Perfect 9:16 vertical ratio for mobile shorts
                        }
                    )
                    result = handler.get()
                    video_url = result["video"]["url"]
                    
                    # Insert the new video asset directly into the Supabase global feed
                    supabase.table("posts").insert({
                        "prompt": user_prompt,
                        "video_url": video_url,
                        "likes": 0
                    }).execute()
                    
                    st.success("🎉 Successfully generated and posted!")
                    st.video(video_url)
                    
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
            st.info("The feed is empty! Be the first to generate a video.")
        
        for post in posts:
            # Container for each social media card
            with st.container(border=True):
                st.markdown(f"💡 **\"{post['prompt']}\"**")
                st.video(post['video_url'])
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    # Like interaction
                    if st.button(f"❤️ {post['likes']}", key=f"like_{post['id']}"):
                        new_likes = post['likes'] + 1
                        supabase.table("posts").update({"likes": new_likes}).eq("id", post['id']).execute()
                        st.rerun()
                with col2:
                    st.caption(f"Posted on {post['created_at'][:10]}")
                    
    except Exception as e:
        st.error(f"Could not load feed: {e}")
