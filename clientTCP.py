import streamlit as st
import socket
import threading
from queue import Queue

# Set up the server address and client socket (TCP)
server_address = ('192.168.1.3', 5000)  # Server's IP address
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Use TCP
client.connect(server_address)  # Connect to the TCP server

# Initialize chat history and message input in the session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "nickname" not in st.session_state:
    st.session_state.nickname = ""
if "message_input" not in st.session_state:
    st.session_state.message_input = ""
if "thread_started" not in st.session_state:
    st.session_state.thread_started = False
    
# Create a queue to handle received messages
message_queue = Queue()

# Function to receive messages and put them in the message queue
def receive_messages():
    while True:
        try:
            message = client.recv(1024)
            print(message)
            if message:
                decoded_message = message.decode('ascii')
                message_queue.put(decoded_message)  # Add received message to the queue
                while not message_queue.empty():
                    print(message_queue.get())
            else:
                break  # Close if no more data
        except Exception as e:
            print(f"An error occurred: {e}")
            break

# Function to send messages
def send_message():
    if st.session_state.nickname and st.session_state.message_input:
        message = f"{st.session_state.nickname}: {st.session_state.message_input}"
        client.send(message.encode('ascii'))  # Send message to the server
        st.session_state.message_input = ""  # Clear the input after sending

# Start the message receiver thread
if not st.session_state.thread_started:
    receive_thread = threading.Thread(target=receive_messages, daemon=True)
    receive_thread.start()
    st.session_state.thread_started = True

# Add a navbar to the sidebar
st.sidebar.title("Kongu Engineering College")
st.sidebar.subheader("Computer Networks")

# Set the nickname
if st.session_state.nickname == "":
    st.session_state.nickname = st.sidebar.text_input("Choose your nickname:")
    if st.sidebar.button("Set Nickname") and st.session_state.nickname:
        # Send the nickname to the server once after it's set
        client.send(f"NICKNAME:{st.session_state.nickname}".encode('ascii'))

# Function to append received messages to chat history
def append_messages():
    while not message_queue.empty():
        msg = message_queue.get()
        st.session_state.chat_history.append(msg)

# Main UI logic
if st.session_state.nickname:
    # Append messages before rendering
    append_messages()

    # Display chat messages
    st.title("TCP Chat App")
    if st.session_state.chat_history:  # Check if there are messages to display
        for msg in st.session_state.chat_history:
            st.write(f"💬 {msg}")  # Display messages using st.write() in the main UI thread
    else:
        st.write("No messages yet.")

    # Input field for sending messages
    st.session_state.message_input = st.text_input("Type your message:", value=st.session_state.message_input)
    if st.button("Send"):
        send_message()  # Call the send_message function
