import socket        # Used to create a TCP server and handle network communication
import threading     # Allows the server to handle multiple clients at the same time
import os            # Used for working with file paths and directories
import urllib.parse  # Used to parse form data from POST requests
import hashlib       # Provides SHA256 hashing for passwords
import uuid          # Generates unique session IDs for logged-in users
# Server network configuration
HOST = '0.0.0.0'      # Listen on all network interfaces
PORT = 8099           # Port number for the web server
# Define important file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))       # Absolute path of project folder
STATIC_DIR = BASE_DIR                                       # Directory containing HTML, CSS, images
USER_FILE = os.path.join(BASE_DIR, "data.txt")              # File storing usernames and hashed passwords
# Dictionary storing active sessions: {session_id: username}
sessions = {}
# Content-Type headers for different file formats (MIME types)
MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}
# Simple logger to print messages to the terminal immediately
def log(msg):
    print(msg, flush=True)





# ----------------------------------------------------------
# Parse the raw HTTP request and extract method, path, headers, and body
# ----------------------------------------------------------
def request(request_data):
    try:
        header, body = request_data.split(b"\r\n\r\n", 1)
    except ValueError:
        header = request_data
        body = b""

    lines = header.decode(errors="ignore").split("\r\n")
    
    # First line: "GET /path HTTP/1.1"
    request_line = lines[0]
    method, path, version = request_line.split(" ")

    # Parse headers into a dictionary
    headers = {}
    for line in lines[1:]:
        parts = line.split(":", 1)
        if len(parts) == 2:
            key = parts[0].strip().lower()
            value = parts[1].strip()
            headers[key] = value

    return method, path, version, headers, body


# ----------------------------------------------------------
# Build the HTTP response packet to send back to the browser
# ----------------------------------------------------------
def response(status_line, headers, body_bytes):
    response = status_line + "\r\n"
    for key, value in headers.items():
        response += f"{key}: {value}\r\n"
    response += "\r\n"
    return response.encode() + body_bytes


# ----------------------------------------------------------
# Custom 404 Not Found HTML page with client IP and group names
# ----------------------------------------------------------
def send_404(client_socket, client_addr, path):
    html = f"""<html>
<head>
    <meta charset="UTF-8">
    <title>Error 404</title>
</head>
<body style="text-align: center; font-family: Arial, sans-serif;">

    <h1 style="color:red;">The file is not found</h1>

    <p>Student Names and ID:</p>
    <p><b>Hanaa Jawad - ID: 1230263</b></p>
    <p><b>Yasmeen Badwan - ID: 1230271</b></p>
    <p><b>Sewar Masri - ID: 1231240</b></p>

    <p>Client Address:{client_addr[0]} : {client_addr[1]}</p>

</body>
</html>"""


 # The full HTML content is here (kept short for readability)

    status_line = "HTTP/1.1 404 Not Found"
    body = html.encode("utf-8")
    
    headers = {
        "Content-Type": "text/html; charset=utf-8",
        "Content-Length": str(len(body))
    }

    resp = response(status_line, headers, body)
    client_socket.sendall(resp)


# ----------------------------------------------------------
# Send a 307 Temporary Redirect (used for external websites)
# ----------------------------------------------------------
def redirect_307(client_socket, location):
    headers = {
        "Location": location,
        "Content-Length": "0"
    }
    status_line = "HTTP/1.1 307 Temporary Redirect"
    resp = response(status_line, headers, b"")
    client_socket.sendall(resp)


# ----------------------------------------------------------
# Serve static files: HTML, CSS, PNG, JPG, etc.
# ----------------------------------------------------------
def serve_file(client_socket, file_path):

    if not os.path.isfile(file_path):
        raise FileNotFoundError()

    ext = os.path.splitext(file_path)[1].lower()
    Myfile = MIME_TYPES.get(ext, "application/octet-stream")

    with open(file_path, "rb") as f:
        body = f.read()

    status_line = "HTTP/1.1 200 OK"
    headers = {
        "Content-Type": Myfile,
        "Content-Length": str(len(body))
    }

    resp = response(status_line, headers, body)
    client_socket.sendall(resp)


# ----------------------------------------------------------
# Hash passwords using SHA256 for secure user storage
# ----------------------------------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ----------------------------------------------------------
# Extract cookies from request headers
# ----------------------------------------------------------
def get_cookies(headers):
    cookies = {}
    cookie_header = headers.get("cookie", "")
    parts = cookie_header.split(";")
    for p in parts:
        if "=" in p:
            name, value = p.split("=", 1)
            cookies[name.strip()] = value.strip()
    return cookies


# ----------------------------------------------------------
# Handle user registration (GET → show form, POST → save user)
# ----------------------------------------------------------
def handle_register(method, headers, body, client_socket):

    # If user is just opening the page (GET)
    if method != "POST":
        file_path = os.path.join(STATIC_DIR, "register.html")
        try:
            serve_file(client_socket, file_path)
        except FileNotFoundError:
            send_404(client_socket, ("?", 0), "/register")
        return

    # If POST request, form data should be URL-encoded
    content_type = headers.get("content-type", "")
    if "application/x-www-form-urlencoded" not in content_type:
        file_path = os.path.join(STATIC_DIR, "register.html")
        serve_file(client_socket, file_path)
        return

    # Extract username and password from form
    form_data = urllib.parse.parse_qs(body.decode())
    username = form_data.get("username", [""])[0].strip()
    password = form_data.get("password", [""])[0].strip()

    # Reload page if fields are empty
    if not username or not password:
        serve_file(client_socket, os.path.join(STATIC_DIR, "register.html"))
        return

    # Load existing users
    users = {}
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                u, h = line.split(":", 1)
                users[u] = h 

    # Duplicate username check
    if username in users:
        serve_file(client_socket, os.path.join(STATIC_DIR, "register.html"))
        return

    # Save new user with hashed password
    hashed_pass = hash_password(password)
    with open(USER_FILE, "a", encoding="utf-8") as f:
        f.write(f"{username}:{hashed_pass}\n")

    # After registration → redirect to login page
    serve_file(client_socket, os.path.join(STATIC_DIR, "login.html"))


# ----------------------------------------------------------
# Handle user login and session creation
# ----------------------------------------------------------
def handle_login(method, headers, body, client_socket):
    # Show login page if GET request
    if method != "POST":
        serve_file(client_socket, os.path.join(STATIC_DIR, "login.html"))
        return
    # Process login form (POST)
    content_type = headers.get("content-type", "")
    if "application/x-www-form-urlencoded" in content_type:
        form_data = urllib.parse.parse_qs(body.decode())
        username = form_data.get("username", [""])[0]
        password = form_data.get("password", [""])[0]
        # Load users from data file
        users = {}
        if os.path.exists(USER_FILE):
            with open(USER_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    u, h = line.split(":", 1)
                    users[u] = h 
        # Verify login
        if username in users and users[username] == hash_password(password):

            # Create a session ID for logged-in user
            session_id = uuid.uuid4().hex
            sessions[session_id] = username

            # Load protected webpage
            file_path = os.path.join(STATIC_DIR, "protected.html")
            with open(file_path, "rb") as f:
                body_bytes = f.read()
            status_line = "HTTP/1.1 200 OK"
            headers_resp = {
                "Content-Type": "text/html; charset=utf-8",
                "Content-Length": str(len(body_bytes)),
                "Set-Cookie": f"session_id={session_id}; HttpOnly; Path=/"
            }
            resp = response(status_line, headers_resp, body_bytes)
            client_socket.sendall(resp)
            return
    # If login fails
    body_bytes = b"<h1>Login failed</h1><a href='/login.html'>Try again</a>"
    resp = response("HTTP/1.1 200 OK", {
        "Content-Type": "text/html; charset=utf-8",
        "Content-Length": str(len(body_bytes))
    }, body_bytes)
    client_socket.sendall(resp)


# ----------------------------------------------------------
# Check session before serving protected content
# ----------------------------------------------------------
def handle_protected(method, headers, body, client_socket):
    cookies = get_cookies(headers)
    session_id = cookies.get("session_id", "")

    if session_id in sessions:
        serve_file(client_socket, os.path.join(STATIC_DIR, "protected.html"))
    else:
        serve_file(client_socket, os.path.join(STATIC_DIR, "login.html"))


# ----------------------------------------------------------
# Remove session and redirect user to login page
# ----------------------------------------------------------
def handle_logout(method, headers, body, client_socket):
    cookies = get_cookies(headers)
    session_id = cookies.get("session_id", "")

    # Remove session from server memory
    if session_id in sessions:
        del sessions[session_id]

    # Delete cookie in the browser + redirect to login
    status_line = "HTTP/1.1 307 Temporary Redirect"
    headers_resp = {
        "Location": "/login.html",
        "Content-Length": "0",
        "Set-Cookie": "session_id=; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=/; HttpOnly"
    }

    resp = response(status_line, headers_resp, b"")
    client_socket.sendall(resp)


# ----------------------------------------------------------
# Main request handler: routing all paths
# ----------------------------------------------------------
def handle_client(client_socket, client_addr):
    try:
        data = client_socket.recv(65535)
        if not data:
            return
        log(f"===== NEW REQUEST FROM {client_addr[0]}:{client_addr[1]} =====")
        log(data.decode(errors="ignore"))
        # Parse HTTP request
        method, path, version, headers, body = request(data)
        # Remove query string (?x=y)
        path = path.split("?", 1)[0]
        # Route handling
        if path in ("/", "/index.html", "/main_en.html", "/en"):
            serve_file(client_socket, os.path.join(STATIC_DIR, "main_en.html"))
        elif path == "/ar":
            serve_file(client_socket, os.path.join(STATIC_DIR, "main_ar.html"))
        elif path == "/chat":
            redirect_307(client_socket, "https://chatgpt.com/")
        elif path == "/cf":
            redirect_307(client_socket, "https://www.cloudflare.com/")
        elif path == "/rt":
            redirect_307(client_socket, "https://ritaj.birzeit.edu/")
        elif path == "/register":
            handle_register(method, headers, body, client_socket)
        elif path == "/login":
            handle_login(method, headers, body, client_socket)
        elif path == "/protected.html":
            handle_protected(method, headers, body, client_socket)
        elif path == "/logout":
            handle_logout(method, headers, body, client_socket)
        else:
            # Serve any static file
            file_path = os.path.join(STATIC_DIR, path.lstrip("/"))
            serve_file(client_socket, file_path)
    except FileNotFoundError:
        send_404(client_socket, client_addr, path)
    except Exception as e:
        log(f"Error: {e}")
    finally:
        client_socket.close()


# ----------------------------------------------------------
# Start the server: create socket, listen, and handle clients
# ----------------------------------------------------------
def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        s.bind((HOST, PORT))
        s.listen(5)

        print(f"Serving on {HOST}:{PORT}")

        # Accept clients forever
        while True:
            client_socket, client_addr = s.accept()

            # Handle each request in a separate thread
            t = threading.Thread(
                target=handle_client,
                args=(client_socket, client_addr)
            )
            t.daemon = True
            t.start()


if __name__ == "__main__":
    main()
