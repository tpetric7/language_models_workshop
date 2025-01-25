import streamlit as st
import openai
from openai import OpenAI

# Initialize OpenAI client with local server configuration
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

# Set up the page
st.set_page_config(page_title="Local Chatbot", page_icon=":speech_balloon:", layout="centered")

st.title("Local Chatbot")

# Initialize session state to store chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Function to handle sending a message to the chatbot
def send_message():
    user_message = st.session_state.user_input
    if user_message:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "message": user_message})
        
        # Send the user message to the chatbot
        try:
            completion = client.chat.completions.create(
                model="llama3.1:8b-instruct-fp16",
                messages=[
                    {"role": "system", "content": "Always answer truthfully."},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.7,
            )
            
            # Get the chatbot response
            bot_response = completion.choices[0].message.content
            st.session_state.chat_history.append({"role": "bot", "message": bot_response})
        
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
        
        # Clear the input field
        st.session_state.user_input = ""

# Chat input
st.text_input("Type your message:", key="user_input", on_change=send_message)

# CSS for chat area
chat_css = """
<style>
#chat-container {
    max-height: 400px;
    overflow-y: auto;
}
</style>
"""
st.markdown(chat_css, unsafe_allow_html=True)  # Apply CSS styles

# Chat message display using a container
chat_container = st.container()
with chat_container:
    chat_messages = "<div id='chat-container'>"
    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            chat_messages += f"<p><strong>You:</strong> {chat['message']}</p>"
        else:
            chat_messages += f"<p><strong>Bot:</strong> {chat['message']}</p>"
    chat_messages += "</div>"
    st.markdown(chat_messages, unsafe_allow_html=True)

# Placeholder to force the chat to scroll to the bottom
scroll_placeholder = st.empty()
scroll_placeholder.markdown("<div></div>", unsafe_allow_html=True)
