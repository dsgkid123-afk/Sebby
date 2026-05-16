import requests
import base64
import os
from PIL import Image
import io
import re

# ------------------ CONFIG ------------------

MODEL = "gemma4"
OLLAMA_URL = "http://localhost:11434/api/chat"

BASE_DIR = os.path.dirname(__file__)
SOUL_PATH = os.path.join(BASE_DIR, "soul.txt")
USER_PATH = os.path.join(BASE_DIR, "user.txt")
TRACKER_PATH = os.path.join(BASE_DIR, "tracker.txt")

# ------------------ STATE ------------------

chat_history = []
system_prompt = """"""


result = None

#ENCODE TO BASE 64

def encode_image(image_path):
    with Image.open(image_path) as img:
        target_height = 480
        aspect_ratio = img.width / img.height
        target_width = int(target_height * aspect_ratio)

        img = img.resize((target_width, target_height))

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=70)
        buffer.seek(0)

        return base64.b64encode(buffer.read()).decode('utf-8')

# READ AND WRITE FILES

def read_file(path):
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path, content):
    with open(path, "a", encoding="utf-8") as f:
        f.write(content + "\n")

#TRACKER
def read_tracker():
    if not os.path.exists(TRACKER_PATH):
        return 0
    try:
        return int(read_file(TRACKER_PATH).strip() or 0)
    except ValueError:
        return 0

def write_tracker(value):
    with open(TRACKER_PATH, "w", encoding="utf-8") as f:
        f.write(str(value))

# ------------------ TOOLS ------------------

def tool_web_search(query):
    try:
        r = requests.get(f"https://duckduckgo.com/?q={query}")
        return f"Search results page: {r.url}"
    except Exception as e:
        return f"Search error: {e}"

def tool_write_memory(target, content):
    if target == "soul":
        write_file(SOUL_PATH, content)
        return "Wrote to soul memory."
    elif target == "user":
        write_file(USER_PATH, content)
        return "Wrote to user memory."
    else:
        return "Invalid memory target."

# LOOK FOR TOOL CALLS

def parse_tool_call(response_text):
    if "[TOOL]" not in response_text:
        return None

    try:
        line = response_text.split("[TOOL]")[1].strip()
        parts = [p.strip() for p in line.split("|")]
        print(f"SEBBYLLM: listed args DEBUG {parts}")
        return {
            "name": parts[0],
            "args": parts[1:]
        }
    except:
        return None


def run_tool(tool):
    try:
        if tool["name"] == "web_search":
            #samble print shit
            print(f"Web SEARCH: {tool['args'][0]}")
            return tool_web_search(tool["args"][0])

        elif tool["name"] == "write_memory":
            print(f"Running write_memory for target: {tool['args'][0]} with content: {tool['args'][1]}")
            return tool_write_memory(tool["args"][0], tool["args"][1])

        elif tool["name"] == "update_sustainability_tracker":
            change = int(tool["args"][0])
            updated_tracker = read_tracker() + change
            write_tracker(updated_tracker)
            return f"changed tracker to {updated_tracker}."

        else:
            return "not a tool"

    except Exception as e:
        return f"Tool error: {e}"

#CHAT MANAGEMENT FUNCS

def reset_chat():
    global chat_history
    chat_history = []

def set_system(prompt):
    global system_prompt
    system_prompt = prompt

#MAIN STUFF

def analyze(image_path=None, prompt=""):
    global chat_history

    images = []

    if not image_path == None:
        full_img = os.path.join(BASE_DIR, image_path)
        images.append(encode_image(full_img))

    # Build base messages
    messages = []
    

    messages.append({
        "role": "system",
        "content": system_prompt
    })

    soul_memory = read_file(SOUL_PATH)
    user_memory = read_file(USER_PATH)
    current_tracker = read_tracker()

    if soul_memory:
        messages.append({
            "role": "system",
            "content": f"[CURRENT PERSONALITY/SOUL]\n{soul_memory}"
        })

    if user_memory:
        messages.append({
            "role": "system",
            "content": f"[CURRENT MEMORY'S OF USER]\n{user_memory}"
        })
    if current_tracker:
        messages.append({
            "role": "system",
            "content": f"[CURRENT SUSTAINABILITY TRACKER SCORE]\n{current_tracker}"
        })
    # remove any old system messages from chat history
    chat_history = [m for m in chat_history if m["role"] != "system"]
    with open("chathistorylogs.txt", "w", encoding="utf-8") as f:
        f.write(chat_history.__str__())
    messages.extend(chat_history)

    messages.append({
        "role": "user",
        "content": prompt,
        "images": images if images else []
    })

    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "temperature": 0,
        "top_p": 0.1,
        "repeat_penalty": 1,
        "think": False,
        #"num_thread": 64,
        "options": {
            "num_gpu": 999
        }
    }

    response = requests.post(OLLAMA_URL, json=payload)
    
    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"
    output = response.json()["message"]["content"]
    print(f"SEBBYLLM OUTPUT: {output}")
       
    tool = parse_tool_call(output)
        
    if len(output) < 20 and not tool:
        output = ""
    # If NO tool → final answer
    if not tool:
        if output != "":
            chat_history.append({"role": "user", "content": prompt})
            chat_history.append({"role": "Sebby", "content": output})
        return output, True, None, None
    # Run tool
    result = run_tool(tool)

    # Feed result back into conversation
    messages.append({
        "role": "Sebby",
        "content": output
    })

    messages.append({
        "role": "system",
        "content": f"[TOOL RESULT]\n{result}"
    })

    if output != "":
        chat_history.append({"role": "user", "content": prompt})
        chat_history.append({"role": "Sebby", "content": output})
        chat_history.append({"role": "system", "content": f"[TOOL RESULT]\n{result}"})
    # strip tool call form output before returning to coordinator:
    output=re.sub(r'^\[TOOL\].*\n?', '', output, flags=re.MULTILINE).strip()
    return output, False, tool, result