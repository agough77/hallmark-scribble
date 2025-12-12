import os
from PIL import Image
import base64
from io import BytesIO

def create_guide(transcript_path="assets/transcript.txt", actions_path="assets/actions.log", output="assets/guide.md"):
    """Generate a visual how-to guide with screenshots and AI-generated instructions"""
    
    # Get the directory containing the files
    guide_dir = os.path.dirname(output)
    
    # Read transcript (AI-generated instructions)
    if not os.path.exists(transcript_path):
        transcript_text = "[No AI analysis available - run Generate Transcript first]\n"
    else:
        with open(transcript_path, "r", encoding="utf-8") as t:
            transcript_text = t.read()
    
    # Read action log
    if not os.path.exists(actions_path):
        actions = []
    else:
        with open(actions_path, "r") as a:
            actions = [line.strip() for line in a.readlines() if line.strip() and not line.startswith('#')]
    
    # Get all screenshots in chronological order
    screenshots = []
    if os.path.exists(guide_dir):
        screenshots = sorted([
            f for f in os.listdir(guide_dir) 
            if f.startswith("screenshot_") and f.endswith(".png")
        ])
    
    # Build the visual guide
    with open(output, "w", encoding="utf-8") as f:
        f.write("# Screen Recording How-To Guide\n\n")
        f.write(f"*Generated from {len(screenshots)} screenshots*\n\n")
        f.write("---\n\n")
        
        # AI-Generated Instructions Section
        f.write("## 📝 AI-Generated Instructions\n\n")
        f.write(transcript_text)
        f.write("\n\n---\n\n")
        
        # Visual Step-by-Step with Screenshots
        f.write("## 🖼️ Visual Step-by-Step\n\n")
        
        if screenshots:
            for i, screenshot in enumerate(screenshots, 1):
                screenshot_path = os.path.join(guide_dir, screenshot)
                
                # Find corresponding action from log
                action_desc = ""
                timestamp_str = screenshot.replace("screenshot_", "").replace(".png", "")
                try:
                    timestamp = float(timestamp_str)
                    # Find closest action
                    for action in actions:
                        if action.startswith(timestamp_str[:10]):  # Match first 10 chars of timestamp
                            parts = action.split(" ", 2)
                            if len(parts) >= 3:
                                action_desc = parts[2]  # Get action details
                            break
                except:
                    pass
                
                f.write(f"### Step {i}\n\n")
                if action_desc:
                    f.write(f"**Action:** {action_desc}\n\n")
                
                # Embed screenshot as relative path
                rel_screenshot = screenshot  # Since guide.md is in same dir as screenshots
                f.write(f"![Step {i}]({rel_screenshot})\n\n")
                f.write("---\n\n")
        else:
            f.write("*No screenshots captured during this recording*\n\n")
        
        # Raw Action Log Section
        f.write("## 📋 Detailed Action Log\n\n")
        f.write("```\n")
        if actions:
            for action in actions:
                f.write(f"{action}\n")
        else:
            f.write("[No actions logged]\n")
        f.write("```\n")
