import socket
from xml.etree import ElementTree as ET

# Define server IP address and port
SERVER_ADDRESS = ("localhost", 5005)  # Replace with actual server IP if needed
PORT = SERVER_ADDRESS[1]  # Extract port from address

# Create XML data
xml_data = """
<message>
  <sender>Client</sender>
  <content>This is some sample XML data</content>
</message>
"""

# Encode the XML data
encoded_data = xml_data.encode("utf-8")

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Send data to the server
sock.sendto(encoded_data, SERVER_ADDRESS)

print("Sent XML data to server:", SERVER_ADDRESS)

# Close the socket (optional, but recommended for proper resource management)
sock.close()
