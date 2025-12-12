import os
import sys
import google.generativeai as genai
from PIL import Image

def analyze_screenshots_with_ai(screenshot_dir, output="transcript.txt"):
    """
    Analyze screenshots using Google Gemini Vision API to generate step-by-step instructions.
    """
    # Get API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        # Create .env template if it doesn't exist
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        if not os.path.exists(env_path):
            with open(env_path, "w") as f:
                f.write("# Get your free API key from: https://aistudio.google.com/apikey\n")
                f.write("GEMINI_API_KEY=your_api_key_here\n")
        raise ValueError(f"Gemini API key not found. Please add it to: {env_path}")
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Get all screenshots in order
    screenshots = sorted([
        f for f in os.listdir(screenshot_dir) 
        if f.startswith("screenshot_") and f.endswith(".png")
    ])
    
    if not screenshots:
        raise FileNotFoundError("No screenshots found to analyze")
    
    # Load images
    images = []
    for screenshot in screenshots[:15]:  # Gemini can handle more images
        img_path = os.path.join(screenshot_dir, screenshot)
        img = Image.open(img_path)
        images.append(img)
    
    # Build the prompt
    prompt = f"""You are analyzing {len(images)} screenshots from a screen recording tutorial.

Your task: Create a clear step-by-step guide describing what's happening in each screenshot.

CRITICAL FORMAT REQUIREMENTS:
- Start each screenshot description with "Step N:" (where N is the screenshot number 1, 2, 3...)
- Describe what the user is doing in that specific screenshot
- Be clear and concise (1-2 sentences per step)
- Focus on the actions visible in each image

Example format:
Step 1: User opens the application from the desktop
Step 2: User clicks on the "New Project" button in the top menu
Step 3: User enters the project name in the text field
Step 4: User selects the project location using the Browse button

Generate the step-by-step guide now:"""
    
    # Call Gemini with all images
    response = model.generate_content([prompt] + images)
    
    instructions = response.text
    
    with open(output, "w", encoding="utf-8") as f:
        f.write(instructions)
    
    return instructions

def transcribe_audio(audio_path="assets/audio.wav", output="assets/transcript.txt"):
    """
    Legacy function - redirects to screenshot analysis.
    For compatibility with existing code.
    """
    # Determine screenshot directory from output path
    screenshot_dir = os.path.dirname(output)
    
    try:
        # Load environment variables
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        load_dotenv(env_path)
        
        result = analyze_screenshots_with_ai(screenshot_dir, output)
        return result
    except Exception as e:
        # Create placeholder
        with open(output, "w", encoding="utf-8") as f:
            f.write("[AI Analysis not available - Manual transcription mode]\n\n")
            f.write("To enable AI-powered screenshot analysis with Google Gemini:\n")
            f.write("1. Get a FREE API key from https://aistudio.google.com/apikey\n")
            f.write("2. Add it to the .env file in the project root:\n")
            f.write("   GEMINI_API_KEY=your_key_here\n")
            f.write("3. Install required package: pip install google-generativeai\n")
            f.write(f"\nError: {str(e)}\n")
        raise Exception(f"AI analysis unavailable: {str(e)}")
