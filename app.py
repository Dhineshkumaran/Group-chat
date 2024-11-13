from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO, emit
import socket
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

clients = []  # For UDP clients
lock = threading.Lock()

# UDP server variables
udp_host = '0.0.0.0'
udp_port = 5000
udp_server = None

# Function to start UDP server
def start_udp_server():
    global udp_server
    udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_server.bind((udp_host, udp_port))
    print("UDP Server is listening...")
    while True:
        message, client_address = udp_server.recvfrom(1024)
        if client_address not in clients:
            with lock:
                clients.append(client_address)
        print(f"Received message from {client_address}: {message.decode('ascii')}")
        socketio.emit('message', {'msg': message.decode('ascii')})

# TCP server variables
tcp_host = '0.0.0.0'
tcp_port = 5001
tcp_server = None

# Function to start TCP server
def start_tcp_server():
    global tcp_server
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.bind((tcp_host, tcp_port))
    tcp_server.listen()
    print("TCP Server is listening...")

    while True:
        client, address = tcp_server.accept()
        print(f"Connection established with {address}")
        with lock:
            clients.append(client)
        client_thread = threading.Thread(target=handle_tcp_client, args=(client,))
        client_thread.start()

# Function to handle TCP clients
def handle_tcp_client(client):
    try:
        while True:
            message = client.recv(1024)
            if not message:
                break
            print(f"Message received: {message.decode('ascii')}")
            broadcast_tcp(message)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        remove_tcp_client(client)

# Broadcast message to all TCP clients
def broadcast_tcp(message):
    with lock:
        for client in clients:
            try:
                client.send(message)
            except Exception:
                print("Failed to send message to client.")

# Remove TCP client
def remove_tcp_client(client):
    with lock:
        if client in clients:
            clients.remove(client)
            client.close()

# Flask route to serve the HTML file
@app.route('/')
def index():
    return render_template('index.html')  # Render the HTML file

# Flask route to start the UDP server
@app.route('/udp_server')
def udp_server_route():
    udp_thread = threading.Thread(target=start_udp_server)
    udp_thread.daemon = True
    udp_thread.start()
    return jsonify({"status": "UDP server started"}), 200

# Flask route to start the TCP server
@app.route('/tcp_server')
def tcp_server_route():
    tcp_thread = threading.Thread(target=start_tcp_server)
    tcp_thread.daemon = True
    tcp_thread.start()
    return jsonify({"status": "TCP server started"}), 200

# WebSocket event for messages
@socketio.on('message')
def handle_message(data):
    msg = data['msg']
    print(f"Message from client: {msg}")
    emit('message', {'msg': msg}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000)
