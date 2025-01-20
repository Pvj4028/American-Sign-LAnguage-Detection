import socket
import streamlit as st

# Function to send a message over an existing socket connection
def send_message_to_server_persistent(sock, message):
    try:
        # Send the message to the server
        sock.sendall(message.encode())
        # Receive the response from the server
        response = sock.recv(1024).decode()
        return response
    except Exception as e:
        return f"Error communicating with server: {e}"

# Function to establish a persistent connection
def establish_connection(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        return sock
    except Exception as e:
        st.error(f"Error connecting to server: {e}")
        return None

# Streamlit app
st.title("TalkTogether")

# Initialize chat history and socket connection in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "socket_connection" not in st.session_state:
    SERVER_HOST ='192.168.1.16'  # Replace with your server's IP
    SERVER_PORT = 8080
    st.session_state.socket_connection = establish_connection(SERVER_HOST, SERVER_PORT)

# Check if the connection was established successfully
if st.session_state.socket_connection:
    # User input for message
    message = st.text_input("Type your message:")

    # Button to send the message to the server
    if st.button("Send"):
        if message:
            # Send the message and get the response
            response = send_message_to_server_persistent(st.session_state.socket_connection, message)
            
            # Append the message and response to chat history
            st.session_state.chat_history.append(f"You: {message}")
            st.session_state.chat_history.append(f"Server: {response}")
        else:
            st.warning("Please type a message before sending.")

    # Display chat history
    st.subheader("Chat History")
    for chat in st.session_state.chat_history:
        st.write(chat)
else:
    st.error("Unable to connect to the server. Please check your network or server status.")
