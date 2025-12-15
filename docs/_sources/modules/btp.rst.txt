.. _btp:

Basic Transport Protocol (BTP)
==============================

BTP is the **transport layer** of the V2X protocol stack. Think of it like UDP for V2X — it provides 
**port-based multiplexing** so multiple services (CAM, DENM, etc.) can share the same GeoNetworking layer.

.. note::

   BTP is defined in ETSI EN 302 636-5-1. It sits between GeoNetworking (below) and 
   Facilities services like CAM and DENM (above).

What BTP Does
-------------

- 🔀 **Port multiplexing** — Routes packets to the correct service based on port numbers
- 📨 **Simple delivery** — Lightweight, connectionless transport (like UDP)
- 🏷️ **Service identification** — Well-known ports for standard services (CAM=2001, DENM=2002, etc.)

Architecture
------------

BTP connects GeoNetworking to upper-layer services:

.. mermaid::

    flowchart LR
        FAC["Facilities Service<br/>(CAM, DENM, etc.)"]
        BTP["Basic Transport Protocol (BTP)"]
        GN["GeoNetworking Layer"]

        FAC -->|BTPDataRequest| BTP
        BTP -->|GNDataRequest | GN
        GN -->|GNDataIndication| BTP
        BTP -->|BTPDataIndication| FAC

BTP Types
~~~~~~~~~

BTP defines two packet types:

.. list-table::
   :header-rows: 1
   :widths: 15 25 60

   * - Type
     - Constant
     - Description
   * - BTP-A
     - ``CommonNH.BTP_A``
     - Interactive packet transport (with source port for replies)
   * - BTP-B
     - ``CommonNH.BTP_B``
     - Non-interactive packet transport (broadcast, no reply expected)

Most V2X services use **BTP-B** since CAMs and DENMs are broadcast without expecting replies.

Well-Known Ports
~~~~~~~~~~~~~~~~

.. list-table::
    :header-rows: 1
    :widths: 15 25 60

    * - Port
      - Service
      - Description
    * - 2001
      - CA (CAM)
      - Cooperative Awareness Messages
    * - 2002
      - DEN (DENM)
      - Decentralized Environmental Notifications
    * - 2003
      - RLT (MAPEM)
      - Road and Lane Topology
    * - 2004
      - TLM (SPATEM)
      - Traffic Light Maneuver
    * - 2005
      - SA (SAEM)
      - Service Announcement
    * - 2006
      - IVI (IVIM)
      - Infrastructure to Vehicle Information
    * - 2007
      - TLC (SREM)
      - Traffic Light Control
    * - 2008
      - TLC (SSEM)
      - Signal Status Extension Message
    * - 2009
      - CP (CPM)
      - Collective Perception Service
    * - 2010
      - EVCSN POI
      - EV Charging Station Notification
    * - 2011
      - TPG (TRM, TCM, VDRM, VDPM, EOFM)
      - Tow-Away and Parking Guidance
    * - 2012
      - Charging (EV-RSR)
      - EV Roaming Service Request
    * - 2013
      - GPC (RTCMEM)
      - GNSS Positioning Correction
    * - 2014
      - CTL (CTLM)
      - Certificate Trust List Message
    * - 2015
      - CRL (CRLM)
      - Certificate Revocation List Message
    * - 2016
      - EC/AT Request
      - Enrollment and Authorization Ticket Request
    * - 2017
      - MCD (MCDM)
      - Misbehavior Complaint Data Message
    * - 2018
      - VA (VAM)
      - Vulnerable Road User Awareness Message
    * - 2019
      - IMZ (IMZM)
      - Imminent Safety-Related Condition Indication

----

Getting Started
---------------

Step 1: Create GeoNetworking Router
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

BTP requires a GeoNetworking router underneath:

.. code-block:: python

   from flexstack.geonet.router import Router as GNRouter
   from flexstack.geonet.mib import MIB
   from flexstack.geonet.gn_address import GNAddress, M, ST, MID

   MAC_ADDRESS = b'\x00\x11\x22\x33\x44\x55'

   mib = MIB(
       itsGnLocalGnAddr=GNAddress(
           m=M.GN_MULTICAST,
           st=ST.CYCLIST,
           mid=MID(MAC_ADDRESS),
       ),
   )
   gn_router = GNRouter(mib=mib, sign_service=None)

Step 2: Create BTP Router
~~~~~~~~~~~~~~~~~~~~~~~~~

Create the BTP router and connect it to GeoNetworking:

.. code-block:: python

   from flexstack.btp.router import Router as BTPRouter

   # Create BTP router on top of GN
   btp_router = BTPRouter(gn_router)

   # Connect GN indications to BTP (incoming packets)
   gn_router.register_indication_callback(btp_router.btp_data_indication)

Step 3: Register Port Callbacks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Register callbacks for the ports you want to receive on:

.. code-block:: python

   from flexstack.btp.service_access_point import BTPDataIndication

   def on_cam_received(indication: BTPDataIndication):
       """Handle incoming CAM packets (port 2001)."""
       print(f"📥 CAM received: {indication.data.hex()}")

   def on_denm_received(indication: BTPDataIndication):
       """Handle incoming DENM packets (port 2002)."""
       print(f"⚠️ DENM received: {indication.data.hex()}")

   # Register callbacks for specific ports
   btp_router.register_indication_callback_btp(port=2001, callback=on_cam_received)
   btp_router.register_indication_callback_btp(port=2002, callback=on_denm_received)

Step 4: Freeze Callbacks
~~~~~~~~~~~~~~~~~~~~~~~~

Before any packets flow, you **must** freeze the callback registry:

.. code-block:: python

   # Lock the callback registry (required before sending/receiving)
   btp_router.freeze_callbacks()

.. warning::

   Always call ``freeze_callbacks()`` after registering all port callbacks and before 
   starting the link layer. This ensures thread safety and optimal performance.

Step 5: Connect Link Layer
~~~~~~~~~~~~~~~~~~~~~~~~~~

Finally, connect the GN router to a link layer:

.. code-block:: python

   from flexstack.linklayer.raw_link_layer import RawLinkLayer

   link_layer = RawLinkLayer(
       iface="lo",
       mac_address=MAC_ADDRESS,
       receive_callback=gn_router.gn_data_indicate
   )
   gn_router.link_layer = link_layer

----

Sending Packets
---------------

To send a BTP packet, create a ``BTPDataRequest``:

.. code-block:: python

   from flexstack.btp.service_access_point import BTPDataRequest
   from flexstack.geonet.service_access_point import (
       Area,
       PacketTransportType,
       CommunicationProfile,
       TrafficClass,
       CommonNH,
   )
   from flexstack.geonet.gn_address import GNAddress

   # Your payload
   payload = b"Hello, BTP!"

   # Create BTP request
   btp_request = BTPDataRequest(
       btp_type=CommonNH.BTP_B,              # Non-interactive (broadcast)
       source_port=0,                         # Not used for BTP-B
       destination_port=2001,                 # Target port (e.g., CAM port)
       destination_port_info=0,
       gn_packet_transport_type=PacketTransportType(),
       gn_destination_address=GNAddress(),
       gn_area=Area(),
       communication_profile=CommunicationProfile.UNSPECIFIED,
       traffic_class=TrafficClass(),
       length=len(payload),
       data=payload,
   )

   # Send it!
   btp_router.btp_data_request(btp_request)

**BTPDataRequest Parameters:**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Parameter
     - Description
   * - ``btp_type``
     - ``BTP_A`` (interactive) or ``BTP_B`` (non-interactive)
   * - ``source_port``
     - Source port (used for BTP-A replies, 0 for BTP-B)
   * - ``destination_port``
     - Target port number (e.g., 2001 for CAM)
   * - ``destination_port_info``
     - Additional port info (usually 0)
   * - ``gn_packet_transport_type``
     - GeoNetworking transport type (broadcast, unicast, etc.)
   * - ``gn_destination_address``
     - GN destination (for unicast)
   * - ``gn_area``
     - Geographic area (for geo-broadcast)
   * - ``traffic_class``
     - Priority and channel settings
   * - ``data``
     - Payload bytes

----

Receiving Packets
-----------------

Incoming packets are delivered to the registered callback for that port:

.. code-block:: python

   from flexstack.btp.service_access_point import BTPDataIndication

   def on_packet_received(indication: BTPDataIndication):
       """Called when a packet arrives on our registered port."""
       print(f"📥 Received on port {indication.destination_port}")
       print(f"   Source port: {indication.source_port}")
       print(f"   Data length: {len(indication.data)} bytes")
       print(f"   Payload: {indication.data.hex()}")

   # Register for a specific port
   btp_router.register_indication_callback_btp(
       port=1234,
       callback=on_packet_received
   )

**BTPDataIndication Fields:**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Field
     - Description
   * - ``btp_type``
     - BTP-A or BTP-B
   * - ``source_port``
     - Sender's port (BTP-A only)
   * - ``destination_port``
     - Port this packet was sent to
   * - ``destination_port_info``
     - Additional port info
   * - ``data``
     - Payload bytes

----

Complete Example
----------------

Here's a complete script that sends and receives BTP packets:

.. code-block:: python
   :linenos:

   #!/usr/bin/env python3
   """
   BTP Example
   
   Demonstrates sending and receiving BTP packets over GeoNetworking.
   """

   import time
   from flexstack.linklayer.raw_link_layer import RawLinkLayer
   from flexstack.geonet.router import Router as GNRouter
   from flexstack.geonet.mib import MIB
   from flexstack.geonet.gn_address import GNAddress, M, ST, MID
   from flexstack.btp.router import Router as BTPRouter
   from flexstack.btp.service_access_point import BTPDataRequest, BTPDataIndication
   from flexstack.geonet.service_access_point import (
       Area,
       PacketTransportType,
       CommunicationProfile,
       TrafficClass,
       CommonNH,
   )

   MAC_ADDRESS = b'\x00\x11\x22\x33\x44\x55'
   MY_PORT = 1234


   def on_btp_received(indication: BTPDataIndication):
       """Handle incoming BTP packets."""
       print(f"📥 Received BTP on port {indication.destination_port}")
       print(f"   Data: {indication.data[:20].hex()}...")


   def main():
       # Step 1: Create GN Router
       mib = MIB(
           itsGnLocalGnAddr=GNAddress(
               m=M.GN_MULTICAST,
               st=ST.CYCLIST,
               mid=MID(MAC_ADDRESS),
           ),
       )
       gn_router = GNRouter(mib=mib, sign_service=None)

       # Step 2: Create BTP Router
       btp_router = BTPRouter(gn_router)
       gn_router.register_indication_callback(btp_router.btp_data_indication)

       # Step 3: Register port callback
       btp_router.register_indication_callback_btp(
           port=MY_PORT,
           callback=on_btp_received
       )

       # Step 4: Freeze callbacks (required!)
       btp_router.freeze_callbacks()

       # Step 5: Connect Link Layer
       link_layer = RawLinkLayer(
           iface="lo",
           mac_address=MAC_ADDRESS,
           receive_callback=gn_router.gn_data_indicate,
       )
       gn_router.link_layer = link_layer

       print("✅ BTP Router active")
       print(f"📡 Listening on port {MY_PORT}")
       print("Press Ctrl+C to exit\n")

       try:
           while True:
               # Create payload
               payload = bytes([i % 256 for i in range(100)])

               # Build BTP request
               btp_request = BTPDataRequest(
                   btp_type=CommonNH.BTP_B,
                   source_port=0,
                   destination_port=MY_PORT,
                   destination_port_info=0,
                   gn_packet_transport_type=PacketTransportType(),
                   gn_destination_address=GNAddress(),
                   gn_area=Area(),
                   communication_profile=CommunicationProfile.UNSPECIFIED,
                   traffic_class=TrafficClass(),
                   length=len(payload),
                   data=payload,
               )

               # Send packet
               btp_router.btp_data_request(btp_request)
               print(f"📤 Sent BTP to port {MY_PORT}: {payload[:20].hex()}...")

               time.sleep(1)

       except KeyboardInterrupt:
           print("\n👋 Shutting down...")

       # Cleanup
       link_layer.sock.close()
       print("✅ Shutdown complete")


   if __name__ == "__main__":
       main()

----

Integration with Facilities
---------------------------

In practice, you rarely use BTP directly. Instead, Facilities services (CAM, DENM) use BTP internally:

.. code-block:: python

   from flexstack.facilities.ca_basic_service.ca_basic_service import (
       CooperativeAwarenessBasicService,
   )

   # CA Basic Service uses BTP internally on port 2001
   ca_service = CooperativeAwarenessBasicService(
       btp_router=btp_router,  # 👈 Pass BTP router
       vehicle_data=vehicle_data,
       ldm=ldm,
   )

See the :doc:`/getting_started` tutorial for a complete example with CAM.

----

See Also
--------

- :doc:`/getting_started` — Complete tutorial building a V2X application
- :doc:`geonetworking` — GeoNetworking layer (underneath BTP)
- :doc:`/modules/facilities/ca_basic_service` — CA Basic Service (uses BTP port 2001)
- :doc:`/modules/facilities/den_service` — DEN Service (uses BTP port 2002)
