import streamlit as st
import socket
import threading
from queue import Queue

# Set up the server address and client socket
server_address = ('192.168.1.3', 5000)  # Server's IP address
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.bind(('', 0))  # Bind to a random available port

# Initialize chat history and message input in the session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "nickname" not in st.session_state:
    st.session_state.nickname = ""
if "message_input" not in st.session_state:
    st.session_state.message_input = ""

# Create a queue to handle received messages
message_queue = Queue()

# Function to receive messages
def receive_messages():
    while True:
        try:
            message, _ = client.recvfrom(1024)
            print(message)
            message_queue.put(message.decode('ascii'))  # Add received message to the queue
        except Exception as e:
            print(f"An error occurred: {e}")
            break

# Function to send messages
def send_message():
    if st.session_state.nickname and st.session_state.message_input:
        message = f"{st.session_state.nickname}: {st.session_state.message_input}"
        client.sendto(message.encode('ascii'), server_address)
        st.session_state.message_input = ""  # Clear the input after sending

# Start the message receiver thread
if 'receive_thread' not in st.session_state:
    receive_thread = threading.Thread(target=receive_messages, daemon=True)
    receive_thread.start()

# Set up the sidebar
st.sidebar.title("Kongu Engineering College")
st.sidebar.subheader("Computer Networks")

# Set the nickname
if st.session_state.nickname == "":
    st.session_state.nickname = st.sidebar.text_input("Choose your nickname:")

# Input for the message
if st.session_state.nickname:
    # Function to append received messages to chat history
    def append_messages():
        while not message_queue.empty():
            msg = message_queue.get()
            st.session_state.chat_history.append(msg)

    # Check for new messages before displaying
    append_messages()

    # Display chat messages
    st.title("UDP Chat App")
    if st.session_state.chat_history:  # Check if there are messages to display
        for msg in st.session_state.chat_history:
            st.markdown(f"> {msg}")  # Display messages using markdown
    else:
        st.markdown("> No messages yet.")

    # Message input
    st.session_state.message_input = st.text_input("Type your message:", value=st.session_state.message_input)
    if st.button("Send"):
        send_message()  # Call the send_message function
