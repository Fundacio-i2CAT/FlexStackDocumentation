.. _rawlinklayer_ethernet:

Ethernet Deployment with RawLinkLayer
=====================================

Send and receive V2X messages over **real Ethernet networks** using FlexStack's ``RawLinkLayer``. 
This guide covers network interface selection, permissions, and troubleshooting.

.. important::

   The ``RawLinkLayer`` only works on **Linux-based operating systems** (Ubuntu, Debian, etc.). 
   It requires root privileges to access raw sockets.

How It Works
------------

The ``RawLinkLayer`` sends V2X messages as raw Ethernet frames:

.. mermaid::

   flowchart LR
       subgraph "FlexStack"
           APP[Application]
           FAC[Facilities<br/>CAM/VAM/DENM]
           BTP[BTP Router]
           GN[GeoNetworking]
           LL[RawLinkLayer]
       end
       
       subgraph "Operating System"
           SOCK[Raw Socket]
           NIC[Network Interface<br/>eth0 / wlan0]
       end
       
       subgraph "Network"
           ETH[Ethernet<br/>Frames]
       end
       
       APP --> FAC --> BTP --> GN --> LL
       LL --> SOCK --> NIC --> ETH
       
       style LL fill:#e3f2fd,stroke:#1565c0
       style NIC fill:#fff3e0,stroke:#e65100

----

Quick Start
-----------

Step 1: Find Your Network Interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

List available network interfaces:

.. code-block:: bash

   ip link show

**Example output:**

.. code-block:: text

   1: lo: <LOOPBACK,UP,LOWER_UP> ...
   2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> ...
   3: wlan0: <BROADCAST,MULTICAST,UP,LOWER_UP> ...

Or use the routing table to find the default interface:

.. code-block:: bash

   route -n | head -3

**Example output:**

.. code-block:: text

   Kernel IP routing table
   Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
   0.0.0.0         192.168.1.1     0.0.0.0         UG    100    0        0 eth0

The ``Iface`` column shows your active network interface.

**Common Interface Names:**

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Interface
     - Description
   * - ``lo``
     - Loopback (for local testing)
   * - ``eth0``
     - First Ethernet adapter
   * - ``enp0s3``
     - Ethernet (predictable naming)
   * - ``wlan0``
     - First WiFi adapter
   * - ``wlp2s0``
     - WiFi (predictable naming)

Step 2: Create Your Application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python
   :linenos:

   #!/usr/bin/env python3
   """
   RawLinkLayer Ethernet Example
   
   Sends VAMs over a real network interface.
   Run with: sudo python ethernet_example.py
   """

   import logging
   import time

   from flexstack.linklayer.raw_link_layer import RawLinkLayer
   from flexstack.geonet.router import Router as GNRouter
   from flexstack.geonet.mib import MIB
   from flexstack.geonet.gn_address import GNAddress, M, ST, MID
   from flexstack.btp.router import Router as BTPRouter
   from flexstack.utils.static_location_service import ThreadStaticLocationService
   from flexstack.facilities.vru_awareness_service.vru_awareness_service import (
       VRUAwarenessService,
   )
   from flexstack.facilities.vru_awareness_service.vam_transmission_management import (
       DeviceDataProvider,
   )

   logging.basicConfig(level=logging.INFO)

   # ============ Configuration ============ #
   
   INTERFACE = "eth0"                        # ← Change this to your interface
   MAC_ADDRESS = b"\xaa\xbb\xcc\x11\x22\x33" # ← Your MAC address
   STATION_ID = 1
   POSITION = [41.386931, 2.112104]          # Barcelona


   def main():
       # GeoNetworking
       mib = MIB(
           itsGnLocalGnAddr=GNAddress(
               m=M.GN_MULTICAST,
               st=ST.CYCLIST,
               mid=MID(MAC_ADDRESS),
           ),
       )
       gn_router = GNRouter(mib=mib, sign_service=None)

       # Link Layer - connects to real network!
       link_layer = RawLinkLayer(
           iface=INTERFACE,
           mac_address=MAC_ADDRESS,
           receive_callback=gn_router.gn_data_indicate,
       )
       gn_router.link_layer = link_layer

       # BTP
       btp_router = BTPRouter(gn_router)
       gn_router.register_indication_callback(btp_router.btp_data_indication)

       # Location Service
       location_service = ThreadStaticLocationService(
           period=1000,
           latitude=POSITION[0],
           longitude=POSITION[1],
       )
       location_service.add_callback(gn_router.refresh_ego_position_vector)

       # VRU Awareness Service
       device_data = DeviceDataProvider(
           station_id=STATION_ID,
           station_type=2,  # Cyclist
       )
       vru_service = VRUAwarenessService(
           btp_router=btp_router,
           device_data_provider=device_data,
       )
       location_service.add_callback(
           vru_service.vam_transmission_management.location_service_callback
       )

       print(f"✅ Sending VAMs on interface: {INTERFACE}")
       print(f"📡 MAC Address: {MAC_ADDRESS.hex(':')}")
       print("Press Ctrl+C to stop\n")

       try:
           location_service.location_service_thread.join()
       except KeyboardInterrupt:
           print("\n👋 Stopping...")

       location_service.stop_event.set()
       link_layer.sock.close()


   if __name__ == "__main__":
       main()

Step 3: Run with Root Privileges
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Raw sockets require root access. You have two options:

**Option 1: Use sudo directly**

.. code-block:: bash

   sudo python ethernet_example.py

Or if using a virtual environment:

.. code-block:: bash

   sudo env PATH=$PATH python ethernet_example.py

**Option 2: Switch to root user**

.. code-block:: bash

   sudo su
   source venv/bin/activate
   python ethernet_example.py

----

Common Errors
-------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Error
     - Solution
   * - ``PermissionError: [Errno 1] Operation not permitted``
     - Run with ``sudo`` — raw sockets need root
   * - ``AttributeError: 'RawLinkLayer' object has no attribute 'sock'``
     - Same as above — socket creation failed due to permissions
   * - ``OSError: [Errno 19] No such device``
     - Interface name is wrong — check with ``ip link show``
   * - ``OSError: [Errno 99] Cannot assign requested address``
     - Interface is down — bring it up with ``sudo ip link set eth0 up``

----

Testing Locally
---------------

For development, use the **loopback interface** (``lo``):

.. code-block:: python

   link_layer = RawLinkLayer(
       iface="lo",  # Loopback for local testing
       mac_address=MAC_ADDRESS,
       receive_callback=gn_router.gn_data_indicate,
   )

This allows you to test without a real network, though messages won't leave your machine.

----

Two-Station Test
----------------

Test V2X communication between two terminals on the same machine:

**Terminal 1 — Station A:**

.. code-block:: bash

   sudo python station.py --station-id 1 --interface eth0

**Terminal 2 — Station B:**

.. code-block:: bash

   sudo python station.py --station-id 2 --interface eth0

Both stations should see each other's messages in the logs!

.. mermaid::

   sequenceDiagram
       participant A as Station A<br/>(Terminal 1)
       participant NET as eth0<br/>Network
       participant B as Station B<br/>(Terminal 2)
       
       A->>NET: VAM (Station 1)
       NET->>B: Receive VAM
       B->>NET: VAM (Station 2)
       NET->>A: Receive VAM
       
       Note over A,B: Both stations see each other

----

Network Capture
---------------

Use **Wireshark** or **tcpdump** to inspect V2X packets:

.. code-block:: bash

   # Capture GeoNetworking packets (EtherType 0x8947)
   sudo tcpdump -i eth0 ether proto 0x8947 -v

**Example output:**

.. code-block:: text

   14:32:15.123456 aa:bb:cc:11:22:33 > ff:ff:ff:ff:ff:ff, ethertype Unknown (0x8947), length 128
   14:32:15.623456 aa:bb:cc:11:22:34 > ff:ff:ff:ff:ff:ff, ethertype Unknown (0x8947), length 132

Or capture to a file for Wireshark:

.. code-block:: bash

   sudo tcpdump -i eth0 ether proto 0x8947 -w v2x_capture.pcap

----

MAC Address Configuration
-------------------------

You can use any MAC address, but for proper operation:

**Random locally-administered MAC:**

.. code-block:: python

   import random

   def generate_random_mac() -> bytes:
       octets = [random.randint(0x00, 0xFF) for _ in range(6)]
       # Set locally administered bit, clear multicast bit
       octets[0] = (octets[0] & 0xFE) | 0x02
       return bytes(octets)

   MAC_ADDRESS = generate_random_mac()

**Parse from string:**

.. code-block:: python

   def parse_mac(mac_str: str) -> bytes:
       """Convert 'aa:bb:cc:dd:ee:ff' to bytes."""
       return bytes(int(x, 16) for x in mac_str.split(":"))

   MAC_ADDRESS = parse_mac("aa:bb:cc:11:22:33")

**Use your real MAC:**

.. code-block:: bash

   # Find your MAC address
   ip link show eth0 | grep ether

.. code-block:: text

   link/ether 00:1a:2b:3c:4d:5e brd ff:ff:ff:ff:ff:ff

----

Complete Example
----------------

Here's a complete station with command-line arguments:

.. code-block:: python
   :linenos:

   #!/usr/bin/env python3
   """
   FlexStack Ethernet Station
   
   Usage:
       sudo python station.py --interface eth0 --station-id 1
   """

   import argparse
   import logging
   import random
   import time

   from flexstack.linklayer.raw_link_layer import RawLinkLayer
   from flexstack.geonet.router import Router as GNRouter
   from flexstack.geonet.mib import MIB
   from flexstack.geonet.gn_address import GNAddress, M, ST, MID
   from flexstack.btp.router import Router as BTPRouter
   from flexstack.utils.static_location_service import ThreadStaticLocationService
   from flexstack.facilities.vru_awareness_service.vru_awareness_service import (
       VRUAwarenessService,
   )
   from flexstack.facilities.vru_awareness_service.vam_transmission_management import (
       DeviceDataProvider,
   )


   def parse_mac(mac_str: str) -> bytes:
       return bytes(int(x, 16) for x in mac_str.split(":"))


   def generate_random_mac() -> bytes:
       octets = [random.randint(0x00, 0xFF) for _ in range(6)]
       octets[0] = (octets[0] & 0xFE) | 0x02
       return bytes(octets)


   def main():
       parser = argparse.ArgumentParser(description="FlexStack Ethernet Station")
       parser.add_argument(
           "--interface", "-i",
           type=str,
           default="eth0",
           help="Network interface (e.g., eth0, wlan0, lo)",
       )
       parser.add_argument(
           "--station-id", "-s",
           type=int,
           default=random.randint(1, 2147483647),
           help="Station ID (default: random)",
       )
       parser.add_argument(
           "--mac-address", "-m",
           type=str,
           default=None,
           help="MAC address (e.g., aa:bb:cc:dd:ee:ff)",
       )
       parser.add_argument(
           "--latitude",
           type=float,
           default=41.386931,
           help="Latitude in degrees",
       )
       parser.add_argument(
           "--longitude",
           type=float,
           default=2.112104,
           help="Longitude in degrees",
       )
       parser.add_argument(
           "--debug",
           action="store_true",
           help="Enable debug logging",
       )
       args = parser.parse_args()

       # Setup logging
       logging.basicConfig(
           level=logging.DEBUG if args.debug else logging.INFO,
           format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
           datefmt="%H:%M:%S",
       )
       logger = logging.getLogger("station")

       # MAC address
       if args.mac_address:
           mac = parse_mac(args.mac_address)
       else:
           mac = generate_random_mac()

       logger.info(f"🚀 Starting station {args.station_id}")
       logger.info(f"📡 Interface: {args.interface}")
       logger.info(f"🔗 MAC: {mac.hex(':')}")
       logger.info(f"📍 Position: {args.latitude}, {args.longitude}")

       # GeoNetworking
       mib = MIB(
           itsGnLocalGnAddr=GNAddress(
               m=M.GN_MULTICAST,
               st=ST.CYCLIST,
               mid=MID(mac),
           ),
       )
       gn_router = GNRouter(mib=mib, sign_service=None)

       # Link Layer
       try:
           link_layer = RawLinkLayer(
               iface=args.interface,
               mac_address=mac,
               receive_callback=gn_router.gn_data_indicate,
           )
       except PermissionError:
           logger.error("❌ Permission denied! Run with sudo.")
           return
       except OSError as e:
           logger.error(f"❌ Failed to open interface: {e}")
           return

       gn_router.link_layer = link_layer

       # BTP
       btp_router = BTPRouter(gn_router)
       gn_router.register_indication_callback(btp_router.btp_data_indication)

       # Location Service
       location_service = ThreadStaticLocationService(
           period=1000,
           latitude=args.latitude,
           longitude=args.longitude,
       )
       location_service.add_callback(gn_router.refresh_ego_position_vector)

       # VRU Awareness Service
       device_data = DeviceDataProvider(
           station_id=args.station_id,
           station_type=2,
       )
       vru_service = VRUAwarenessService(
           btp_router=btp_router,
           device_data_provider=device_data,
       )
       location_service.add_callback(
           vru_service.vam_transmission_management.location_service_callback
       )

       logger.info("✅ Station running! Press Ctrl+C to stop.\n")

       try:
           while True:
               time.sleep(1)
       except KeyboardInterrupt:
           logger.info("\n👋 Shutting down...")

       location_service.stop_event.set()
       location_service.location_service_thread.join()
       link_layer.sock.close()
       logger.info("Goodbye!")


   if __name__ == "__main__":
       main()

**Usage:**

.. code-block:: bash

   # Basic usage
   sudo python station.py --interface eth0

   # With custom settings
   sudo python station.py \
       --interface wlan0 \
       --station-id 42 \
       --mac-address aa:bb:cc:dd:ee:ff \
       --latitude 48.8566 \
       --longitude 2.3522 \
       --debug

----

See Also
--------

- :doc:`/getting_started` — Complete V2X tutorial
- :doc:`/modules/link_layer` — Link Layer documentation
- :doc:`docker-deployment` — Deploy in Docker containers
- :doc:`logging` — Configure logging output
