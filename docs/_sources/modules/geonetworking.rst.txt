.. _geonetworking:

GeoNetworking (GN)
==================

GeoNetworking is the **routing layer** of the V2X protocol stack. Unlike traditional IP routing that uses 
addresses, GeoNetworking routes messages based on **geographic areas** — perfect for vehicular scenarios 
where you want to reach "all vehicles within 500 meters" rather than specific IP addresses.

.. note::

   GeoNetworking is defined in ETSI EN 302 636-4-1. It sits between the Link Layer (below) and 
   BTP/Facilities layers (above).

What GeoNetworking Does
-----------------------

- 📍 **Geographic addressing** — Send to areas, not addresses
- 🔄 **Position management** — Tracks your vehicle's location
- 📦 **Packet forwarding** — Routes packets based on position
- 🗺️ **Location table** — Maintains positions of nearby stations

Architecture
------------

GeoNetworking connects the Link Layer to upper protocol layers:

.. mermaid::

   flowchart LR
    BTP["Basic Transport Protocol (BTP)"]
    GN["Geonetworking"]
    LL["Link Layer"]
    BTP -->|"GNDataRequest"| GN
    GN -->|"GNDataIndication"| BTP
    GN -->|"send(packet: bytes)"| LL
    LL -->|"receive_callback(packet: bytes)"| GN
    LS["Location Service"]
    LS -->|GPSD TPV| GN

Key Components
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Component
     - Description
   * - **GN Router**
     - Main routing engine that processes incoming/outgoing packets
   * - **MIB**
     - Management Information Base — configuration parameters
   * - **GN Address**
     - Unique identifier combining station type and MAC address
   * - **Location Table**
     - Cache of known neighbor positions (updated from received packets)

----

Getting Started
---------------

Step 1: Configure the MIB
~~~~~~~~~~~~~~~~~~~~~~~~~

The MIB (Management Information Base) holds configuration for your GeoNetworking station.
The most important setting is your **GN Address**:

.. code-block:: python

   from flexstack.geonet.mib import MIB
   from flexstack.geonet.gn_address import GNAddress, M, ST, MID

   # Your station's MAC address (6 bytes)
   MAC_ADDRESS = b'\x00\x11\x22\x33\x44\x55'

   # Configure the MIB with your GN Address
   mib = MIB(
       itsGnLocalGnAddr=GNAddress(
           m=M.GN_MULTICAST,      # Addressing mode
           st=ST.CYCLIST,         # Station type (see table below)
           mid=MID(MAC_ADDRESS),  # Mobile ID from MAC
       ),
   )

**Station Types (ST):**

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Value
     - Constant
     - Description
   * - 0
     - ``UNKNOWN``
     - Unknown station type
   * - 1
     - ``PEDESTRIAN``
     - Pedestrian
   * - 2
     - ``CYCLIST``
     - Cyclist
   * - 3
     - ``MOPED``
     - Moped
   * - 4
     - ``MOTORCYCLE``
     - Motorcycle
   * - 5
     - ``PASSENGER_CAR``
     - Passenger car
   * - 6
     - ``BUS``
     - Bus
   * - 7
     - ``LIGHT_TRUCK``
     - Light truck
   * - 8
     - ``HEAVY_TRUCK``
     - Heavy truck
   * - 15
     - ``RSU``
     - Road Side Unit

Step 2: Create the Router
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from flexstack.geonet.router import Router as GNRouter

   # Create the GeoNetworking router
   gn_router = GNRouter(mib=mib, sign_service=None)

.. tip::

   The ``sign_service`` parameter is for security. Set to ``None`` for unsigned packets, 
   or pass a security service for signed V2X messages.

Step 3: Provide Position Updates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

GeoNetworking needs to know your current position. You can either:

**Option A: Manual updates** (for testing)

.. code-block:: python

   # GPSD-TPV format position data
   position = {
       'lat': 52.5200,    # Latitude (degrees)
       'lon': 13.4050,    # Longitude (degrees)
       'alt': 34.0,       # Altitude (meters)
       'speed': 0.0,      # Speed (m/s)
       'climb': 0.0,      # Vertical speed (m/s)
       'track': 0.0,      # Heading (degrees from north)
       'mode': 3          # Fix type: 3 = 3D fix
   }

   gn_router.refresh_ego_position_vector(position)

There is the ThreadStaticLocationService in ``flexstack.utils.static_location_service`` module that can be used to provide periodic manual updates.

.. code-block:: python

    from flexstack.utils.static_location_service import ThreadStaticLocationService

    # Create location service
    location_service = ThreadStaticLocationService(
        period=1000,  # milliseconds
        latitude=2.112104,
        longitude=41.386931,
    )
    # Register callback to update GN router
    location_service.add_callback(gn_router.refresh_ego_position_vector)

**Option B: Automatic updates** (recommended)

.. code-block:: python

   from flexstack.utils.static_location_service import GPSDLocationService

   # Create location service
   location_service = GPSDLocationService(
        gpsd_host="localhost",
        gpsd_port=2947,
    )

   # Register callback for automatic updates
   location_service.add_callback(gn_router.refresh_ego_position_vector)

Step 4: Connect to Link Layer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The GN Router needs a Link Layer to actually send and receive packets:

.. code-block:: python

   from flexstack.linklayer.raw_link_layer import RawLinkLayer

   # Create link layer (receives packets → forwards to GN router)
   link_layer = RawLinkLayer(
       iface="lo",
       mac_address=MAC_ADDRESS,
       receive_callback=gn_router.gn_data_indicate  # 👈 Incoming packets
   )

   # Connect GN router to link layer (for outgoing packets)
   gn_router.link_layer = link_layer  # 👈 Outgoing packets

----

Sending Packets
---------------

To send a GeoNetworking packet, create a ``GNDataRequest`` with all necessary parameters:

.. code-block:: python

   from flexstack.geonet.service_access_point import (
       GNDataRequest,
       CommonNH,
       PacketTransportType,
       CommunicationProfile,
       SecurityProfile,
       TrafficClass,
   )

   # Your payload
   payload = b"Hello, GeoNetworking!"

   # Create the request
   gn_request = GNDataRequest(
       upper_protocol_entity=CommonNH.ANY,
       packet_transport_type=PacketTransportType(),  # Default: Single Hop Broadcast
       communication_profile=CommunicationProfile.UNSPECIFIED,
       security_profile=SecurityProfile.NO_SECURITY,
       its_aid=0,
       security_permissions=b"\x00",
       traffic_class=TrafficClass(),
       length=len(payload),
       data=payload,
   )

   # Send it!
   gn_router.gn_data_request(gn_request)

**GNDataRequest Parameters:**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Parameter
     - Description
   * - ``upper_protocol_entity``
     - Next header type (usually ``CommonNH.BTP_A`` or ``CommonNH.BTP_B``)
   * - ``packet_transport_type``
     - How to route: broadcast, unicast, geo-broadcast, etc.
   * - ``communication_profile``
     - ITS communication profile
   * - ``security_profile``
     - Whether to sign/encrypt the packet
   * - ``its_aid``
     - ITS Application ID (identifies the service)
   * - ``traffic_class``
     - Priority and channel settings
   * - ``data``
     - The actual payload bytes

----

Receiving Packets
-----------------

Register a callback to handle incoming GeoNetworking packets:

.. code-block:: python

   from flexstack.geonet.service_access_point import GNDataIndication

   def on_gn_packet_received(indication: GNDataIndication):
       """Called when a GeoNetworking packet arrives."""
       print(f"📥 Received GN packet!")
       print(f"   Source: {indication.source_position_vector}")
       print(f"   Data: {indication.data.hex()}")

   # Register the callback
   gn_router.register_indication_callback(on_gn_packet_received)

.. note::

   In practice, you rarely handle GN packets directly. Instead, you connect a **BTP Router** 
   which demultiplexes packets to the appropriate facilities service (CAM, DENM, etc.).

----

Complete Example
----------------

Here's a complete script that sends and receives GeoNetworking packets:

.. code-block:: python
   :linenos:

   #!/usr/bin/env python3
   """
   GeoNetworking Example
   
   Demonstrates sending and receiving GN packets over C-V2X.
   """

   import time
   from flexstack.linklayer.cv2x_link_layer import PythonCV2XLinkLayer
   from flexstack.geonet.router import Router as GNRouter
   from flexstack.geonet.mib import MIB
   from flexstack.geonet.gn_address import GNAddress, M, ST, MID
   from flexstack.geonet.service_access_point import (
       GNDataRequest,
       GNDataIndication,
       CommonNH,
       PacketTransportType,
       CommunicationProfile,
       SecurityProfile,
       TrafficClass,
   )

   MAC_ADDRESS = b'\x00\x11\x22\x33\x44\x55'


   def on_gn_packet_received(indication: GNDataIndication):
       """Handle incoming GeoNetworking packets."""
       print(f"📥 Received GN packet: {indication.data[:20].hex()}...")


   def main():
       # Step 1: Configure MIB
       mib = MIB(
           itsGnLocalGnAddr=GNAddress(
               m=M.GN_MULTICAST,
               st=ST.CYCLIST,
               mid=MID(MAC_ADDRESS),
           ),
       )

       # Step 2: Create GN Router
       gn_router = GNRouter(mib=mib, sign_service=None)
       gn_router.register_indication_callback(on_gn_packet_received)

       # Step 3: Provide position (manual for this example)
       position = {
           'lat': 52.5200,
           'lon': 13.4050,
           'alt': 34.0,
           'speed': 0.0,
           'climb': 0.0,
           'track': 0.0,
           'mode': 3
       }
       gn_router.refresh_ego_position_vector(position)

       # Step 4: Connect Link Layer
       link_layer = PythonCV2XLinkLayer(
           receive_callback=gn_router.gn_data_indicate
       )
       gn_router.link_layer = link_layer

       print("✅ GeoNetworking router active")
       print("📡 Sending packets every second...")
       print("Press Ctrl+C to exit\n")

       try:
           while True:
               # Create payload
               payload = bytes([i % 256 for i in range(100)])

               # Build GN request
               gn_request = GNDataRequest(
                   upper_protocol_entity=CommonNH.ANY,
                   packet_transport_type=PacketTransportType(),
                   communication_profile=CommunicationProfile.UNSPECIFIED,
                   security_profile=SecurityProfile.NO_SECURITY,
                   its_aid=0,
                   security_permissions=b"\x00",
                   traffic_class=TrafficClass(),
                   length=len(payload),
                   data=payload,
               )

               # Send packet
               gn_router.gn_data_request(gn_request)
               print(f"📤 Sent GN packet: {payload[:20].hex()}...")

               time.sleep(1)

       except KeyboardInterrupt:
           print("\n👋 Shutting down...")

       # Cleanup
       del link_layer.link_layer
       time.sleep(2)
       print("✅ Shutdown complete")


   if __name__ == "__main__":
       main()

----

See Also
--------

- :doc:`/getting_started` — Complete tutorial building a V2X application
- :doc:`link_layer` — Link Layer implementations (RawLinkLayer, C-V2X)
- :doc:`btp` — Basic Transport Protocol for port multiplexing