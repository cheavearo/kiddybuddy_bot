import streamlit as st
import random
import json
import os
import uuid
from openai import OpenAI
from dotenv import load_dotenv

# -------------------------------
# --- Config & API Setup -------
# -------------------------------
st.set_page_config(
    page_title="Kiddy Buddy Chatbot 🤖",
    page_icon="🧸",
    layout="wide"
)

load_dotenv()
os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Bot avatar and name
BOT_NAME = "KiddyBuddyBot"
BOT_AVATAR = "https://media.giphy.com/media/3oKIPwoeGErMmaI43C/giphy.gif"

# Predefined sounds
CORRECT_SOUND = "https://www.soundjay.com/buttons/sounds/button-3.mp3"
WRONG_SOUND   = "https://www.soundjay.com/buttons/sounds/button-10.mp3"

# All emojis pool
ALL_EMOJIS = ["🐶","🐱","🐭","🐹","🐰","🦊","🐻","🐼","🦁","🐵","🦄","🐸","🐷","🐤","🦖"]

# -------------------------------
# --- CSS for chat bubbles & emoji buttons -----
# -------------------------------
st.markdown("""
<style>
.chatbox {
     border-radius: 15px;
     padding: 10px;
     margin-bottom: 10px;
     font-family: 'Comic Sans MS', cursive, sans-serif;
     font-size: 20px;
     max-width: 70%;
}
.user { background-color: #6FA8DC; color: white; text-align: right; margin-left: auto; }
.bot { background-color: #FFD966; color: black; text-align: left; display:flex; align-items:center;}
.bot img { width:50px; margin-right:10px; }
button.stButton > button {
     font-size: 30px;
     padding: 20px 20px;
     margin: 5px;
     border-radius: 10px;
     border: 2px solid #666;
    min-width: 60px;
    min-height: 60px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# --- Session State Init -------
# -------------------------------
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'current_activity' not in st.session_state:
    st.session_state.current_activity = None

# -------------------------------
# --- Display Messages ---------
# -------------------------------
def display_messages():
    for msg in st.session_state.messages:
        if msg['role'] == 'user':
            st.markdown(f"<div class='chatbox user'>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(
                f"<div class='chatbox bot'><img src='{BOT_AVATAR}'>{msg['content']}</div>",
                unsafe_allow_html=True
            )

# -------------------------------
# --- Safe JSON parser ----------
# -------------------------------
def parse_llm_json(raw_text, default_activity=None):
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        start = raw_text.find("{")
        end = raw_text.rfind("}") + 1
        try:
            return json.loads(raw_text[start:end])
        except:
            return default_activity or {}

# -------------------------------
# --- Play sound automatically --
# -------------------------------
def play_sound(url):
    audio_id = uuid.uuid4()
    st.markdown(f"""
    <audio autoplay>
      <source src="{url}?{audio_id}" type="audio/mpeg">
    </audio>
    """, unsafe_allow_html=True)

# -------------------------------
# --- Generate Joke -------------
# -------------------------------
def generate_joke():
    prompt = "Tell me a short, child-friendly joke. Return only the joke text."
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9
        )
        return response.choices[0].message.content.strip()
    except:
        return "Why did the banana go to the doctor? Because it wasn't peeling well! 🍌"

# -------------------------------
# --- Generate Mini-Game --------
# -------------------------------
def generate_mini_game():
    prompt = """
    You are a friendly chatbot for kids. Generate a fun mini-game for children. The game can be:
    1. "guess_number" → child guesses a number in a range.
    2. "emoji_match" → child must match a sequence of emojis.
    Return ONLY valid JSON with keys:
    - type: "mini_game"
    - activity_type: "mini_game"
    - game: "guess_number" or "emoji_match"
    - instructions: short instruction
    - range: [min,max] if game is guess_number
    - sequence: list of emojis in correct order if emoji_match
    - options: list of emoji options if emoji_match
    """
    default_activity = {
        "type": "mini_game",
        "activity_type": "mini_game",
        "game": "emoji_match",
        "instructions": "Match the emoji sequence!",
        "sequence": ["🐶","🐱","🐭"],
        "options": ["🐶","🐱","🐭","🐹"],
        "sound_correct": CORRECT_SOUND,
        "sound_wrong": WRONG_SOUND
    }

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9
        )
        activity = parse_llm_json(response.choices[0].message.content, default_activity)
    except:
        activity = default_activity

    if activity.get('game') == 'emoji_match':
        sequence = activity.get('sequence') or random.sample(ALL_EMOJIS, k=4)
        activity['sequence'] = sequence
        options = activity.get('options')
        if not options:
            extra = [e for e in ALL_EMOJIS if e not in sequence]
            options = sequence + random.sample(extra, k=max(1, 6 - len(sequence)))
            random.shuffle(options)
            activity['options'] = options
    if activity.get('game') == 'guess_number':
        activity.setdefault('range', [1, 10])
        activity.setdefault('instructions', "Guess the correct number!")
    activity.setdefault('sound_correct', CORRECT_SOUND)
    activity.setdefault('sound_wrong', WRONG_SOUND)
    return activity

# -------------------------------
# --- Generate Quiz -------------
# -------------------------------
def generate_quiz():
    prompt = """
    You are a friendly chatbot for kids. Generate a child-friendly quiz question. Focus on educational topics like math, colors, animals, shapes, or spelling.
    Return ONLY valid JSON with keys:
    - type: "quiz"
    - activity_type: "quiz"
    - question: text
    - options: list of 3-4 answer choices
    - correct_option: correct answer
    """
    default_activity = {
        "type": "quiz",
        "activity_type": "quiz",
        "question": "What color is the sky on a sunny day?",
        "options": ["Blue","Green","Red","Yellow"],
        "correct_option": "Blue",
        "sound_correct": CORRECT_SOUND,
        "sound_wrong": WRONG_SOUND
    }

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9
        )
        activity = parse_llm_json(response.choices[0].message.content, default_activity)
    except:
        activity = default_activity

    activity.setdefault('sound_correct', CORRECT_SOUND)
    activity.setdefault('sound_wrong', WRONG_SOUND)
    return activity

# -------------------------------
# --- Render Activity -----------
# -------------------------------
def render_activity(activity_json):
    if not activity_json:
        st.error("⚠️ Failed to load activity.")
        return

    if activity_json['activity_type'] == 'quiz':
        st.write("📝 Quiz Time!")
        answer = st.radio(activity_json.get('question','Question?'), activity_json.get('options',[]), key="quiz_radio")
        if st.button("Submit Answer", key="quiz_btn"):
            if answer == activity_json.get('correct_option'):
                st.success("🎉 Correct! 🎊")
                st.balloons()
                play_sound(activity_json.get('sound_correct'))
            else:
                st.error("❌ Try again!")
                play_sound(activity_json.get('sound_wrong'))

    elif activity_json['activity_type'] == 'mini_game':
        st.write("🎮 Mini Game!")
        st.write(activity_json.get("instructions", "Try to win the game!"))
        game_type = activity_json.get('game')

        if game_type == 'guess_number':
            guess = st.number_input(
                f"Pick a number between {activity_json['range'][0]}-{activity_json['range'][1]}",
                min_value=activity_json['range'][0],
                max_value=activity_json['range'][1],
                step=1,
                key="guess_input"
            )
            if st.button("Check", key="mini_btn"):
                target = random.randint(activity_json['range'][0], activity_json['range'][1])
                if guess == target:
                    st.success("🎉 Correct! 🎊")
                    st.balloons()
                    play_sound(activity_json.get('sound_correct'))
                else:
                    st.warning(f"❌ Nope! It was {target}")
                    play_sound(activity_json.get('sound_wrong'))

        elif game_type == 'emoji_match':
            sequence = activity_json.get('sequence', [])
            options = activity_json.get('options', [])

            if not sequence:
                sequence = random.sample(ALL_EMOJIS, k=4)
                activity_json['sequence'] = sequence

            if not options:
                extra = [e for e in ALL_EMOJIS if e not in sequence]
                options = sequence + random.sample(extra, k=max(1, 6 - len(sequence)))
                random.shuffle(options)
                activity_json['options'] = options

            # SHOW the target sequence for kids
            st.write("Match the sequence of emojis shown below:")
            st.markdown(" ".join(sequence), unsafe_allow_html=True)

            # Create selectboxes for each position
            user_sequence = []
            for i in range(len(sequence)):
                choice = st.selectbox(f"Position {i+1}:", options, key=f"emoji_pos_{i}")
                user_sequence.append(choice)

            if st.button("Check Emoji Match", key="emoji_btn"):
                if user_sequence == sequence:
                    st.success("🎉 Perfect match! 🎊")
                    st.balloons()
                    play_sound(activity_json.get('sound_correct'))
                else:
                    st.warning(f"❌ Try again! Correct sequence: {' '.join(sequence)}")
                    play_sound(activity_json.get('sound_wrong'))

# -------------------------------
# --- Main Chatbot UI -----------
# -------------------------------
display_messages()

st.markdown("### Choose an action:")
options = ["Say Hello 👋", "Tell a Joke 😂", "Dynamic Mini Game 🎮", "Dynamic Quiz 📝"]

with st.form("action_form"):
    choice = st.radio("Choose an option:", options, label_visibility="collapsed")
    submitted = st.form_submit_button("Send")

if submitted:
    st.session_state.messages.append({"role": "user", "content": choice})

    if choice == "Say Hello 👋":
        st.session_state.messages.append({"role": "bot", "content": f"{BOT_NAME}: Hello! You chose: {choice} 😃"})

    elif choice == "Tell a Joke 😂":
        joke = generate_joke()
        st.session_state.messages.append({"role": "bot", "content": f"{BOT_NAME}: {joke}"})

    elif choice == "Dynamic Mini Game 🎮":
        st.session_state.current_activity = generate_mini_game()
        st.session_state.messages.append({"role": "bot", "content": f"{BOT_NAME}: Here's your mini-game! 🎉"})

    elif choice == "Dynamic Quiz 📝":
        st.session_state.current_activity = generate_quiz()
        st.session_state.messages.append({"role": "bot", "content": f"{BOT_NAME}: Here's your quiz! 📝"})

# Render current activity
if st.session_state.current_activity:
    render_activity(st.session_state.current_activity)
