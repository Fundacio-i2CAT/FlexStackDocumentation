.. _link_layer:

Link Layer
==========

The Link Layer is the foundation of V2X communication — it's responsible for actually sending and receiving 
packets over the air (or wire). Think of it as the "radio" of your V2X stack.

.. note::

   The Link Layer sits at the bottom of the protocol stack. All messages from GeoNetworking eventually 
   pass through here to reach other vehicles.

Choosing a Link Layer
---------------------

FlexStack® provides two Link Layer implementations for different scenarios:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Implementation
     - Use Case
     - Requirements
   * - ``RawLinkLayer``
     - Testing, development, IEEE 802.11p (ITS-G5)
     - Linux with raw socket support
   * - ``PythonCV2XLinkLayer``
     - Production C-V2X communication
     - Qualcomm ``telux_cv2x`` SDK

Architecture
------------

Both implementations inherit from a common ``LinkLayer`` base class:

.. mermaid::

    classDiagram
        direction TB
        class LinkLayer {
            <<abstract>>
            +receive_callback: Callable[[bytes], None]
            +send(packet: bytes)*
        }
        class RawLinkLayer {
            +iface: str
            +mac_address: bytes
            +send(packet: bytes)
        }
        class PythonCV2XLinkLayer {
            +send(packet: bytes)
        }
        
        LinkLayer <|-- RawLinkLayer : implements
        LinkLayer <|-- PythonCV2XLinkLayer : implements

The key concept is simple:

- **send()** — Transmit a packet
- **receive_callback** — Function called when a packet arrives

This design makes it easy to swap implementations without changing your application code.

----

RawLinkLayer
------------

The ``RawLinkLayer`` uses Linux raw sockets to send and receive Ethernet frames directly. 
It's perfect for:

- 🧪 **Testing** on loopback (``lo``) interface
- 🔌 **Wired setups** using Ethernet or virtual interfaces (veth)
- 📡 **ITS-G5** when using an 802.11p OCB interface

Quick Start
~~~~~~~~~~~

.. code-block:: python

    from flexstack.linklayer.raw_link_layer import RawLinkLayer

    def on_packet_received(packet: bytes):
        print(f"📥 Received: {packet.hex()}")

    # Create link layer on loopback interface
    link_layer = RawLinkLayer(
        iface="lo",                    # Network interface
        mac_address=b'\xAA\xBB\xCC\xDD\xEE\xFF',
        receive_callback=on_packet_received
    )

    # Send a packet
    link_layer.send(b"Hello V2X!")

Parameters
~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Parameter
     - Type
     - Description
   * - ``iface``
     - ``str``
     - Network interface name (e.g., ``"lo"``, ``"eth0"``, ``"wlan0"``)
   * - ``mac_address``
     - ``bytes``
     - 6-byte MAC address for this station
   * - ``receive_callback``
     - ``Callable``
     - Function called with received packet bytes

Complete Example
~~~~~~~~~~~~~~~~

.. code-block:: python

    import time
    from flexstack.linklayer.raw_link_layer import RawLinkLayer

    def on_packet_received(packet: bytes):
        print(f"📥 Received packet: {packet.hex()}")

    if __name__ == "__main__":
        MAC_ADDRESS = b'\xAA\xBB\xCC\xDD\xEE\xFF'
        
        link_layer = RawLinkLayer(
            iface="lo",
            mac_address=MAC_ADDRESS,
            receive_callback=on_packet_received
        )

        print("📡 RawLinkLayer running on loopback interface")
        print("Press Ctrl+C to exit\n")

        try:
            while True:
                # Send test packet
                data = bytes([i % 256 for i in range(100)])
                link_layer.send(data)
                print(f"📤 Sent packet: {data[:10].hex()}...")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Exiting...")

.. tip::

   For testing two stations locally, create a virtual Ethernet pair:
   
   .. code-block:: bash

      sudo ip link add veth0 type veth peer name veth1
      sudo ip link set veth0 up
      sudo ip link set veth1 up

   Then use ``"veth0"`` for one station and ``"veth1"`` for the other.

----

PythonCV2XLinkLayer
-------------------

The ``PythonCV2XLinkLayer`` enables real C-V2X (Cellular V2X) communication using 
Qualcomm's PC5 sidelink interface. This is what you'd use in production vehicles.

.. warning::

   This requires the ``telux_cv2x`` SDK and compatible hardware (e.g., Qualcomm SDX55/SDX65).

Quick Start
~~~~~~~~~~~

.. code-block:: python

    from flexstack.linklayer.cv2x_link_layer import PythonCV2XLinkLayer

    def on_packet_received(packet: bytes):
        print(f"📥 Received C-V2X packet: {packet.hex()}")

    # Create C-V2X link layer
    link_layer = PythonCV2XLinkLayer(receive_callback=on_packet_received)

    # Send a packet
    link_layer.send(b"Hello C-V2X!")

Complete Example
~~~~~~~~~~~~~~~~

.. code-block:: python

    import time
    from flexstack.linklayer.cv2x_link_layer import PythonCV2XLinkLayer

    def on_packet_received(packet: bytes):
        print(f"📥 Received C-V2X packet: {packet.hex()}")

    if __name__ == "__main__":
        link_layer = PythonCV2XLinkLayer(receive_callback=on_packet_received)

        print("📡 C-V2X Link Layer active")
        print("Press Ctrl+C to exit\n")

        try:
            while True:
                data = bytes([i % 256 for i in range(100)])
                link_layer.send(data)
                print(f"📤 Sent C-V2X packet: {data[:10].hex()}...")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
        
        # Clean up C-V2X resources
        del link_layer.link_layer
        time.sleep(2)  # Allow time for cleanup
        print("✅ Shutdown complete")

----

.. _cv2xlinklayer:

CV2XLinkLayer C++ Library
-------------------------

Under the hood, ``PythonCV2XLinkLayer`` uses a C++ library called ``cv2xlinklayer`` that interfaces 
with the Qualcomm telematics SDK. This section is for advanced users who need to build or modify 
this library.

.. mermaid::

    flowchart LR
        subgraph Python
            A[PythonCV2XLinkLayer]
        end
        subgraph "C++ (pybind11)"
            B[cv2xlinklayer.so]
        end
        subgraph "Qualcomm SDK"
            C[telux_cv2x]
        end
        subgraph Hardware
            D[C-V2X Modem]
        end
        
        A <--> B
        B <--> C
        C <--> D

Library Components
~~~~~~~~~~~~~~~~~~

The library consists of three main files:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - File
     - Description
   * - ``cv2x_link_layer.cpp``
     - Main implementation: Tx/Rx flow setup, callbacks, send/receive methods
   * - ``cv2x_link_layer.hpp``
     - Header file declaring the ``CV2XLinkLayer`` class
   * - ``CMakeLists.txt``
     - Build configuration for CMake

Building from Source
~~~~~~~~~~~~~~~~~~~~

**Prerequisites:**

- CMake ≥ 3.12
- C++11 compiler
- ``pybind11``
- ``telux_cv2x`` SDK (from Qualcomm)

**Build steps:**

.. code-block:: bash

    # Clone and enter the directory
    cd cv2xlinklayer

    # Create build directory
    mkdir build && cd build

    # Configure and build
    cmake ..
    make

    # The output is: lib/cv2xlinklayer.so

Direct C++ API Usage
~~~~~~~~~~~~~~~~~~~~

If you need to use the library directly from Python without the FlexStack wrapper:

.. code-block:: python

    import cv2xlinklayer

    # Create instance
    link_layer = cv2xlinklayer.CV2XLinkLayer()

    # Send data
    link_layer.send(b"Hello, C-V2X!")

    # Receive data (blocking)
    received = link_layer.receive()
    print(f"Received: {received}")

----

Integration with FlexStack
--------------------------

In a complete FlexStack application, the Link Layer connects to the GeoNetworking router:

.. code-block:: python

    from flexstack.linklayer.raw_link_layer import RawLinkLayer
    from flexstack.geonet.router import Router as GNRouter

    # Create GeoNetworking router
    gn_router = GNRouter(mib=mib, sign_service=None)

    # Create Link Layer with GN router as callback
    link_layer = RawLinkLayer(
        iface="lo",
        mac_address=MAC_ADDRESS,
        receive_callback=gn_router.gn_data_indicate  # 👈 Connect to GN
    )

    # Connect GN router to Link Layer for sending
    gn_router.link_layer = link_layer  # 👈 Bidirectional connection

This creates a bidirectional connection:

- **Incoming packets**: Link Layer → ``gn_router.gn_data_indicate()``
- **Outgoing packets**: GN Router → ``link_layer.send()``

See the :doc:`/getting_started` tutorial for a complete example.
