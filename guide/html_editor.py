import os
import json
import logging
from urllib.parse import quote

def create_html_editor(scribble_dir):
    """Create an interactive HTML editor for the guide"""
    
    # Normalize path for JavaScript (use forward slashes and escape)
    scribble_dir_normalized = scribble_dir.replace('\\', '/')
    scribble_dir_escaped = scribble_dir.replace('\\', '\\\\')
    
    # Get files
    transcript_path = os.path.join(scribble_dir, "transcript.txt")
    actions_path = os.path.join(scribble_dir, "actions.log")
    video_path = os.path.join(scribble_dir, "recording.mp4")
    notes_path = os.path.join(scribble_dir, "notes.json")
    
    # Check if this is video mode
    is_video_mode = os.path.exists(video_path)
    
    # Read transcript
    if os.path.exists(transcript_path):
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript = f.read()
    else:
        transcript = "[No transcript generated yet]"
    
    # Read saved notes (which includes step metadata)
    saved_notes = []
    if os.path.exists(notes_path):
        try:
            with open(notes_path, "r", encoding="utf-8") as f:
                saved_notes = json.load(f)
            logging.info(f"Loaded {len(saved_notes)} saved notes from {notes_path}")
            logging.info(f"Saved notes content: {saved_notes}")
        except Exception as e:
            logging.error(f"Error loading notes: {e}")
            saved_notes = []
    else:
        logging.info(f"Notes file does not exist: {notes_path}")
    
    # Get screenshots from disk
    screenshots = sorted([
        f for f in os.listdir(scribble_dir)
        if f.startswith("screenshot_") and f.endswith(".png")
    ])
    
    # If we have saved notes with metadata, OR more notes than screenshots, use them to reconstruct all steps
    # Otherwise just use screenshot files
    if saved_notes and (len(saved_notes) > len(screenshots) or any(note.get('type') or note.get('imageSrc') for note in saved_notes)):
        # We have metadata or extra steps, use saved notes to build step list
        all_steps = saved_notes
        logging.info(f"Using {len(all_steps)} steps from saved metadata (have {len(saved_notes)} notes vs {len(screenshots)} screenshots)")
    else:
        # No metadata, build from screenshot files only
        all_steps = [{'type': 'screenshot', 'file': f, 'note': ''} for f in screenshots]
        logging.info(f"Using {len(all_steps)} steps from screenshot files")
    
    # Read actions
    if os.path.exists(actions_path):
        with open(actions_path, "r") as f:
            actions = f.readlines()
    else:
        actions = []
    
    # Parse AI transcript into steps (split by common delimiters)
    transcript_steps = []
    if transcript and transcript != "[No transcript generated yet]":
        # Check if transcript contains error messages or setup instructions
        error_keywords = [
            "AI Analysis not available",
            "Manual transcription mode",
            "enable AI-powered",
            "Get a FREE API key",
            "Error:",
            "No screenshots found",
            "GEMINI_API_KEY"
        ]
        
        # Skip transcript parsing if it contains error messages
        is_error_message = any(keyword in transcript for keyword in error_keywords)
        
        if not is_error_message:
            # Try to split by step numbers or paragraphs
            import re
            # Look for numbered steps like "1.", "Step 1:", etc.
            step_pattern = r'(?:^|\n)(?:\d+\.|Step \d+:?|##\s+Step \d+)'
            parts = re.split(step_pattern, transcript, flags=re.MULTILINE)
            # Filter out empty parts and clean up
            transcript_steps = [part.strip() for part in parts if part.strip()]
            
            # If no clear steps found, split by paragraphs
            if len(transcript_steps) <= 1:
                transcript_steps = [p.strip() for p in transcript.split('\n\n') if p.strip()]
    
    # Build HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hallmark Scribble - Guide Editor</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        
        h1 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 32px;
        }}
        
        .subtitle {{
            color: #666;
            margin-bottom: 30px;
            font-size: 16px;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section-title {{
            font-size: 24px;
            color: #444;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }}
        
        .title-editor {{
            width: 100%;
            padding: 15px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 28px;
            font-weight: bold;
            color: #333;
            margin-bottom: 20px;
            font-family: inherit;
        }}
        
        .title-editor:focus {{
            outline: none;
            border-color: #4285f4;
        }}
        
        .transcript-editor {{
            width: 100%;
            min-height: 300px;
            padding: 20px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            line-height: 1.6;
            font-family: inherit;
            resize: vertical;
        }}
        
        .transcript-editor:focus {{
            outline: none;
            border-color: #4285f4;
        }}
        
        .screenshots-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-top: 20px;
        }}
        
        .screenshot-item {{
            background: #fafafa;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            transition: all 0.3s;
            position: relative;
            cursor: move;
        }}
        
        .screenshot-item:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            border-color: #4285f4;
        }}
        
        .screenshot-item.dragging {{
            opacity: 0.5;
            transform: scale(0.95);
        }}
        
        .drag-handle {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: #4285f4;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 12px;
            cursor: move;
            z-index: 10;
        }}
        
        .delete-btn {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: #ea4335;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
            z-index: 10;
        }}
        
        .delete-btn:hover {{
            background: #c5221f;
        }}
        
        .upload-section {{
            margin: 20px 0;
            padding: 20px;
            background: #f0f7ff;
            border: 2px dashed #4285f4;
            border-radius: 8px;
            text-align: center;
        }}
        
        .upload-btn {{
            background: #4285f4;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            margin: 10px;
        }}
        
        .upload-btn:hover {{
            background: #357ae8;
        }}
        
        .screenshot-number {{
            font-weight: bold;
            color: #4285f4;
            margin-bottom: 10px;
            font-size: 18px;
        }}
        
        .screenshot-img {{
            width: 100%;
            border-radius: 6px;
            margin-bottom: 15px;
            cursor: pointer;
            transition: transform 0.2s;
            display: block;
        }}
        
        .screenshot-img:hover {{
            transform: scale(1.02);
        }}
        
        .edit-btn {{
            background: #ff6b6b;
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-bottom: 10px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        
        .edit-btn:hover {{
            background: #ff5252;
        }}
        
        .screenshot-note {{
            width: 100%;
            min-height: 120px;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            background: white;
            overflow-y: auto;
            line-height: 1.6;
        }}
        
        .screenshot-note:focus {{
            outline: none;
            border-color: #4285f4;
        }}
        
        .rich-text-toolbar {{
            background: #f8f9fa;
            border: 1px solid #ddd;
            border-bottom: none;
            border-radius: 6px 6px 0 0;
            padding: 8px;
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
            align-items: center;
        }}
        
        .format-btn {{
            background: white;
            border: 1px solid #ccc;
            border-radius: 3px;
            padding: 6px 10px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
            min-width: 32px;
            height: 32px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }}
        
        .format-btn:hover {{
            background: #e9ecef;
            border-color: #999;
        }}
        
        .format-btn:active {{
            background: #dee2e6;
        }}
        
        .format-btn.active {{
            background: #4285f4;
            color: white;
            border-color: #4285f4;
        }}
        
        .toolbar-separator {{
            width: 1px;
            height: 24px;
            background: #ddd;
            margin: 0 5px;
        }}
        
        .color-input {{
            width: 32px;
            height: 32px;
            border: 1px solid #ccc;
            border-radius: 3px;
            cursor: pointer;
        }}
        
        .actions-log {{
            background: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            max-height: 400px;
            overflow-y: auto;
        }}
        
        .action-line {{
            padding: 4px 0;
            color: #555;
        }}
        
        .buttons {{
            display: flex;
            gap: 15px;
            margin-top: 30px;
            padding-top: 30px;
            border-top: 2px solid #e0e0e0;
        }}
        
        button {{
            padding: 12px 24px;
            font-size: 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s;
        }}
        
        .btn-primary {{
            background: #4285f4;
            color: white;
        }}
        
        .btn-primary:hover {{
            background: #357ae8;
            box-shadow: 0 2px 8px rgba(66, 133, 244, 0.3);
        }}
        
        .btn-secondary {{
            background: #f1f3f4;
            color: #333;
        }}
        
        .btn-secondary:hover {{
            background: #e8eaed;
        }}
        
        .btn-success {{
            background: #34a853;
            color: white;
        }}
        
        .btn-success:hover {{
            background: #2d9348;
        }}
        
        .modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
            z-index: 1000;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}
        
        .modal-content {{
            position: relative;
            max-width: 95%;
            max-height: 95%;
            display: flex;
            flex-direction: column;
            background: white;
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .annotation-toolbar {{
            background: #2c3e50;
            padding: 15px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            align-items: center;
        }}
        
        .tool-btn {{
            background: #34495e;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }}
        
        .tool-btn:hover {{
            background: #4a6278;
        }}
        
        .tool-btn.active {{
            background: #3498db;
            box-shadow: 0 0 10px rgba(52, 152, 219, 0.5);
        }}
        
        .color-picker {{
            width: 40px;
            height: 40px;
            border: 2px solid white;
            border-radius: 4px;
            cursor: pointer;
        }}
        
        .size-slider {{
            width: 120px;
        }}
        
        .canvas-container {{
            position: relative;
            flex: 1;
            overflow: auto;
            background: #ecf0f1;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            max-height: calc(100vh - 150px);
        }}
        
        #annotationCanvas {{
            cursor: crosshair;
            background: white;
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }}
        
        .close-modal {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: #e74c3c;
            color: white;
            border: none;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 20px;
            z-index: 10;
        }}
        
        .close-modal:hover {{
            background: #c0392b;
        }}
        
        .modal img {{
            max-width: 90%;
            max-height: 90%;
            border-radius: 8px;
        }}
        
        .toast {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #333;
            color: white;
            padding: 16px 24px;
            border-radius: 8px;
            display: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10000;
            font-size: 16px;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <div>
                <h1>📝 Hallmark Scribble - Guide Editor</h1>
                <p class="subtitle">Edit your guide title, customize screenshot notes, and export to HTML or Markdown</p>
            </div>
            <button onclick="window.location.href='/'" style="padding: 12px 24px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: 600;">⬅ Back to Home</button>
        </div>
        
        <div class="section">
            <h2 class="section-title">📋 Guide Title</h2>
            <input type="text" class="title-editor" id="titleEditor" placeholder="Enter your guide title..." value="How-To Guide">
        </div>
        

        <div class="section">
            <h2 class="section-title">🖼️ Screenshots & Annotations</h2>
            <p style="color: #666; margin-bottom: 15px;">Drag screenshots to reorder, click to view full size, or add new ones manually.</p>
            
            <div class="upload-section">
                <h3 style="margin-bottom: 10px;">➕ Add New Step</h3>
                <input type="file" id="fileInput" accept="image/*" style="display: none;">
                <button class="upload-btn" onclick="document.getElementById('fileInput').click()">📁 Upload Image</button>
                <button class="upload-btn" onclick="addTextStep()">📝 Add Text</button>
                <p style="color: #666; margin-top: 10px; font-size: 14px;">Upload images or add text-only steps</p>
            </div>
            
            <div class="screenshots-grid" id="screenshotsGrid">
"""
    
    # Add all steps (screenshots, uploads, and text-only)
    for i, step in enumerate(all_steps, 1):
        step_type = step.get('type', 'screenshot')
        step_note = step.get('note', '')
        
        logging.info(f"Rendering step {i}: type={step_type}, note length={len(step_note) if step_note else 0}")
        
        # Handle different step types
        if step_type == 'text':
            # Text-only step (no image)
            html_content += f"""
                <div class="screenshot-item" draggable="true" data-step="{i}" data-type="text">
                    <div class="drag-handle">⋮⋮ Drag</div>
                    <button class="delete-btn" onclick="deleteStep(this)">🗑️ Delete</button>
                    <div class="screenshot-number">Step {i} - Text Only</div>
                    
                    <div class="rich-text-toolbar" data-step="{i}">
                        <button class="format-btn" onclick="formatText('bold', {i})" title="Bold"><b>B</b></button>
                        <button class="format-btn" onclick="formatText('italic', {i})" title="Italic"><i>I</i></button>
                        <button class="format-btn" onclick="formatText('underline', {i})" title="Underline"><u>U</u></button>
                        <button class="format-btn" onclick="formatText('strikeThrough', {i})" title="Strikethrough"><s>S</s></button>
                        <div class="toolbar-separator"></div>
                        <button class="format-btn" onclick="formatText('insertUnorderedList', {i})" title="Bullet List">• List</button>
                        <button class="format-btn" onclick="formatText('insertOrderedList', {i})" title="Numbered List">1. List</button>
                        <div class="toolbar-separator"></div>
                        <button class="format-btn" onclick="formatText('justifyLeft', {i})" title="Align Left">⬅</button>
                        <button class="format-btn" onclick="formatText('justifyCenter', {i})" title="Align Center">⬌</button>
                        <button class="format-btn" onclick="formatText('justifyRight', {i})" title="Align Right">➡</button>
                        <div class="toolbar-separator"></div>
                        <input type="color" class="color-input" onchange="formatTextColor(this.value, {i})" title="Text Color" value="#000000">
                        <button class="format-btn" onclick="createLink({i})" title="Insert Link">🔗</button>
                        <button class="format-btn" onclick="formatText('removeFormat', {i})" title="Clear Formatting">✕</button>
                    </div>
                    
                    <div class="screenshot-note" contenteditable="true" data-step="{i}" id="note-{i}" onblur="saveNoteContent({i})">{step_note}</div>
                </div>
"""
        elif step_type == 'upload':
            # Manually uploaded image
            image_src = step.get('imageSrc', '')
            html_content += f"""
                <div class="screenshot-item" draggable="true" data-step="{i}" data-type="upload">
                    <div class="drag-handle">⋮⋮ Drag</div>
                    <button class="delete-btn" onclick="deleteStep(this)">🗑️ Delete</button>
                    <div class="screenshot-number">Step {i} - Uploaded</div>
                    <button class="edit-btn" onclick="generateStepInstructionsDataURL('{image_src}', {i})" style="background: #27ae60;">🤖 Generate AI Instructions</button>
                    <img src="{image_src}" class="screenshot-img" id="img-{i}" onclick="showImage(this.src)" alt="Screenshot {i}">
                    
                    <div class="rich-text-toolbar" data-step="{i}">
                        <button class="format-btn" onclick="formatText('bold', {i})" title="Bold"><b>B</b></button>
                        <button class="format-btn" onclick="formatText('italic', {i})" title="Italic"><i>I</i></button>
                        <button class="format-btn" onclick="formatText('underline', {i})" title="Underline"><u>U</u></button>
                        <button class="format-btn" onclick="formatText('strikeThrough', {i})" title="Strikethrough"><s>S</s></button>
                        <div class="toolbar-separator"></div>
                        <button class="format-btn" onclick="formatText('insertUnorderedList', {i})" title="Bullet List">• List</button>
                        <button class="format-btn" onclick="formatText('insertOrderedList', {i})" title="Numbered List">1. List</button>
                        <div class="toolbar-separator"></div>
                        <button class="format-btn" onclick="formatText('justifyLeft', {i})" title="Align Left">⬅</button>
                        <button class="format-btn" onclick="formatText('justifyCenter', {i})" title="Align Center">⬌</button>
                        <button class="format-btn" onclick="formatText('justifyRight', {i})" title="Align Right">➡</button>
                        <div class="toolbar-separator"></div>
                        <input type="color" class="color-input" onchange="formatTextColor(this.value, {i})" title="Text Color" value="#000000">
                        <button class="format-btn" onclick="createLink({i})" title="Insert Link">🔗</button>
                        <button class="format-btn" onclick="formatText('removeFormat', {i})" title="Clear Formatting">✕</button>
                    </div>
                    
                    <div class="screenshot-note" contenteditable="true" data-step="{i}" id="note-{i}" onblur="saveNoteContent({i})">{step_note}</div>
                </div>
"""
        else:
            # Screenshot from recording
            # Check if we have a file reference or can match to a screenshot
            if step.get('file'):
                screenshot_file = step.get('file')
            elif i <= len(screenshots):
                screenshot_file = screenshots[i-1]
            else:
                # No file and index beyond screenshots - treat as text-only
                html_content += f"""
                <div class="screenshot-item" draggable="true" data-step="{i}" data-type="text">
                    <div class="drag-handle">⋮⋮ Drag</div>
                    <button class="delete-btn" onclick="deleteStep(this)">🗑️ Delete</button>
                    <div class="screenshot-number">Step {i} - Text Only</div>
                    
                    <div class="rich-text-toolbar" data-step="{i}">
                        <button class="format-btn" onclick="formatText('bold', {i})" title="Bold"><b>B</b></button>
                        <button class="format-btn" onclick="formatText('italic', {i})" title="Italic"><i>I</i></button>
                        <button class="format-btn" onclick="formatText('underline', {i})" title="Underline"><u>U</u></button>
                        <button class="format-btn" onclick="formatText('strikeThrough', {i})" title="Strikethrough"><s>S</s></button>
                        <div class="toolbar-separator"></div>
                        <button class="format-btn" onclick="formatText('insertUnorderedList', {i})" title="Bullet List">• List</button>
                        <button class="format-btn" onclick="formatText('insertOrderedList', {i})" title="Numbered List">1. List</button>
                        <div class="toolbar-separator"></div>
                        <button class="format-btn" onclick="formatText('justifyLeft', {i})" title="Align Left">⬅</button>
                        <button class="format-btn" onclick="formatText('justifyCenter', {i})" title="Align Center">⬌</button>
                        <button class="format-btn" onclick="formatText('justifyRight', {i})" title="Align Right">➡</button>
                        <div class="toolbar-separator"></div>
                        <input type="color" class="color-input" onchange="formatTextColor(this.value, {i})" title="Text Color" value="#000000">
                        <button class="format-btn" onclick="createLink({i})" title="Insert Link">🔗</button>
                        <button class="format-btn" onclick="formatText('removeFormat', {i})" title="Clear Formatting">✕</button>
                    </div>
                    
                    <div class="screenshot-note" contenteditable="true" data-step="{i}" id="note-{i}" onblur="saveNoteContent({i})">{step_note}</div>
                </div>
"""
                continue
            
            screenshot_path = os.path.join(scribble_dir, screenshot_file).replace(chr(92), "/")
            encoded_path = quote(screenshot_path, safe='')
            
            html_content += f"""
                <div class="screenshot-item" draggable="true" data-step="{i}" data-type="screenshot">
                    <div class="drag-handle">⋮⋮ Drag</div>
                    <button class="delete-btn" onclick="deleteStep(this)">🗑️ Delete</button>
                    <div class="screenshot-number">Step {i}</div>
                    <button class="edit-btn" onclick="openAnnotationEditor('/api/editor/image/{encoded_path}', {i})">✏️ Edit & Annotate</button>
                    <button class="edit-btn" onclick="generateStepInstructions('{screenshot_path}', {i})" style="background: #27ae60;">🤖 Generate AI Instructions</button>
                    <img src="/api/editor/image/{encoded_path}" class="screenshot-img" id="img-{i}" onclick="showImage(this.src)" alt="Screenshot {i}">
                    
                    <div class="rich-text-toolbar" data-step="{i}">
                        <button class="format-btn" onclick="formatText('bold', {i})" title="Bold"><b>B</b></button>
                        <button class="format-btn" onclick="formatText('italic', {i})" title="Italic"><i>I</i></button>
                        <button class="format-btn" onclick="formatText('underline', {i})" title="Underline"><u>U</u></button>
                        <button class="format-btn" onclick="formatText('strikeThrough', {i})" title="Strikethrough"><s>S</s></button>
                        <div class="toolbar-separator"></div>
                        <button class="format-btn" onclick="formatText('insertUnorderedList', {i})" title="Bullet List">• List</button>
                        <button class="format-btn" onclick="formatText('insertOrderedList', {i})" title="Numbered List">1. List</button>
                        <div class="toolbar-separator"></div>
                        <button class="format-btn" onclick="formatText('justifyLeft', {i})" title="Align Left">⬅</button>
                        <button class="format-btn" onclick="formatText('justifyCenter', {i})" title="Align Center">⬌</button>
                        <button class="format-btn" onclick="formatText('justifyRight', {i})" title="Align Right">➡</button>
                        <div class="toolbar-separator"></div>
                        <input type="color" class="color-input" onchange="formatTextColor(this.value, {i})" title="Text Color" value="#000000">
                        <button class="format-btn" onclick="createLink({i})" title="Insert Link">🔗</button>
                        <button class="format-btn" onclick="formatText('removeFormat', {i})" title="Clear Formatting">✕</button>
                    </div>
                    
                    <div class="screenshot-note" contenteditable="true" data-step="{i}" id="note-{i}" onblur="saveNoteContent({i})">{step_note}</div>
                </div>
"""
    
    html_content += f"""
            </div>
        </div>
        

        <div class="buttons">
            <button class="btn-primary" onclick="saveChanges()">💾 Save Changes</button>
            <button class="btn-success" onclick="exportHTML()">📄 Export HTML Guide</button>
        </div>
    </div>
    
    <div class="modal" id="imageModal" onclick="closeModal()">
        <img id="modalImage" src="" alt="Full size">
    </div>
    
    <!-- Annotation Editor Modal -->
    <div class="modal" id="annotationModal">
        <div class="modal-content">
            <div class="annotation-toolbar">
                <button class="tool-btn active" data-tool="pen" onclick="selectTool('pen')">🖊️ Pen</button>
                <button class="tool-btn" data-tool="highlighter" onclick="selectTool('highlighter')">🖍️ Highlighter</button>
                <button class="tool-btn" data-tool="arrow" onclick="selectTool('arrow')">➡️ Arrow</button>
                <button class="tool-btn" data-tool="rectangle" onclick="selectTool('rectangle')">⬜ Box</button>
                <button class="tool-btn" data-tool="circle" onclick="selectTool('circle')">⭕ Circle</button>
                <button class="tool-btn" data-tool="text" onclick="selectTool('text')">🔤 Text</button>
                <button class="tool-btn" data-tool="crop" onclick="selectTool('crop')">✂️ Crop</button>
                <input type="color" id="colorPicker" class="color-picker" value="#ffff00" title="Pick color">
                <label style="color: white; margin-left: 10px;">Size:</label>
                <input type="range" id="sizeSlider" class="size-slider" min="1" max="20" value="3">
                <label for="opacitySlider" style="color: white; margin-left: 10px;">Opacity: 35%</label>
                <input type="range" id="opacitySlider" class="size-slider" min="5" max="100" value="35" title="Adjust transparency (100 = opaque, 5 = very transparent)">
                <button class="tool-btn" onclick="undoAnnotation()">↶ Undo</button>
                <button class="tool-btn" onclick="clearAnnotations()">🗑️ Clear All</button>
                <button class="tool-btn" style="background: #e67e22;" onclick="restoreOriginal()">↻ Restore Original</button>
                <button class="tool-btn" style="background: #27ae60;" onclick="saveAnnotatedImage()">💾 Save</button>
                <button class="tool-btn" style="background: #e74c3c; margin-left: 10px;" onclick="closeAnnotationEditor()">✕ Close</button>
            </div>
            <div class="canvas-container">
                <canvas id="annotationCanvas"></canvas>
            </div>
        </div>
    </div>
    
    <div class="toast" id="toast"></div>
    
    <script>
        const scribbleDir = '{scribble_dir.replace(chr(92), "/")}';
        let currentTool = 'pen';
        let isDrawing = false;
        let currentColor = '#ffff00'; // Yellow for highlighter
        let currentSize = 3;
        let currentOpacity = 1.0; // Default full opacity
        let canvas, ctx, originalImage, originalImageSrc;
        let currentStepIndex = null;
        let annotations = [];
        let startX, startY;
        let cropRect = null;
        let isCropping = false;
        
        function showImage(src) {{
            document.getElementById('modalImage').src = src;
            document.getElementById('imageModal').style.display = 'flex';
        }}
        
        function closeModal() {{
            document.getElementById('imageModal').style.display = 'none';
        }}
        
        function openAnnotationEditor(imageSrc, stepIndex) {{
            currentStepIndex = stepIndex;
            const modal = document.getElementById('annotationModal');
            canvas = document.getElementById('annotationCanvas');
            ctx = canvas.getContext('2d');
            
            // Reset crop flag
            window.isCroppedImage = false;
            
            // Store original image source for later reset
            originalImageSrc = imageSrc;
            
            // Load image with CORS enabled
            const img = new Image();
            img.crossOrigin = 'anonymous';  // Enable CORS to allow canvas export
            img.onload = function() {{
                // Calculate scaling to fit viewport
                const maxWidth = window.innerWidth * 0.8;
                const maxHeight = window.innerHeight * 0.7;
                
                let scale = Math.min(
                    maxWidth / img.width,
                    maxHeight / img.height,
                    1 // Don't scale up, only down
                );
                
                // Set canvas display size
                canvas.style.width = (img.width * scale) + 'px';
                canvas.style.height = (img.height * scale) + 'px';
                
                // Set actual canvas size (for high resolution)
                canvas.width = img.width;
                canvas.height = img.height;
                
                ctx.drawImage(img, 0, 0);
                originalImage = ctx.getImageData(0, 0, canvas.width, canvas.height);
                annotations = [];
                
                // Setup canvas event listeners after image is loaded and sized
                setupCanvas();
            }};
            img.src = imageSrc;
            
            modal.style.display = 'flex';
        }}
        
        function openAnnotationEditorFromDataURL(dataUrl, stepIndex) {{
            // This function handles uploaded images that are base64 data URLs
            // It works the same as openAnnotationEditor but uses the data URL directly
            openAnnotationEditor(dataUrl, stepIndex);
        }}
        
        function closeAnnotationEditor() {{
            document.getElementById('annotationModal').style.display = 'none';
        }}
        
        // Add global escape key handler
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') {{
                const annotationModal = document.getElementById('annotationModal');
                const imageModal = document.getElementById('imageModal');
                if (annotationModal && annotationModal.style.display === 'flex') {{
                    closeAnnotationEditor();
                }} else if (imageModal && imageModal.style.display === 'flex') {{
                    closeModal();
                }}
            }}
        }});
        
        function selectTool(tool) {{
            currentTool = tool;
            document.querySelectorAll('.tool-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelector(`[data-tool="${{tool}}"]`).classList.add('active');
        }}
        
        function setupCanvas() {{
            const colorPicker = document.getElementById('colorPicker');
            const sizeSlider = document.getElementById('sizeSlider');
            const opacitySlider = document.getElementById('opacitySlider');
            
            colorPicker.addEventListener('change', (e) => {{
                currentColor = e.target.value;
            }});
            
            sizeSlider.addEventListener('input', (e) => {{
                currentSize = parseInt(e.target.value);
            }});
            
            opacitySlider.addEventListener('input', (e) => {{
                currentOpacity = parseInt(e.target.value) / 100; // Convert 5-100 to 0.05-1.0
                // Update opacity display
                const opacityLabel = document.querySelector('label[for="opacitySlider"]');
                if (opacityLabel) {{
                    const percent = parseInt(e.target.value);
                    opacityLabel.textContent = `Opacity: ${{percent}}%`;
                }}
            }});
            
            canvas.addEventListener('mousedown', handleMouseDown);
            canvas.addEventListener('mousemove', handleMouseMove);
            canvas.addEventListener('mouseup', handleMouseUp);
            canvas.addEventListener('mouseout', handleMouseOut);
        }}
        
        function handleMouseDown(e) {{
            if (currentTool === 'crop') {{
                startCrop(e);
            }} else {{
                startDrawing(e);
            }}
        }}
        
        function handleMouseMove(e) {{
            if (currentTool === 'crop' && isCropping) {{
                updateCrop(e);
            }} else {{
                draw(e);
            }}
        }}
        
        function handleMouseUp(e) {{
            if (currentTool === 'crop' && isCropping) {{
                finishCrop(e);
            }} else {{
                stopDrawing(e);
            }}
        }}
        
        function handleMouseOut(e) {{
            if (currentTool === 'crop') {{
                // Don't cancel crop on mouse out
            }} else {{
                stopDrawing(e);
            }}
        }}
        
        // Helper function to get canvas coordinates accounting for scaling
        function getCanvasCoords(e) {{
            const rect = canvas.getBoundingClientRect();
            const scaleX = canvas.width / rect.width;
            const scaleY = canvas.height / rect.height;
            
            return {{
                x: (e.clientX - rect.left) * scaleX,
                y: (e.clientY - rect.top) * scaleY
            }};
        }}
        
        function startDrawing(e) {{
            isDrawing = true;
            const coords = getCanvasCoords(e);
            startX = coords.x;
            startY = coords.y;
            
            if (currentTool === 'text') {{
                const text = prompt('Enter text:');
                if (text) {{
                    ctx.font = `${{currentSize * 8}}px Arial`;
                    ctx.fillStyle = currentColor;
                    ctx.fillText(text, startX, startY);
                    annotations.push({{
                        tool: 'text',
                        text: text,
                        x: startX,
                        y: startY,
                        color: currentColor,
                        size: currentSize
                    }});
                }}
                isDrawing = false;
            }} else if (currentTool === 'pen' || currentTool === 'highlighter') {{
                ctx.beginPath();
                ctx.moveTo(startX, startY);
            }}
        }}
        
        function draw(e) {{
            if (!isDrawing) return;
            
            const coords = getCanvasCoords(e);
            const x = coords.x;
            const y = coords.y;
            
            if (currentTool === 'pen') {{
                ctx.strokeStyle = currentColor;
                ctx.lineWidth = currentSize;
                ctx.lineCap = 'round';
                ctx.lineJoin = 'round';
                ctx.globalAlpha = currentOpacity;
                ctx.lineTo(x, y);
                ctx.stroke();
            }} else if (currentTool === 'highlighter') {{
                ctx.strokeStyle = currentColor;
                ctx.lineWidth = currentSize * 5;
                ctx.lineCap = 'round';
                ctx.lineJoin = 'round';
                // Highlighter uses semi-transparent color to show text underneath
                // Lower opacity = more transparent, you can see text better
                ctx.globalAlpha = currentOpacity;
                ctx.lineTo(x, y);
                ctx.stroke();
            }} else if (currentTool === 'arrow' || currentTool === 'rectangle' || currentTool === 'circle') {{
                // Redraw from original + annotations
                ctx.putImageData(originalImage, 0, 0);
                redrawAnnotations();
                
                ctx.strokeStyle = currentColor;
                ctx.lineWidth = currentSize;
                ctx.globalAlpha = currentOpacity;
                ctx.lineCap = 'round';
                ctx.lineJoin = 'round';
                
                if (currentTool === 'arrow') {{
                    drawArrow(startX, startY, x, y);
                }} else if (currentTool === 'rectangle') {{
                    ctx.beginPath();
                    ctx.rect(startX, startY, x - startX, y - startY);
                    ctx.stroke();
                }} else if (currentTool === 'circle') {{
                    const radius = Math.sqrt(Math.pow(x - startX, 2) + Math.pow(y - startY, 2));
                    ctx.beginPath();
                    ctx.arc(startX, startY, radius, 0, 2 * Math.PI);
                    ctx.stroke();
                }}
            }}
        }}
        
        function stopDrawing(e) {{
            if (!isDrawing) return;
            isDrawing = false;
            
            const coords = getCanvasCoords(e);
            const x = coords.x;
            const y = coords.y;
            
            // Save annotation for shape tools and draw them permanently
            if (currentTool === 'arrow' || currentTool === 'rectangle' || currentTool === 'circle') {{
                // Draw the final shape
                ctx.strokeStyle = currentColor;
                ctx.lineWidth = currentSize;
                ctx.globalAlpha = currentOpacity;
                ctx.lineCap = 'round';
                ctx.lineJoin = 'round';
                
                if (currentTool === 'arrow') {{
                    drawArrow(startX, startY, x, y);
                }} else if (currentTool === 'rectangle') {{
                    ctx.beginPath();
                    ctx.rect(startX, startY, x - startX, y - startY);
                    ctx.stroke();
                }} else if (currentTool === 'circle') {{
                    const radius = Math.sqrt(Math.pow(x - startX, 2) + Math.pow(y - startY, 2));
                    ctx.beginPath();
                    ctx.arc(startX, startY, radius, 0, 2 * Math.PI);
                    ctx.stroke();
                }}
                
                // Save to annotations
                annotations.push({{
                    tool: currentTool,
                    startX: startX,
                    startY: startY,
                    endX: x,
                    endY: y,
                    color: currentColor,
                    size: currentSize,
                    opacity: currentOpacity
                }});
                
                // Update original image with the new annotation
                originalImage = ctx.getImageData(0, 0, canvas.width, canvas.height);
            }} else if (currentTool === 'pen' || currentTool === 'highlighter') {{
                // For continuous drawing, save the current canvas state
                originalImage = ctx.getImageData(0, 0, canvas.width, canvas.height);
            }}
            
            ctx.globalAlpha = 1;
        }}
        
        function drawArrow(fromX, fromY, toX, toY) {{
            const headLength = 20 + currentSize * 2;
            const angle = Math.atan2(toY - fromY, toX - fromX);
            
            // Draw line
            ctx.beginPath();
            ctx.moveTo(fromX, fromY);
            ctx.lineTo(toX, toY);
            ctx.stroke();
            
            // Draw arrowhead
            ctx.beginPath();
            ctx.moveTo(toX, toY);
            ctx.lineTo(toX - headLength * Math.cos(angle - Math.PI / 6), toY - headLength * Math.sin(angle - Math.PI / 6));
            ctx.moveTo(toX, toY);
            ctx.lineTo(toX - headLength * Math.cos(angle + Math.PI / 6), toY - headLength * Math.sin(angle + Math.PI / 6));
            ctx.stroke();
        }}
        
        function redrawAnnotations() {{
            annotations.forEach(ann => {{
                ctx.strokeStyle = ann.color;
                ctx.lineWidth = ann.size;
                ctx.globalAlpha = ann.opacity || 1; // Use saved opacity, default to 1 for old annotations
                ctx.lineCap = 'round';
                ctx.lineJoin = 'round';
                
                if (ann.tool === 'arrow') {{
                    drawArrow(ann.startX, ann.startY, ann.endX, ann.endY);
                }} else if (ann.tool === 'rectangle') {{
                    ctx.beginPath();
                    ctx.rect(ann.startX, ann.startY, ann.endX - ann.startX, ann.endY - ann.startY);
                    ctx.stroke();
                }} else if (ann.tool === 'circle') {{
                    const radius = Math.sqrt(Math.pow(ann.endX - ann.startX, 2) + Math.pow(ann.endY - ann.startY, 2));
                    ctx.beginPath();
                    ctx.arc(ann.startX, ann.startY, radius, 0, 2 * Math.PI);
                    ctx.stroke();
                }} else if (ann.tool === 'text') {{
                    ctx.font = `${{ann.size * 8}}px Arial`;
                    ctx.fillStyle = ann.color;
                    ctx.globalAlpha = ann.opacity || 1; // Also apply to text
                    ctx.fillText(ann.text, ann.x, ann.y);
                }}
            }});
            ctx.globalAlpha = 1; // Reset to default after redrawing all
        }}
        
        function undoAnnotation() {{
            if (annotations.length > 0) {{
                annotations.pop();
                // Reload clean image
                const img = new Image();
                img.crossOrigin = 'anonymous';  // Enable CORS
                img.onload = function() {{
                    ctx.drawImage(img, 0, 0);
                    // Redraw remaining annotations
                    redrawAnnotations();
                    // Save new state
                    originalImage = ctx.getImageData(0, 0, canvas.width, canvas.height);
                    showToast('↶ Undo successful');
                }};
                img.src = originalImageSrc;
            }}
        }}
        
        function clearAnnotations() {{
            if (confirm('Clear all annotations?')) {{
                annotations = [];
                cropRect = null;
                // Reset to the very original image before any annotations
                const img = new Image();
                img.crossOrigin = 'anonymous';  // Enable CORS
                img.onload = function() {{
                    ctx.drawImage(img, 0, 0);
                    originalImage = ctx.getImageData(0, 0, canvas.width, canvas.height);
                    showToast('🗑️ All annotations cleared');
                }};
                img.src = originalImageSrc;
            }}
        }}
        
        function restoreOriginal() {{
            if (confirm('Restore original image? This will undo any crops and clear all annotations.')) {{
                annotations = [];
                cropRect = null;
                window.isCroppedImage = false;
                
                // Reload the original image with original dimensions
                const img = new Image();
                img.crossOrigin = 'anonymous';
                img.onload = function() {{
                    // Calculate scaling to fit viewport
                    const maxWidth = window.innerWidth * 0.8;
                    const maxHeight = window.innerHeight * 0.7;
                    
                    let scale = Math.min(
                        maxWidth / img.width,
                        maxHeight / img.height,
                        1 // Don't scale up, only down
                    );
                    
                    // Set canvas display size
                    canvas.style.width = (img.width * scale) + 'px';
                    canvas.style.height = (img.height * scale) + 'px';
                    
                    // Set actual canvas size (for high resolution)
                    canvas.width = img.width;
                    canvas.height = img.height;
                    
                    ctx.drawImage(img, 0, 0);
                    originalImage = ctx.getImageData(0, 0, canvas.width, canvas.height);
                    
                    showToast('↻ Original image restored!');
                    selectTool('pen');
                }};
                img.src = originalImageSrc;
            }}
        }}
        
        function startCrop(e) {{
            const rect = canvas.getBoundingClientRect();
            const scaleX = canvas.width / rect.width;
            const scaleY = canvas.height / rect.height;
            
            startX = (e.clientX - rect.left) * scaleX;
            startY = (e.clientY - rect.top) * scaleY;
            isCropping = true;
            cropRect = null;
        }}
        
        function updateCrop(e) {{
            if (!isCropping) return;
            
            const rect = canvas.getBoundingClientRect();
            const scaleX = canvas.width / rect.width;
            const scaleY = canvas.height / rect.height;
            
            const currentX = (e.clientX - rect.left) * scaleX;
            const currentY = (e.clientY - rect.top) * scaleY;
            
            // Redraw canvas
            ctx.putImageData(originalImage, 0, 0);
            redrawAnnotations();
            
            // Draw crop selection rectangle
            const width = currentX - startX;
            const height = currentY - startY;
            
            ctx.strokeStyle = '#00ff00';
            ctx.lineWidth = 3;
            ctx.setLineDash([10, 5]);
            ctx.strokeRect(startX, startY, width, height);
            ctx.setLineDash([]);
            
            // Draw semi-transparent overlay outside selection
            ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
            ctx.fillRect(0, 0, canvas.width, startY); // Top
            ctx.fillRect(0, startY, startX, height); // Left
            ctx.fillRect(startX + width, startY, canvas.width - (startX + width), height); // Right
            ctx.fillRect(0, startY + height, canvas.width, canvas.height - (startY + height)); // Bottom
        }}
        
        function finishCrop(e) {{
            if (!isCropping) return;
            
            const rect = canvas.getBoundingClientRect();
            const scaleX = canvas.width / rect.width;
            const scaleY = canvas.height / rect.height;
            
            const endX = (e.clientX - rect.left) * scaleX;
            const endY = (e.clientY - rect.top) * scaleY;
            
            const x = Math.min(startX, endX);
            const y = Math.min(startY, endY);
            const width = Math.abs(endX - startX);
            const height = Math.abs(endY - startY);
            
            if (width > 10 && height > 10) {{
                cropRect = {{ x, y, width, height }};
                applyCrop();
            }} else {{
                // Too small, cancel crop
                ctx.putImageData(originalImage, 0, 0);
                redrawAnnotations();
            }}
            
            isCropping = false;
        }}
        
        function applyCrop() {{
            if (!cropRect) return;
            
            // Get the cropped image data
            const croppedData = ctx.getImageData(cropRect.x, cropRect.y, cropRect.width, cropRect.height);
            
            // Calculate new display size maintaining proper scaling
            const maxWidth = window.innerWidth * 0.8;
            const maxHeight = window.innerHeight * 0.7;
            
            let scale = Math.min(
                maxWidth / cropRect.width,
                maxHeight / cropRect.height,
                1 // Don't scale up, only down
            );
            
            // Set canvas display size
            canvas.style.width = (cropRect.width * scale) + 'px';
            canvas.style.height = (cropRect.height * scale) + 'px';
            
            // Resize canvas to cropped dimensions
            canvas.width = cropRect.width;
            canvas.height = cropRect.height;
            
            // Draw cropped image
            ctx.putImageData(croppedData, 0, 0);
            
            // Update original image to cropped version
            originalImage = ctx.getImageData(0, 0, canvas.width, canvas.height);
            
            // Clear annotations and crop rect
            annotations = [];
            cropRect = null;
            
            // Mark that this is a cropped image
            window.isCroppedImage = true;
            
            showToast('✂️ Image cropped! Click Save to create cropped copy.');
            
            // Switch back to pen tool
            selectTool('pen');
        }}
        
        function saveAnnotatedImage() {{
            console.log('=== SAVE STARTED ===');
            console.log('Scribble dir:', '{scribble_dir_normalized}');
            
            // Convert canvas to data URL
            const dataURL = canvas.toDataURL('image/png');
            console.log('Data URL length:', dataURL.length);
            
            console.log('Saving annotated image, step:', currentStepIndex);
            
            // We'll update the image after save completes with a cache-busting URL
            const imgElement = document.getElementById(`img-${{currentStepIndex}}`);
            if (!imgElement) {{
                console.error('Image element not found for step:', currentStepIndex);
            }}
            
            // Get filename from the current image being edited
            let filename = null;
            
            // Try to get from screenshotFiles array first
            const screenshotFiles = {json.dumps([f for f in screenshots])};
            console.log('Screenshot files:', screenshotFiles);
            
            if (currentStepIndex < screenshotFiles.length) {{
                filename = screenshotFiles[currentStepIndex];
            }} else {{
                // For manually uploaded images, get filename from the img element
                if (imgElement && imgElement.dataset.filename) {{
                    filename = imgElement.dataset.filename;
                }} else {{
                    // Generate a new filename
                    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                    filename = `screenshot_manual_${{timestamp}}.png`;
                }}
            }}
            
            console.log('Saving to filename:', filename);
            
            // If this is a cropped image, create a new filename with _cropped suffix
            let saveFilename = filename;
            if (window.isCroppedImage) {{
                const nameParts = filename.split('.');
                const extension = nameParts.pop();
                const baseName = nameParts.join('.');
                saveFilename = baseName + '_cropped.' + extension;
                console.log('Cropped image, new filename:', saveFilename);
            }}
            
            const requestData = {{
                filename: saveFilename,
                dataURL: dataURL,
                scribbleDir: '{scribble_dir_normalized}'
            }};
            console.log('Request data (without dataURL):', {{filename: requestData.filename, scribbleDir: requestData.scribbleDir, dataURLLength: requestData.dataURL.length}});
            
            fetch('/api/editor/save_image', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(requestData)
            }})
            .then(response => {{
                console.log('Response status:', response.status);
                return response.json();
            }})
            .then(data => {{
                console.log('Response data:', data);
                if (data.success) {{
                    // Update the image element with cache-busting URL to show saved version
                    if (imgElement) {{
                        // Get the original image URL and add cache-busting timestamp
                        const originalSrc = imgElement.getAttribute('src');
                        const timestamp = new Date().getTime();
                        
                        // Remove any existing cache-busting parameter
                        const cleanSrc = originalSrc.split('?')[0];
                        
                        // Add new timestamp
                        const newSrc = cleanSrc + '?t=' + timestamp;
                        imgElement.src = newSrc;
                        console.log('Updated image element with cache-busting URL:', newSrc);
                        
                        // Force reload the image by creating a new Image object
                        const preloadImg = new Image();
                        preloadImg.onload = function() {{
                            imgElement.src = newSrc + '&reload=' + Math.random();
                            console.log('Image preloaded and reloaded');
                        }};
                        preloadImg.src = newSrc;
                    }}
                    
                    if (window.isCroppedImage) {{
                        showToast('✅ Cropped image saved as new file! Original preserved.', 'success', 4000);
                        window.isCroppedImage = false;
                    }} else {{
                        showToast('✅ Annotated image saved successfully!', 'success', 4000);
                    }}
                    // Close editor after successful save and image reload
                    setTimeout(() => closeAnnotationEditor(), 1000);
                }} else {{
                    showToast('❌ Failed to save: ' + data.error, 'error', 5000);
                    console.error('Save failed:', data.error);
                }}
            }})
            .catch(err => {{
                console.error('Save error:', err);
                showToast('❌ Save failed: ' + err.message, 'error', 5000);
            }});
        }}
        
        // Rich text formatting functions
        function formatText(command, stepIndex) {{
            const noteElement = document.getElementById(`note-${{stepIndex}}`);
            noteElement.focus();
            document.execCommand(command, false, null);
            noteElement.focus();
        }}
        
        function formatTextColor(color, stepIndex) {{
            const noteElement = document.getElementById(`note-${{stepIndex}}`);
            noteElement.focus();
            document.execCommand('foreColor', false, color);
            noteElement.focus();
        }}
        
        function createLink(stepIndex) {{
            const noteElement = document.getElementById(`note-${{stepIndex}}`);
            const selection = window.getSelection();
            
            if (!selection.rangeCount) {{
                alert('Please select some text first');
                return;
            }}
            
            const selectedText = selection.toString();
            if (!selectedText) {{
                alert('Please select some text to make into a link');
                return;
            }}
            
            const url = prompt('Enter URL:', 'https://');
            if (url && url !== 'https://') {{
                noteElement.focus();
                document.execCommand('createLink', false, url);
                
                // Make the link open in a new tab
                const links = noteElement.querySelectorAll('a');
                links.forEach(link => {{
                    if (!link.hasAttribute('target')) {{
                        link.setAttribute('target', '_blank');
                        link.setAttribute('rel', 'noopener noreferrer');
                    }}
                }});
                
                noteElement.focus();
                saveNoteContent(stepIndex);
            }}
        }}
        
        function saveNoteContent(stepIndex) {{
            const noteElement = document.getElementById(`note-${{stepIndex}}`);
            const storageKey = `note-${{scribbleDir}}-${{stepIndex}}`;
            localStorage.setItem(storageKey, noteElement.innerHTML);
        }}
        
        // Load saved rich text content
        window.addEventListener('DOMContentLoaded', function() {{
            document.querySelectorAll('.screenshot-note').forEach(note => {{
                const stepIndex = note.dataset.step;
                const storageKey = `note-${{scribbleDir}}-${{stepIndex}}`;
                const saved = localStorage.getItem(storageKey);
                if (saved) {{
                    note.innerHTML = saved;
                }}
            }});
        }});
        
        function showToast(message, type = 'info', duration = 3000) {{
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.style.display = 'block';
            
            // Set background color based on type
            if (type === 'success') {{
                toast.style.background = '#4caf50';
            }} else if (type === 'error') {{
                toast.style.background = '#f44336';
            }} else {{
                toast.style.background = '#333';
            }}
            
            setTimeout(() => {{ toast.style.display = 'none'; }}, duration);
        }}
        
        function generateStepInstructionsFromDataURL(dataURL, stepIndex) {{
            const noteDiv = document.getElementById(`note-${{stepIndex}}`);
            const button = event.target;
            
            // Show loading state
            button.disabled = true;
            button.textContent = '⏳ Generating...';
            button.style.background = '#95a5a6';
            
            showToast('🤖 Generating AI instructions...', 'info', 2000);
            
            // Convert data URL to blob
            fetch(dataURL)
                .then(res => res.blob())
                .then(blob => {{
                    // Create a temporary file path or send blob directly
                    // For now, we'll send the data URL directly and let server handle it
                    return fetch('/api/generate_step_instructions_base64', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{
                            image_data: dataURL
                        }})
                    }});
                }})
                .then(response => response.json())
                .then(data => {{
                    button.disabled = false;
                    button.textContent = '🤖 Generate AI Instructions';
                    button.style.background = '#27ae60';
                    
                    if (data.success) {{
                        noteDiv.innerHTML = data.instructions;
                        saveNoteContent(stepIndex);
                        showToast('✅ AI instructions generated!', 'success', 3000);
                    }} else {{
                        let errorMsg = data.error || 'Failed to generate instructions';
                        if (data.error_type === 'rate_limit') {{
                            showToast('⚠️ Rate limit reached. Wait a few minutes.', 'error', 5000);
                        }} else if (data.error_type === 'safety') {{
                            showToast('⚠️ Content blocked by safety filters.', 'error', 5000);
                        }} else {{
                            showToast('❌ ' + errorMsg, 'error', 5000);
                        }}
                    }}
                }})
                .catch(err => {{
                    console.error('Generation error:', err);
                    button.disabled = false;
                    button.textContent = '🤖 Generate AI Instructions';
                    button.style.background = '#27ae60';
                    showToast('❌ Failed to connect to server', 'error', 5000);
                }});
        }}
        
        function generateStepInstructions(imagePath, stepIndex) {{
            const noteDiv = document.getElementById(`note-${{stepIndex}}`);
            const button = event.target;
            
            // Show loading state
            button.disabled = true;
            button.textContent = '⏳ Generating...';
            button.style.background = '#95a5a6';
            
            showToast('🤖 Generating AI instructions...', 'info', 2000);
            
            fetch('/api/generate_step_instructions', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{
                    image_path: imagePath
                }})
            }})
            .then(response => response.json())
            .then(data => {{
                button.disabled = false;
                button.textContent = '🤖 Generate AI Instructions';
                button.style.background = '#27ae60';
                
                if (data.success) {{
                    // Insert the AI-generated text into the note
                    noteDiv.innerHTML = data.instructions;
                    saveNoteContent(stepIndex);
                    showToast('✅ AI instructions generated!', 'success', 3000);
                }} else {{
                    let errorMsg = data.error || 'Failed to generate instructions';
                    if (data.error_type === 'rate_limit') {{
                        showToast('⚠️ Rate limit reached. Wait a few minutes.', 'error', 5000);
                    }} else if (data.error_type === 'safety') {{
                        showToast('⚠️ Content blocked by safety filters.', 'error', 5000);
                    }} else {{
                        showToast('❌ ' + errorMsg, 'error', 5000);
                    }}
                }}
            }})
            .catch(err => {{
                console.error('Generation error:', err);
                button.disabled = false;
                button.textContent = '🤖 Generate AI Instructions';
                button.style.background = '#27ae60';
                showToast('❌ Failed to connect to server', 'error', 5000);
            }});
        }}
        
        function saveChanges() {{
            try {{
                const title = document.getElementById('titleEditor').value || 'How-To Guide';
                
                // Collect all steps with metadata about their type and source
                const notes = Array.from(document.querySelectorAll('.screenshot-item')).map((item, index) => {{
                    const noteDiv = item.querySelector('.screenshot-note');
                    const img = item.querySelector('img');
                    const stepNum = noteDiv.dataset.step;
                    
                    return {{
                        step: stepNum,
                        note: noteDiv.innerHTML,
                        type: item.dataset.type || 'screenshot',  // screenshot, upload, or text
                        imageSrc: img ? img.src : null
                    }};
                }});
                
                console.log('Saving data:', {{ title, notes, output_dir: '{scribble_dir.replace(chr(92), chr(92)+chr(92))}' }});
                
                // Show saving message
                showToast('💾 Saving changes...', 'info', 1000);
                
                // Save to server (transcript is empty string since we don't have a transcript editor)
                fetch('/api/editor/save', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        title: title,
                        transcript: '',
                        notes: notes,
                        output_dir: '{scribble_dir.replace(chr(92), chr(92)+chr(92))}'
                    }})
                }}).then(response => {{
                    console.log('Save response status:', response.status);
                    return response.json();
                }})
                  .then(data => {{
                      console.log('Save response data:', data);
                      if (data.success) {{
                          showToast('✅ All changes saved successfully!', 'success', 4000);
                      }} else {{
                          showToast('❌ Failed to save: ' + data.error, 'error', 5000);
                      }}
                  }})
                  .catch(err => {{
                      console.error('Save error:', err);
                      showToast('❌ Save failed: ' + err.message, 'error', 5000);
                  }});
            }} catch (error) {{
                console.error('Save function error:', error);
                showToast('❌ Save error: ' + error.message, 'error', 5000);
            }}
        }}
        
        function exportHTML() {{
            const title = document.getElementById('titleEditor').value || 'How-To Guide';
            const screenshots = document.querySelectorAll('.screenshot-item');
            
            let html = `<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>${{title}}</title>
<style>
body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; }}
h1 {{ color: #333; }}
.step {{ margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
.step img {{ width: 100%; border-radius: 6px; }}
.step-note {{ margin-top: 15px; color: #555; line-height: 1.6; }}
</style></head><body>
<h1>📚 ${{title}}</h1>
<h2>Step-by-Step Instructions</h2>`;
            
            // Convert images to base64 for embedding
            const promises = Array.from(screenshots).map((item, i) => {{
                return new Promise((resolve) => {{
                    const img = item.querySelector('img');
                    const noteDiv = item.querySelector('.screenshot-note');
                    const note = noteDiv.innerHTML;  // Changed to innerHTML for rich text
                    
                    // Skip if no image (text-only step)
                    if (!img) {{
                        resolve({{
                            index: i,
                            base64: null,
                            note: note
                        }});
                        return;
                    }}
                    
                    // Convert image to base64
                    fetch(img.src)
                        .then(res => res.blob())
                        .then(blob => {{
                            const reader = new FileReader();
                            reader.onloadend = () => {{
                                resolve({{
                                    index: i,
                                    base64: reader.result,
                                    note: note
                                }});
                            }};
                            reader.readAsDataURL(blob);
                        }})
                        .catch(() => {{
                            // Fallback to src if fetch fails
                            resolve({{
                                index: i,
                                base64: img.src,
                                note: note
                            }});
                        }});
                }});
            }});
            
            Promise.all(promises).then(images => {{
                images.sort((a, b) => a.index - b.index);
                images.forEach(img => {{
                    html += `<div class="step"><h3>Step ${{img.index + 1}}</h3>`;
                    if (img.base64) {{
                        html += `<img src="${{img.base64}}" alt="Step ${{img.index + 1}}">`;
                    }}
                    html += `<div class="step-note">${{img.note}}</div></div>`;
                }});
                
                html += '</body></html>';
                
                const blob = new Blob([html], {{type: 'text/html'}});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'guide.html';
                a.click();
                
                showToast('📄 HTML guide exported with embedded images!');
            }});
        }}
        
        function exportMarkdown() {{
            const title = document.getElementById('titleEditor').value || 'How-To Guide';
            const screenshots = document.querySelectorAll('.screenshot-item');
            
            let md = `# ${{title}}\\n\\n## Step-by-Step Instructions\\n\\n`;
            
            screenshots.forEach((item, i) => {{
                const img = item.querySelector('img').src.split('/').pop();
                const noteDiv = item.querySelector('.screenshot-note');
                const note = noteDiv.innerText;  // Use innerText to strip HTML for markdown
                md += `### Step ${{i + 1}}\\n\\n![](${{img}})\\n\\n${{note}}\\n\\n---\\n\\n`;
            }});
            
            const blob = new Blob([md], {{type: 'text/markdown'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'guide.md';
            a.click();
            
            showToast('📝 Markdown guide exported!');
        }}
        
        // Capture JavaScript errors and send to server
        window.onerror = function(message, source, lineno, colno, error) {{
            // Only log errors if client-side debugging is enabled
            const debugEnabled = localStorage.getItem('debugClientErrors') === 'true';
            if (debugEnabled) {{
                fetch('/api/log_client_error', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        message: message,
                        source: source,
                        line: lineno,
                        column: colno,
                        stack: error ? error.stack : null
                    }})
                }}).catch(() => {{}}); // Silently fail if logging fails
            }}
            return false; // Let browser also handle the error
        }};
        
        // Capture unhandled promise rejections
        window.addEventListener('unhandledrejection', function(event) {{
            // Only log errors if client-side debugging is enabled
            const debugEnabled = localStorage.getItem('debugClientErrors') === 'true';
            if (debugEnabled) {{
                fetch('/api/log_client_error', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        message: 'Unhandled Promise Rejection: ' + (event.reason ? event.reason.message || event.reason : 'Unknown'),
                        source: 'Promise',
                        line: 0,
                        column: 0,
                        stack: event.reason && event.reason.stack ? event.reason.stack : null
                    }})
                }}).catch(() => {{}}); // Silently fail if logging fails
            }}
        }});
        
        // Load saved changes on page load
        window.onload = function() {{
            // Don't load saved title for new guides (keep default)
            const titleEditor = document.getElementById('titleEditor');
            const currentTitle = titleEditor.value;
            const savedTitle = localStorage.getItem('guideTitle');
            
            // Only load saved title if current title is not the default "How-To Guide"
            if (savedTitle && currentTitle !== 'How-To Guide') {{
                titleEditor.value = savedTitle;
            }} else if (currentTitle === 'How-To Guide') {{
                // Clear localStorage for new guides
                localStorage.removeItem('guideTitle');
            }}
            
            const savedTranscript = localStorage.getItem('transcript');
            const savedNotes = localStorage.getItem('notes');
            
            if (savedTranscript) {{
                document.getElementById('transcriptEditor').value = savedTranscript;
            }}
            
            if (savedNotes) {{
                const notes = JSON.parse(savedNotes);
                notes.forEach(item => {{
                    const textarea = document.querySelector(`[data-step="${{item.step}}"]`);
                    if (textarea) textarea.value = item.note;
                }});
            }}
            
            // Initialize drag and drop
            initDragAndDrop();
            
            // Initialize file upload
            document.getElementById('fileInput').addEventListener('change', handleFileUpload);
            
            // Save title on change
            document.getElementById('titleEditor').addEventListener('input', function() {{
                localStorage.setItem('guideTitle', this.value);
            }});
        }};
        
        // Drag and drop functionality
        let draggedItem = null;
        
        function initDragAndDrop() {{
            const items = document.querySelectorAll('.screenshot-item');
            
            items.forEach(item => {{
                item.addEventListener('dragstart', handleDragStart);
                item.addEventListener('dragover', handleDragOver);
                item.addEventListener('drop', handleDrop);
                item.addEventListener('dragend', handleDragEnd);
            }});
        }}
        
        function handleDragStart(e) {{
            draggedItem = this;
            this.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
        }}
        
        function handleDragOver(e) {{
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            
            // Get the element being dragged over
            const afterElement = getDragAfterElement(e.clientX, e.clientY);
            const container = document.getElementById('screenshotsGrid');
            
            if (afterElement == null) {{
                container.appendChild(draggedItem);
            }} else {{
                container.insertBefore(draggedItem, afterElement);
            }}
        }}
        
        function handleDrop(e) {{
            e.stopPropagation();
            e.preventDefault();
            renumberSteps();
            return false;
        }}
        
        function handleDragEnd(e) {{
            this.classList.remove('dragging');
        }}
        
        function getDragAfterElement(x, y) {{
            const container = document.getElementById('screenshotsGrid');
            const draggableElements = [...container.querySelectorAll('.screenshot-item:not(.dragging)')];
            
            let closestElement = null;
            let closestDistance = Number.POSITIVE_INFINITY;
            
            draggableElements.forEach(child => {{
                const box = child.getBoundingClientRect();
                const centerX = box.left + box.width / 2;
                const centerY = box.top + box.height / 2;
                
                // Calculate distance from mouse to element center
                const distanceX = x - centerX;
                const distanceY = y - centerY;
                const distance = Math.sqrt(distanceX * distanceX + distanceY * distanceY);
                
                // Find closest element
                if (distance < closestDistance) {{
                    closestDistance = distance;
                    closestElement = child;
                }}
            }});
            
            // Determine if we should insert before or after based on position
            if (closestElement) {{
                const box = closestElement.getBoundingClientRect();
                const centerX = box.left + box.width / 2;
                const centerY = box.top + box.height / 2;
                
                // If in grid, check both X and Y
                if (y > centerY || (y >= box.top && y <= box.bottom && x > centerX)) {{
                    // Insert after this element
                    return closestElement.nextSibling;
                }} else {{
                    // Insert before this element
                    return closestElement;
                }}
            }}
            
            return closestElement;
        }}
        
        function renumberSteps() {{
            const items = document.querySelectorAll('.screenshot-item');
            items.forEach((item, index) => {{
                const stepNum = index + 1;
                item.dataset.step = stepNum;
                item.querySelector('.screenshot-number').textContent = `Step ${{stepNum}}`;
                item.querySelector('.screenshot-note').dataset.step = stepNum;
            }});
            showToast('📝 Steps reordered');
        }}
        
        function deleteStep(btn) {{
            if (confirm('Delete this step?')) {{
                btn.closest('.screenshot-item').remove();
                renumberSteps();
                showToast('🗑️ Step deleted');
            }}
        }}
        
        function addTextStep() {{
            const container = document.getElementById('screenshotsGrid');
            const stepNum = container.children.length + 1;
            
            const newItem = document.createElement('div');
            newItem.className = 'screenshot-item';
            newItem.draggable = true;
            newItem.dataset.step = stepNum;
            newItem.dataset.type = 'text';  // Mark as text-only step
            
            newItem.innerHTML = `
                <div class="drag-handle">⋮⋮ Drag</div>
                <button class="delete-btn" onclick="deleteStep(this)">🗑️ Delete</button>
                <div class="screenshot-number">Step ${{stepNum}}</div>
                <div class="rich-text-toolbar" data-step="${{stepNum}}">
                    <button class="format-btn" onclick="formatText('bold', ${{stepNum}})" title="Bold"><b>B</b></button>
                    <button class="format-btn" onclick="formatText('italic', ${{stepNum}})" title="Italic"><i>I</i></button>
                    <button class="format-btn" onclick="formatText('underline', ${{stepNum}})" title="Underline"><u>U</u></button>
                    <button class="format-btn" onclick="formatText('strikeThrough', ${{stepNum}})" title="Strikethrough"><s>S</s></button>
                    <div class="toolbar-separator"></div>
                    <button class="format-btn" onclick="formatText('insertUnorderedList', ${{stepNum}})" title="Bullet List">• List</button>
                    <button class="format-btn" onclick="formatText('insertOrderedList', ${{stepNum}})" title="Numbered List">1. List</button>
                    <div class="toolbar-separator"></div>
                    <button class="format-btn" onclick="formatText('justifyLeft', ${{stepNum}})" title="Align Left">⬅</button>
                    <button class="format-btn" onclick="formatText('justifyCenter', ${{stepNum}})" title="Align Center">⬌</button>
                    <button class="format-btn" onclick="formatText('justifyRight', ${{stepNum}})" title="Align Right">➡</button>
                    <div class="toolbar-separator"></div>
                    <input type="color" class="color-input" onchange="formatTextColor(this.value, ${{stepNum}})" title="Text Color" value="#000000">
                    <button class="format-btn" onclick="createLink(${{stepNum}})" title="Insert Link">🔗</button>
                    <button class="format-btn" onclick="formatText('removeFormat', ${{stepNum}})" title="Clear Formatting">✕</button>
                </div>
                <div class="screenshot-note" contenteditable="true" data-step="${{stepNum}}" id="note-${{stepNum}}" onblur="saveNoteContent(${{stepNum}})">Type your step instructions here...</div>
            `;
            
            container.appendChild(newItem);
            
            // Add drag listeners to new item
            newItem.addEventListener('dragstart', handleDragStart);
            newItem.addEventListener('dragover', handleDragOver);
            newItem.addEventListener('drop', handleDrop);
            newItem.addEventListener('dragend', handleDragEnd);
            
            showToast('📝 Text step added');
            
            // Focus the new note field
            setTimeout(() => {{
                const noteField = document.getElementById(`note-${{stepNum}}`);
                if (noteField) {{
                    noteField.focus();
                }}
            }}, 100);
        }}
        
        function handleFileUpload(e) {{
            const file = e.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = function(event) {{
                const img = event.target.result;
                addNewStep(img);
                showToast('✅ Screenshot added');
            }};
            reader.readAsDataURL(file);
        }}
        
        function addNewStep(imgSrc) {{
            const container = document.getElementById('screenshotsGrid');
            const stepNum = container.children.length + 1;
            
            const newItem = document.createElement('div');
            newItem.className = 'screenshot-item';
            newItem.draggable = true;
            newItem.dataset.step = stepNum;
            newItem.dataset.type = 'upload';  // Mark as uploaded image
            
            newItem.innerHTML = `
                <div class="drag-handle">⋮⋮ Drag</div>
                <button class="delete-btn" onclick="deleteStep(this)">🗑️ Delete</button>
                <div class="screenshot-number">Step ${{stepNum}}</div>
                <button class="edit-btn" onclick="openAnnotationEditorFromDataURL('${{imgSrc}}', ${{stepNum}})">✏️ Edit & Annotate</button>
                <button class="edit-btn" onclick="generateStepInstructionsFromDataURL('${{imgSrc}}', ${{stepNum}})" style="background: #27ae60;">🤖 Generate AI Instructions</button>
                <img src="${{imgSrc}}" class="screenshot-img" id="img-${{stepNum}}" onclick="showImage(this.src)" alt="Screenshot ${{stepNum}}">
                
                <div class="rich-text-toolbar" data-step="${{stepNum}}">
                    <button class="format-btn" onclick="formatText('bold', ${{stepNum}})" title="Bold"><b>B</b></button>
                    <button class="format-btn" onclick="formatText('italic', ${{stepNum}})" title="Italic"><i>I</i></button>
                    <button class="format-btn" onclick="formatText('underline', ${{stepNum}})" title="Underline"><u>U</u></button>
                    <button class="format-btn" onclick="formatText('strikeThrough', ${{stepNum}})" title="Strikethrough"><s>S</s></button>
                    <div class="toolbar-separator"></div>
                    <button class="format-btn" onclick="formatText('insertUnorderedList', ${{stepNum}})" title="Bullet List">• List</button>
                    <button class="format-btn" onclick="formatText('insertOrderedList', ${{stepNum}})" title="Numbered List">1. List</button>
                    <div class="toolbar-separator"></div>
                    <button class="format-btn" onclick="formatText('justifyLeft', ${{stepNum}})" title="Align Left">⬅</button>
                    <button class="format-btn" onclick="formatText('justifyCenter', ${{stepNum}})" title="Align Center">⬌</button>
                    <button class="format-btn" onclick="formatText('justifyRight', ${{stepNum}})" title="Align Right">➡</button>
                    <div class="toolbar-separator"></div>
                    <input type="color" class="color-input" onchange="formatTextColor(this.value, ${{stepNum}})" title="Text Color" value="#000000">
                    <button class="format-btn" onclick="createLink(${{stepNum}})" title="Insert Link">🔗</button>
                    <button class="format-btn" onclick="formatText('removeFormat', ${{stepNum}})" title="Clear Formatting">✕</button>
                </div>
                
                <div class="screenshot-note" contenteditable="true" data-step="${{stepNum}}" id="note-${{stepNum}}" onblur="saveNoteContent(${{stepNum}})">Add notes for this step...</div>
            `;
            
            container.appendChild(newItem);
            
            // Add drag listeners to new item
            newItem.addEventListener('dragstart', handleDragStart);
            newItem.addEventListener('dragover', handleDragOver);
            newItem.addEventListener('drop', handleDrop);
            newItem.addEventListener('dragend', handleDragEnd);
        }}
        

    </script>
</body>
</html>
"""
    
    # Save HTML file for desktop version
    html_path = os.path.join(scribble_dir, "editor.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # Return both the path (for desktop) and content (for web)
    return html_content
