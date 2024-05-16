import socket
from xml.etree import ElementTree as ET

# Define server IP address and port
SERVER_ADDRESS = ("localhost", 5000)  # Replace with actual server IP if needed
PORT = SERVER_ADDRESS[1]  # Extract port from address

# Create XML data
xml_data = """
<DOCUMENT>
<Client NameId="Client AA"/>
<Order Number="18" WorkPiece="P5" Quantity="2" DueDate="7" LatePen="10" EarlyPen="5"/>
<Order Number="19" WorkPiece="P6" Quantity="1" DueDate="4" LatePen="10" EarlyPen="10"/>
</DOCUMENT>
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
