Getting Started
===============

Welcome to FlexStack®! This tutorial will walk you through building your first V2X application — a vehicle that broadcasts 
its position to nearby vehicles using **Cooperative Awareness Messages (CAMs)**.

.. note::
   
   By the end of this tutorial, you'll have a working V2X station that can send and receive CAM messages, 
   the foundation of vehicle-to-vehicle communication.

What You'll Build
-----------------

In this tutorial, you'll create a simple V2X application that:

- 📡 **Broadcasts** your vehicle's position, speed, and heading to nearby vehicles
- 📥 **Receives** CAM messages from other vehicles
- 🗺️ **Stores** received data in a Local Dynamic Map (LDM)

This is the "Hello World" of V2X — the Cooperative Awareness use case that enables vehicles to know about each other's presence on the road.

Prerequisites
-------------

Before starting, make sure you have:

- Python 3.8 or higher
- Linux operating system (required for raw socket access)
- ``sudo`` privileges (needed for low-level network access)

Installation
------------

Install FlexStack® using pip:

.. code-block:: bash

    pip install v2xflexstack

That's it! All dependencies are installed automatically.

Understanding the Protocol Stack
--------------------------------

Before diving into code, let's understand what we're building. The ETSI C-ITS protocol stack looks like this:

.. mermaid::

   graph TB
       subgraph "Application Layer"
           APP[Your Application]
       end
       subgraph "Facilities Layer"
           LDM[Local Dynamic Map]
           CAM[CA Basic Service]
       end
       subgraph "Transport & Network"
           BTP[BTP Router]
           GN[GeoNetworking Router]
       end
       subgraph "Access Layer"
           LL[Link Layer]
       end
       
       APP --> LDM
       LDM --> CAM
       CAM <--> BTP
       CAM --> LDM
       BTP <--> GN
       GN <--> LL
       
       style APP fill:#e1f5fe
       style CAM fill:#fff3e0
       style LDM fill:#fff3e0
       style BTP fill:#f3e5f5
       style GN fill:#f3e5f5
       style LL fill:#e8f5e9


Each layer has a specific role:

- **Link Layer**: Handles raw network communication (ITS-G5 or C-V2X)
- **GeoNetworking**: Routes messages based on geographic position
- **BTP**: Multiplexes messages to the correct service
- **Facilities Layer**: Provides high-level services like CAM broadcasting
- **Local Dynamic Map**: Stores and manages received V2X data

We'll build this stack from the bottom up.

Step-by-Step Tutorial
---------------------

Let's build our CAM broadcaster step by step. Create a new file called ``cam_example.py`` and follow along.

Step 1: Basic Setup
~~~~~~~~~~~~~~~~~~~

First, let's set up logging and define some constants for our vehicle:

.. code-block:: python

    import logging
    import random
    import time

    # Enable logging to see what's happening
    logging.basicConfig(level=logging.INFO)

    def generate_random_mac_address() -> bytes:
        """Generate a valid random MAC address."""
        octets = [random.randint(0x00, 0xFF) for _ in range(6)]
        # Set locally administered and unicast bits
        octets[0] = (octets[0] & 0b11111110) | 0b00000010
        return bytes(octets)

    # Vehicle configuration
    POSITION_COORDINATES = [41.386931, 2.112104]  # Barcelona, Spain
    MAC_ADDRESS = generate_random_mac_address()
    STATION_ID = random.randint(1, 2147483647)


Step 2: Location Service
~~~~~~~~~~~~~~~~~~~~~~~~

V2X is all about location. The protocol stack needs to know where your vehicle is. FlexStack® provides 
different location services — we'll use a static one for this tutorial:

.. code-block:: python

    from flexstack.utils.static_location_service import ThreadStaticLocationService

    # Create a location service that reports our fixed position every second
    location_service = ThreadStaticLocationService(
        period=1000,  # Update every 1000ms
        latitude=POSITION_COORDINATES[0],
        longitude=POSITION_COORDINATES[1]
    )

.. tip::

   In a real application, you'd use ``GPSDLocationService`` to get live GPS data from a GPSD daemon.

Step 3: GeoNetworking Router
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

GeoNetworking is the heart of V2X — it routes messages based on geographic areas. Let's set it up:

.. code-block:: python

    from flexstack.geonet.router import Router as GNRouter
    from flexstack.geonet.mib import MIB
    from flexstack.geonet.gn_address import GNAddress, M, ST, MID

    # Configure the GeoNetworking Management Information Base (MIB)
    mib = MIB(
        itsGnLocalGnAddr=GNAddress(
            m=M.GN_MULTICAST,      # Multicast addressing mode
            st=ST.CYCLIST,         # Station type (see ETSI TS 102 894-2)
            mid=MID(MAC_ADDRESS),  # Mobile ID based on MAC address
        ),
    )

    # Create the GeoNetworking router
    gn_router = GNRouter(mib=mib, sign_service=None)

    # Connect location updates to the router
    location_service.add_callback(gn_router.refresh_ego_position_vector)

Step 4: BTP Router
~~~~~~~~~~~~~~~~~~

The Basic Transport Protocol (BTP) multiplexes incoming messages to the right service based on port numbers:

.. code-block:: python

    from flexstack.btp.router import Router as BTPRouter

    # Create BTP router and connect it to GeoNetworking
    btp_router = BTPRouter(gn_router)
    gn_router.register_indication_callback(btp_router.btp_data_indication)


Step 5: Local Dynamic Map (LDM)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Local Dynamic Map is like a database for V2X — it stores all received messages and lets you query them. 
This is where you'll find data about nearby vehicles:

.. code-block:: python

    from flexstack.facilities.local_dynamic_map.factory import LDMFactory
    from flexstack.facilities.local_dynamic_map.ldm_classes import (
        AccessPermission,
        Circle,
        Filter,
        FilterStatement,
        ComparisonOperators,
        GeometricArea,
        Location,
        OrderTupleValue,
        OrderingDirection,
        SubscribeDataobjectsReq,
        SubscribeDataObjectsResp,
        SubscribeDataobjectsResult,
        RegisterDataConsumerReq,
        RegisterDataConsumerResp,
        RequestDataObjectsResp,
        TimestampIts,
    )
    from flexstack.facilities.local_dynamic_map.ldm_constants import CAM

    # Define our location for the LDM
    ldm_location = Location.initializer(
        latitude=int(POSITION_COORDINATES[0] * 10**7),
        longitude=int(POSITION_COORDINATES[1] * 10**7),
    )

    # Define area of interest: 5km radius around our position
    ldm_area = GeometricArea(
        circle=Circle(radius=5000),
        rectangle=None,
        ellipse=None,
    )

    # Create the LDM
    ldm_factory = LDMFactory()
    ldm = ldm_factory.create_ldm(
        ldm_location,
        ldm_maintenance_type="Reactive",
        ldm_service_type="Reactive",
        ldm_database_type="Dictionary",
    )

    # Keep LDM updated with our position
    location_service.add_callback(ldm_location.location_service_callback)

Now let's register as a data consumer and subscribe to CAM messages:

.. code-block:: python

    # Register as a consumer of CAM data
    register_response: RegisterDataConsumerResp = ldm.if_ldm_4.register_data_consumer(
        RegisterDataConsumerReq(
            application_id=CAM,
            access_permisions=(AccessPermission.CAM,),
            area_of_interest=ldm_area,
        )
    )

    if register_response.result == 2:
        print("Failed to register with LDM!")
        exit(1)

    # Define what happens when we receive a CAM
    def on_cam_received(data: RequestDataObjectsResp) -> None:
        station_id = data.data_objects[0]["dataObject"]["header"]["stationId"]
        print(f"🚗 Received CAM from station: {station_id}")

    # Subscribe to CAM messages (excluding our own)
    subscribe_response: SubscribeDataObjectsResp = ldm.if_ldm_4.subscribe_data_consumer(
        SubscribeDataobjectsReq(
            application_id=CAM,
            data_object_type=(CAM,),
            priority=1,
            filter=Filter(
                filter_statement_1=FilterStatement(
                    "header.stationId",
                    ComparisonOperators.NOT_EQUAL,
                    STATION_ID  # Don't notify us about our own CAMs
                )
            ),
            notify_time=TimestampIts(0),
            multiplicity=1,
            order=(
                OrderTupleValue(
                    attribute="cam.generationDeltaTime",
                    ordering_direction=OrderingDirection.ASCENDING
                ),
            ),
        ),
        on_cam_received,
    )

    if subscribe_response.result != SubscribeDataobjectsResult.SUCCESSFUL:
        print("Failed to subscribe to CAM messages!")
        exit(1)

Step 6: CA Basic Service
~~~~~~~~~~~~~~~~~~~~~~~~

Now for the main attraction — the Cooperative Awareness Basic Service. This is what actually sends and receives CAM messages:

.. code-block:: python

    from flexstack.facilities.ca_basic_service.ca_basic_service import (
        CooperativeAwarenessBasicService,
    )
    from flexstack.facilities.ca_basic_service.cam_transmission_management import (
        VehicleData,
    )

    # Configure our vehicle's properties
    vehicle_data = VehicleData(
        station_id=STATION_ID,
        station_type=5,  # Passenger car (see ETSI TS 102 894-2)
        drive_direction="forward",
        vehicle_length={
            "vehicleLengthValue": 1023,  # Unknown length
            "vehicleLengthConfidenceIndication": "unavailable",
        },
        vehicle_width=62,  # ~1.5m width
    )

    # Create the CA Basic Service
    ca_basic_service = CooperativeAwarenessBasicService(
        btp_router=btp_router,
        vehicle_data=vehicle_data,
        ldm=ldm,
    )

    # Connect location updates to CAM transmission
    location_service.add_callback(
        ca_basic_service.cam_transmission_management.location_service_callback
    )

Step 7: Link Layer
~~~~~~~~~~~~~~~~~~

Finally, we need to connect everything to the network. The Link Layer handles the actual packet transmission:

.. code-block:: python

    from flexstack.linklayer.raw_link_layer import RawLinkLayer

    # Freeze BTP callbacks before starting (prevents race conditions)
    btp_router.freeze_callbacks()

    # Create the link layer on the loopback interface
    link_layer = RawLinkLayer(
        "lo",  # Network interface (use "lo" for testing)
        MAC_ADDRESS,
        receive_callback=gn_router.gn_data_indicate
    )

    # Connect GeoNetworking to the link layer
    gn_router.link_layer = link_layer

.. warning::

   For testing, we use the loopback interface ``"lo"``. In production, you'd use your actual network 
   interface (e.g., ``"eth0"``, ``"wlan0"``) or specialized V2X hardware with ``PythonCV2XLinkLayer``.

Step 8: Run the Application
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add the main loop to keep everything running:

.. code-block:: python

    print("✅ CA Basic Service is running!")
    print("📡 Broadcasting CAMs and listening for nearby vehicles...")
    print("Press Ctrl+C to exit.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")

    # Clean up
    location_service.stop_event.set()
    location_service.location_service_thread.join()
    link_layer.sock.close()

Complete Example
----------------

Here's the complete script. Save it as ``cam_example.py`` and run with ``sudo``:

.. code-block:: bash

    sudo python cam_example.py

.. code-block:: python
    :linenos:

    #!/usr/bin/env python3
    """
    FlexStack® CAM Example
    
    A simple V2X application that broadcasts Cooperative Awareness Messages (CAMs)
    and listens for CAMs from nearby vehicles.
    
    Run with: sudo python cam_example.py
    """

    import logging
    import random
    import time

    # FlexStack imports
    from flexstack.linklayer.raw_link_layer import RawLinkLayer
    from flexstack.geonet.router import Router as GNRouter
    from flexstack.geonet.mib import MIB
    from flexstack.geonet.gn_address import GNAddress, M, ST, MID
    from flexstack.btp.router import Router as BTPRouter
    from flexstack.utils.static_location_service import ThreadStaticLocationService
    from flexstack.facilities.local_dynamic_map.factory import LDMFactory
    from flexstack.facilities.local_dynamic_map.ldm_constants import CAM
    from flexstack.facilities.local_dynamic_map.ldm_classes import (
        AccessPermission,
        Circle,
        ComparisonOperators,
        Filter,
        FilterStatement,
        GeometricArea,
        Location,
        OrderTupleValue,
        OrderingDirection,
        RegisterDataConsumerReq,
        RegisterDataConsumerResp,
        RequestDataObjectsResp,
        SubscribeDataobjectsReq,
        SubscribeDataObjectsResp,
        SubscribeDataobjectsResult,
        TimestampIts,
    )
    from flexstack.facilities.ca_basic_service.ca_basic_service import (
        CooperativeAwarenessBasicService,
    )
    from flexstack.facilities.ca_basic_service.cam_transmission_management import (
        VehicleData,
    )

    # Enable logging
    logging.basicConfig(level=logging.INFO)


    def generate_random_mac_address() -> bytes:
        """Generate a valid random MAC address."""
        octets = [random.randint(0x00, 0xFF) for _ in range(6)]
        octets[0] = (octets[0] & 0b11111110) | 0b00000010
        return bytes(octets)


    # Configuration
    POSITION_COORDINATES = [41.386931, 2.112104]  # Barcelona, Spain
    MAC_ADDRESS = generate_random_mac_address()
    STATION_ID = random.randint(1, 2147483647)


    def main():
        # ========== Step 2: Location Service ==========
        location_service = ThreadStaticLocationService(
            period=1000,
            latitude=POSITION_COORDINATES[0],
            longitude=POSITION_COORDINATES[1],
        )

        # ========== Step 3: GeoNetworking ==========
        mib = MIB(
            itsGnLocalGnAddr=GNAddress(
                m=M.GN_MULTICAST,
                st=ST.CYCLIST,
                mid=MID(MAC_ADDRESS),
            ),
        )
        gn_router = GNRouter(mib=mib, sign_service=None)
        location_service.add_callback(gn_router.refresh_ego_position_vector)

        # ========== Step 4: BTP ==========
        btp_router = BTPRouter(gn_router)
        gn_router.register_indication_callback(btp_router.btp_data_indication)

        # ========== Step 5: Local Dynamic Map ==========
        ldm_location = Location.initializer(
            latitude=int(POSITION_COORDINATES[0] * 10**7),
            longitude=int(POSITION_COORDINATES[1] * 10**7),
        )
        ldm_area = GeometricArea(
            circle=Circle(radius=5000),
            rectangle=None,
            ellipse=None,
        )
        ldm_factory = LDMFactory()
        ldm = ldm_factory.create_ldm(
            ldm_location,
            ldm_maintenance_type="Reactive",
            ldm_service_type="Reactive",
            ldm_database_type="Dictionary",
        )
        location_service.add_callback(ldm_location.location_service_callback)

        # Register with LDM
        register_response: RegisterDataConsumerResp = ldm.if_ldm_4.register_data_consumer(
            RegisterDataConsumerReq(
                application_id=CAM,
                access_permisions=(AccessPermission.CAM,),
                area_of_interest=ldm_area,
            )
        )
        if register_response.result == 2:
            print("Failed to register with LDM!")
            exit(1)

        # CAM received callback
        def on_cam_received(data: RequestDataObjectsResp) -> None:
            station_id = data.data_objects[0]["dataObject"]["header"]["stationId"]
            print(f"🚗 Received CAM from station: {station_id}")

        # Subscribe to CAMs
        subscribe_response: SubscribeDataObjectsResp = ldm.if_ldm_4.subscribe_data_consumer(
            SubscribeDataobjectsReq(
                application_id=CAM,
                data_object_type=(CAM,),
                priority=1,
                filter=Filter(
                    filter_statement_1=FilterStatement(
                        "header.stationId",
                        ComparisonOperators.NOT_EQUAL,
                        STATION_ID,
                    )
                ),
                notify_time=TimestampIts(0),
                multiplicity=1,
                order=(
                    OrderTupleValue(
                        attribute="cam.generationDeltaTime",
                        ordering_direction=OrderingDirection.ASCENDING,
                    ),
                ),
            ),
            on_cam_received,
        )
        if subscribe_response.result != SubscribeDataobjectsResult.SUCCESSFUL:
            print("Failed to subscribe to CAM messages!")
            exit(1)

        # ========== Step 6: CA Basic Service ==========
        vehicle_data = VehicleData(
            station_id=STATION_ID,
            station_type=5,
            drive_direction="forward",
            vehicle_length={
                "vehicleLengthValue": 1023,
                "vehicleLengthConfidenceIndication": "unavailable",
            },
            vehicle_width=62,
        )
        ca_basic_service = CooperativeAwarenessBasicService(
            btp_router=btp_router,
            vehicle_data=vehicle_data,
            ldm=ldm,
        )
        location_service.add_callback(
            ca_basic_service.cam_transmission_management.location_service_callback
        )

        # ========== Step 7: Link Layer ==========
        btp_router.freeze_callbacks()
        link_layer = RawLinkLayer(
            "lo",
            MAC_ADDRESS,
            receive_callback=gn_router.gn_data_indicate,
        )
        gn_router.link_layer = link_layer

        # ========== Step 8: Run ==========
        print("✅ CA Basic Service is running!")
        print("📡 Broadcasting CAMs and listening for nearby vehicles...")
        print("Press Ctrl+C to exit.\n")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")

        location_service.stop_event.set()
        location_service.location_service_thread.join()
        link_layer.sock.close()


    if __name__ == "__main__":
        main()

Need Help?
----------

- Check the :doc:`overview` for a high-level introduction
- Browse the module documentation in the sidebar
- Visit our `GitHub repository <https://github.com/Fundacio-i2CAT/FlexStack>`_ for issues and discussions
