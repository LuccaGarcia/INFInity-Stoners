import socket
from xml.etree import ElementTree as ET

# Define server port
PORT = 5005  # You can change this port as needed

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
sock.bind(("", PORT))

print("UDP Server listening on port:", PORT)

while True:
    # Receive data from the socket
    data, address = sock.recvfrom(1024)

    # Decode the received data
    xml_data = data.decode("utf-8")

    # Parse the XML data
    try:
        root = ET.fromstring(xml_data)

        # Access and process the XML data here
        print("Received XML data:")
        print(ET.tostring(root, encoding="utf-8").decode("utf-8"))

    except ET.ParseError as e:
        print("Error parsing XML data:", e)

    # Additional processing or handling of the received data can be done here

