import socket

try:
    ip = socket.gethostbyname("api.groq.com")
    print("Groq DNS Working:", ip)
except Exception as e:
    print("DNS Failed:", e)