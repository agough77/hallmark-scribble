import os
import sys
import subprocess
from pathlib import Path

def get_config_path():
    """Get the path to config.txt in a persistent location"""
    # If running as EXE, store config next to the executable
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        app_dir = os.path.dirname(sys.executable)
    else:
        # Running as script
        app_dir = os.path.dirname(os.path.dirname(__file__))
    
    return os.path.join(app_dir, "config.txt")

def enhance_transcript_for_narration(transcript_text, scribble_dir):
    """
    Use AI to enhance the transcript into a proper narration script
    that describes what's happening in the video
    """
    try:
        import google.generativeai as genai
        
        # Get API key from environment or config
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            # Try reading from config file
            config_path = get_config_path()
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    for line in f:
                        if line.startswith('GEMINI_API_KEY='):
                            api_key = line.split('=', 1)[1].strip()
                            break
        
        if not api_key:
            # Fallback to original transcript if no API key
            return transcript_text
        
        # Read action logs if available
        actions_log = ""
        actions_path = os.path.join(scribble_dir, "actions.log")
        if os.path.exists(actions_path):
            with open(actions_path, 'r', encoding='utf-8') as f:
                actions_log = f.read()
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        actions_context = f"\n\nUser actions logged during recording:\n{actions_log}" if actions_log else ""
        
        prompt = f"""You are creating a professional video narration for a screen recording tutorial.

Speech transcript (what was said during recording):
{transcript_text}
{actions_context}

Create a narration script that:
1. DESCRIBES THE VISUAL ACTIONS: "Now I'm clicking on...", "Next, I navigate to...", "Here I'm typing..."
2. Explains WHAT is being done and WHY
3. Mentions specific UI elements, buttons, menus being interacted with
4. Uses second-person ("you") or first-person ("I") perspective
5. Flows naturally with the video timing

Focus on VISUAL DESCRIPTION - what viewers see happening on screen, not just what was said.
Keep it conversational and tutorial-style. Write ONLY the narration script."""

        response = model.generate_content(prompt)
        enhanced_text = response.text.strip()
        
        return enhanced_text if enhanced_text else transcript_text
        
    except Exception as e:
        print(f"AI enhancement failed, using original transcript: {e}")
        return transcript_text

def add_narration_to_video(scribble_dir, transcript_path=None, output_name="narrated_video.mp4"):
    """
    Generate AI narration from transcript and merge with video using FFmpeg and edge-tts
    
    Args:
        scribble_dir: Directory containing recording.mp4 and transcript.txt
        transcript_path: Path to transcript file (optional, defaults to scribble_dir/transcript.txt)
        output_name: Name for the output narrated video file
    
    Returns:
        Path to the narrated video file
    """
    
    if transcript_path is None:
        transcript_path = os.path.join(scribble_dir, "transcript.txt")
    
    # Check if transcript exists
    if not os.path.exists(transcript_path):
        raise FileNotFoundError(f"Transcript not found at {transcript_path}")
    
    # Read transcript
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript_text = f.read().strip()
    
    if not transcript_text:
        raise ValueError("Transcript is empty")
    
    # Clean up markdown formatting and special characters for TTS
    import re
    
    # Remove markdown formatting
    narration_script = transcript_text
    narration_script = re.sub(r'\*\*([^*]+)\*\*', r'\1', narration_script)  # Remove bold **text**
    narration_script = re.sub(r'\*([^*]+)\*', r'\1', narration_script)      # Remove italic *text*
    narration_script = re.sub(r'`([^`]+)`', r'\1', narration_script)        # Remove code `text`
    narration_script = re.sub(r'#{1,6}\s+', '', narration_script)           # Remove headers ###
    narration_script = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', narration_script)  # Remove links [text](url)
    narration_script = re.sub(r'^\s*[-*+]\s+', '', narration_script, flags=re.MULTILINE)  # Remove bullet points
    narration_script = re.sub(r'^\s*\d+\.\s+', '', narration_script, flags=re.MULTILINE)  # Remove numbered lists
    
    # Clean up extra whitespace
    narration_script = re.sub(r'\n{3,}', '\n\n', narration_script)  # Max 2 newlines
    narration_script = narration_script.strip()
    
    print(f"Cleaned narration script: {narration_script[:150]}...")
    
    # Paths
    video_path = os.path.join(scribble_dir, "recording.mp4")
    narration_audio_path = os.path.join(scribble_dir, "narration.mp3")
    output_video_path = os.path.join(scribble_dir, output_name)
    
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found at {video_path}")
    
    # Generate narration audio using edge-tts (Microsoft Edge TTS - free and high quality)
    try:
        import edge_tts
        import asyncio
        
        print("✓ edge-tts module imported successfully")
        
        async def generate_audio():
            # Use natural voice with faster speaking rate
            # en-US-AriaNeural (female), en-US-GuyNeural (male), en-US-JennyNeural (female)
            # Add rate parameter: +20% faster for more natural pacing
            communicate = edge_tts.Communicate(
                narration_script, 
                "en-US-AriaNeural",
                rate="+20%"
            )
            await communicate.save(narration_audio_path)
        
        try:
            asyncio.run(generate_audio())
            print(f"✓ Narration audio generated with edge-tts: {narration_audio_path}")
        except Exception as tts_error:
            # If edge-tts fails, try gTTS with faster speed
            error_msg = str(tts_error).lower()
            print(f"edge-tts error: {tts_error}")
            if "401" in error_msg or "invalid response" in error_msg or "wss://" in error_msg:
                print("Falling back to gTTS due to edge-tts connection error...")
                try:
                    from gtts import gTTS
                    # Use gTTS with slower=False for faster, more natural speech
                    tts = gTTS(text=narration_script, lang='en', slow=False, tld='com')
                    tts.save(narration_audio_path)
                    print(f"✓ Narration audio generated with gTTS (fallback): {narration_audio_path}")
                    
                    # Speed up the audio by 15% using FFmpeg
                    temp_path = narration_audio_path.replace(".mp3", "_temp.mp3")
                    os.rename(narration_audio_path, temp_path)
                    
                    ffmpeg_path_local = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ffmpeg", "bin", "ffmpeg.exe")
                    subprocess.run([
                        ffmpeg_path_local,
                        "-i", temp_path,
                        "-filter:a", "atempo=1.15",  # Speed up 15%
                        "-y",
                        narration_audio_path
                    ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                    
                    os.remove(temp_path)
                except ImportError as gtts_err:
                    raise ImportError(f"Both edge-tts and gTTS failed. gTTS error: {gtts_err}. Install gTTS: pip install gtts")
            else:
                raise tts_error
        
    except ImportError as import_err:
        raise ImportError(f"edge-tts module not found: {import_err}. Install with: pip install edge-tts")
    
    # Get video duration to check if we need to adjust narration speed
    ffmpeg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ffmpeg", "bin", "ffmpeg.exe")
    
    # Merge narration with video
    # Strategy: Add narration audio to video with volume boost
    try:
        # Try adding audio with volume normalization
        result = subprocess.run(
            [
                ffmpeg_path,
                "-i", video_path,
                "-i", narration_audio_path,
                "-filter_complex", "[1:a]volume=2.0[narr];[narr]apad[aout]",  # Boost volume 2x and pad
                "-map", "0:v",
                "-map", "[aout]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",  # Match video length
                "-y",
                output_video_path
            ],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        if result.returncode != 0:
            # Fallback: simple audio replacement
            result = subprocess.run(
                [
                    ffmpeg_path,
                    "-i", video_path,
                    "-i", narration_audio_path,
                    "-map", "0:v",
                    "-map", "1:a",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-shortest",
                    "-y",
                    output_video_path
                ],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")
        
        return output_video_path
        
    except Exception as e:
        raise Exception(f"Failed to merge narration with video: {str(e)}")


def list_available_voices():
    """List all available edge-tts voices"""
    try:
        import edge_tts
        import asyncio
        
        async def get_voices():
            voices = await edge_tts.list_voices()
            return voices
        
        voices = asyncio.run(get_voices())
        
        # Filter to English voices
        en_voices = [v for v in voices if v['Locale'].startswith('en-')]
        
        return [
            {
                'name': v['ShortName'],
                'gender': v['Gender'],
                'locale': v['Locale']
            }
            for v in en_voices
        ]
    except ImportError:
        return []
