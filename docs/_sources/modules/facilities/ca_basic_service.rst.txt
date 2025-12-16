.. _ca_basic_service:

Cooperative Awareness (CA) Basic Service
========================================

The CA Basic Service is the heart of vehicle awareness in V2X — it broadcasts **Cooperative Awareness 
Messages (CAMs)** that tell nearby vehicles "I'm here, this is my position, speed, and heading."

.. note::

   The CA Basic Service implements ETSI TS 103 900 V2.1.1 (2023-11). CAMs are the most fundamental 
   V2X message type, enabling vehicles to be aware of each other's presence.

What CAMs Contain
-----------------

Every CAM broadcasts essential information about your vehicle:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Field
     - Description
   * - **Position**
     - GPS coordinates (latitude, longitude, altitude)
   * - **Speed**
     - Current velocity in m/s
   * - **Heading**
     - Direction of travel (degrees from north)
   * - **Station ID**
     - Unique identifier for this vehicle
   * - **Station Type**
     - Vehicle category (car, truck, motorcycle, etc.)
   * - **Vehicle Size**
     - Length and width dimensions

Architecture
------------

The CA Basic Service sits in the **Facilities Layer** and connects to BTP for transport:

.. mermaid::

   erdiagram TB
       subgraph "Facilities Layer"
           subgraph CA["CA Basic Service"]
              TM[Transmission<br/>Management]
              RM[Reception<br/>Management]
           end
           LDM[(Local Dynamic Map)]
       end
       
       subgraph "Location"
           LOC[Location Service]
       end
       
       subgraph "Transport"
           BTP[BTP Router<br/>Port 2001]
       end
       
       LOC -->|"Position Updates"| TM
       TM -->|"Generate CAM"| CA
       CA <-->|"Send/Receive"| BTP
       CA -->|"Store Received"| LDM
       RM -->|"Process CAM"| CA
       
       style CA fill:#fff3e0,stroke:#f57c00
       style LDM fill:#e8f5e9

**How it works:**

1. **Sending**: Location Service updates trigger CAM generation → sent via BTP port 2001
2. **Receiving**: Incoming CAMs on port 2001 → processed and stored in LDM

----

Getting Started
---------------

Step 1: Configure Vehicle Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, describe your vehicle using ``VehicleData``:

.. code-block:: python

   from flexstack.facilities.ca_basic_service.cam_transmission_management import VehicleData

   STATION_ID = 12345  # Unique ID for your station
   vehicle_data = VehicleData(
       station_id=STATION_ID,          
       station_type=5,                # 5 = Passenger car
       drive_direction="forward",     # "forward", "backward", or "unavailable"
       vehicle_length={
           "vehicleLengthValue": 42,  # Length in 10cm units (42 = 4.2m)
           "vehicleLengthConfidenceIndication": "unavailable",
       },
       vehicle_width=18,              # Width in 10cm units (18 = 1.8m)
   )

**VehicleData Parameters:**

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Parameter
     - Type
     - Description
   * - ``station_id``
     - ``int``
     - Unique station identifier (1 to 2^31-1)
   * - ``station_type``
     - ``int``
     - Vehicle type code (see table below)
   * - ``drive_direction``
     - ``str``
     - ``"forward"``, ``"backward"``, or ``"unavailable"``
   * - ``vehicle_length``
     - ``dict``
     - Length value (0.1m units) and confidence
   * - ``vehicle_width``
     - ``int``
     - Width in 0.1m units (1-62, where 62 = unavailable)

**Station Types:**

.. list-table::
   :header-rows: 1
   :widths: 15 25 60

   * - Value
     - Type
     - Description
   * - 0
     - Unknown
     - Unknown station type
   * - 1
     - Pedestrian
     - Person on foot
   * - 2
     - Cyclist
     - Bicycle rider
   * - 3
     - Moped
     - Moped/scooter
   * - 4
     - Motorcycle
     - Motorcycle
   * - 5
     - Passenger Car
     - Standard automobile
   * - 6
     - Bus
     - Bus/coach
   * - 7
     - Light Truck
     - Light commercial vehicle
   * - 8
     - Heavy Truck
     - Heavy goods vehicle
   * - 15
     - RSU
     - Road Side Unit

Step 2: Set Up Prerequisites
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The CA Basic Service requires:

- A **BTP Router** (for sending/receiving)
- A **Local Dynamic Map** (for storing received CAMs)
- A **Location Service** (for position updates)

.. code-block:: python

   from flexstack.btp.router import Router as BTPRouter
   from flexstack.geonet.router import Router as GNRouter
   from flexstack.geonet.mib import MIB
   from flexstack.geonet.gn_address import GNAddress, M, ST, MID
   from flexstack.facilities.local_dynamic_map.factory import LDMFactory
   from flexstack.facilities.local_dynamic_map.ldm_classes import Location, GeometricArea, Circle
   from flexstack.utils.static_location_service import ThreadStaticLocationService

   # Location Service
   location_service = ThreadStaticLocationService(
       period=1000,
       latitude=41.386931,
       longitude=2.112104,
   )

   # GeoNetworking + BTP
   MAC_ADDRESS = b'\x00\x11\x22\x33\x44\x55'
   mib = MIB(itsGnLocalGnAddr=GNAddress(m=M.GN_MULTICAST, st=ST.PASSENGER_CAR, mid=MID(MAC_ADDRESS)))
   gn_router = GNRouter(mib=mib, sign_service=None)
   btp_router = BTPRouter(gn_router)
   gn_router.register_indication_callback(btp_router.btp_data_indication)
   location_service.add_callback(gn_router.refresh_ego_position_vector)

   # Local Dynamic Map
   ldm_location = Location.initializer(latitude=413869310, longitude=21121040)
   ldm_factory = LDMFactory()
   ldm = ldm_factory.create_ldm(
       ldm_location,
       ldm_maintenance_type="Reactive",
       ldm_service_type="Reactive",
       ldm_database_type="Dictionary",
   )
   location_service.add_callback(ldm_location.location_service_callback)

Step 3: Create CA Basic Service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now create the service and connect it to the location service:

.. code-block:: python

   from flexstack.facilities.ca_basic_service.ca_basic_service import (
       CooperativeAwarenessBasicService,
   )

   # Create the CA Basic Service
   ca_basic_service = CooperativeAwarenessBasicService(
       btp_router=btp_router,
       vehicle_data=vehicle_data,
       ldm=ldm,
   )

   # Connect location updates to trigger CAM transmission
   location_service.add_callback(
       ca_basic_service.cam_transmission_management.location_service_callback
   )

That's it! The service will now:

- ✅ **Automatically send CAMs** whenever the location service provides an update
- ✅ **Automatically receive CAMs** and store them in the LDM

----

Receiving CAMs
--------------

To be notified when CAMs arrive, subscribe to the LDM:

.. code-block:: python

   from flexstack.facilities.local_dynamic_map.ldm_constants import CAM
   from flexstack.facilities.local_dynamic_map.ldm_classes import (
       AccessPermission,
       RegisterDataConsumerReq,
       RegisterDataConsumerResp,
       SubscribeDataobjectsReq,
       SubscribeDataObjectsResp,
       RequestDataObjectsResp,
       Filter,
       FilterStatement,
       ComparisonOperators,
       TimestampIts,
       OrderTupleValue,
       OrderingDirection,
       SubscribeDataobjectsResult,
   )

   ldm_area = GeometricArea(circle=Circle(radius=5000), rectangle=None, ellipse=None)

   # Register as a CAM consumer
   ldm.if_ldm_4.register_data_consumer(
       RegisterDataConsumerReq(
           application_id=CAM,
           access_permisions=(AccessPermission.CAM,),
           area_of_interest=ldm_area,
       )
   )

   # Callback when CAMs are received
   def on_cam_received(data: RequestDataObjectsResp) -> None:
       cam = data.data_objects[0]["dataObject"]
       station_id = cam["header"]["stationId"]
       print(f"🚗 Received CAM from station {station_id}")

   # Subscribe to CAM updates (filtering out our own)
   ldm.if_ldm_4.subscribe_data_consumer(
       SubscribeDataobjectsReq(
           application_id=CAM,
           data_object_type=(CAM,),
           priority=1,
           filter=Filter(
               filter_statement_1=FilterStatement(
                   "header.stationId",
                   ComparisonOperators.NOT_EQUAL,
                   STATION_ID,  # Don't notify about our own CAMs
               )
           ),
           notify_time=TimestampIts(0),
           multiplicity=1,
           order=(OrderTupleValue(
               attribute="cam.generationDeltaTime",
               ordering_direction=OrderingDirection.ASCENDING,
           ),),
       ),
       on_cam_received,
   )

----

CAM Message Structure
---------------------

A CAM contains three main containers:

.. mermaid::

   flowchart LR
       subgraph CAM[CAM Message]
           H[ITS PDU Header]
           BC[Basic Container]
           HFC[High Frequency Container]
           LFC[Low Frequency Container]
       end
       
       H --> BC --> HFC --> LFC

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Container
     - Contents
   * - **ITS PDU Header**
     - Protocol version, message ID, station ID
   * - **Basic Container**
     - Station type, reference position
   * - **High Frequency Container**
     - Heading, speed, drive direction, vehicle length, width, acceleration
   * - **Low Frequency Container**
     - Vehicle role, exterior lights, path history

----

Complete Example
----------------

Here's a complete script that sends and receives CAMs:

.. code-block:: python
   :linenos:

   #!/usr/bin/env python3
   """
   CA Basic Service Example
   
   Broadcasts CAMs and listens for nearby vehicles.
   Run with: sudo python cam_example.py
   """

   import logging
   import random
   import time

   from flexstack.linklayer.raw_link_layer import RawLinkLayer
   from flexstack.geonet.router import Router as GNRouter
   from flexstack.geonet.mib import MIB
   from flexstack.geonet.gn_address import GNAddress, M, ST, MID
   from flexstack.btp.router import Router as BTPRouter
   from flexstack.utils.static_location_service import ThreadStaticLocationService
   from flexstack.facilities.local_dynamic_map.factory import LDMFactory
   from flexstack.facilities.local_dynamic_map.ldm_constants import CAM
   from flexstack.facilities.local_dynamic_map.ldm_classes import (
       AccessPermission, Circle, ComparisonOperators, Filter, FilterStatement,
       GeometricArea, Location, OrderTupleValue, OrderingDirection,
       RegisterDataConsumerReq, RegisterDataConsumerResp, RequestDataObjectsResp,
       SubscribeDataobjectsReq, SubscribeDataObjectsResp, SubscribeDataobjectsResult,
       TimestampIts,
   )
   from flexstack.facilities.ca_basic_service.ca_basic_service import (
       CooperativeAwarenessBasicService,
   )
   from flexstack.facilities.ca_basic_service.cam_transmission_management import VehicleData

   logging.basicConfig(level=logging.INFO)

   # Configuration
   POSITION = [41.386931, 2.112104]  # Barcelona
   MAC_ADDRESS = bytes([random.randint(0, 255) for _ in range(6)])
   STATION_ID = random.randint(1, 2147483647)


   def on_cam_received(data: RequestDataObjectsResp) -> None:
       """Called when a CAM is received from another vehicle."""
       station_id = data.data_objects[0]["dataObject"]["header"]["stationId"]
       print(f"🚗 Received CAM from station: {station_id}")


   def main():
       # Location Service
       location_service = ThreadStaticLocationService(
           period=1000, latitude=POSITION[0], longitude=POSITION[1]
       )

       # GeoNetworking
       mib = MIB(itsGnLocalGnAddr=GNAddress(m=M.GN_MULTICAST, st=ST.CYCLIST, mid=MID(MAC_ADDRESS)))
       gn_router = GNRouter(mib=mib, sign_service=None)
       location_service.add_callback(gn_router.refresh_ego_position_vector)

       # BTP
       btp_router = BTPRouter(gn_router)
       gn_router.register_indication_callback(btp_router.btp_data_indication)

       # Local Dynamic Map
       ldm_location = Location.initializer(
           latitude=int(POSITION[0] * 10**7),
           longitude=int(POSITION[1] * 10**7),
       )
       ldm_area = GeometricArea(circle=Circle(radius=5000), rectangle=None, ellipse=None)
       ldm = LDMFactory().create_ldm(
           ldm_location, ldm_maintenance_type="Reactive",
           ldm_service_type="Reactive", ldm_database_type="Dictionary",
       )
       location_service.add_callback(ldm_location.location_service_callback)

       # Register with LDM
       ldm.if_ldm_4.register_data_consumer(RegisterDataConsumerReq(
           application_id=CAM, access_permisions=(AccessPermission.CAM,), area_of_interest=ldm_area,
       ))

       # Subscribe to CAMs
       ldm.if_ldm_4.subscribe_data_consumer(
           SubscribeDataobjectsReq(
               application_id=CAM, data_object_type=(CAM,), priority=1,
               filter=Filter(filter_statement_1=FilterStatement(
                   "header.stationId", ComparisonOperators.NOT_EQUAL, STATION_ID,
               )),
               notify_time=TimestampIts(0), multiplicity=1,
               order=(OrderTupleValue(
                   attribute="cam.generationDeltaTime",
                   ordering_direction=OrderingDirection.ASCENDING,
               ),),
           ),
           on_cam_received,
       )

       # CA Basic Service
       vehicle_data = VehicleData(
           station_id=STATION_ID, station_type=5, drive_direction="forward",
           vehicle_length={"vehicleLengthValue": 1023, "vehicleLengthConfidenceIndication": "unavailable"},
           vehicle_width=62,
       )
       ca_service = CooperativeAwarenessBasicService(
           btp_router=btp_router, vehicle_data=vehicle_data, ldm=ldm,
       )
       location_service.add_callback(ca_service.cam_transmission_management.location_service_callback)

       # Link Layer
       btp_router.freeze_callbacks()
       link_layer = RawLinkLayer("lo", MAC_ADDRESS, receive_callback=gn_router.gn_data_indicate)
       gn_router.link_layer = link_layer

       print("✅ CA Basic Service running!")
       print("📡 Broadcasting CAMs...")
       print("Press Ctrl+C to exit\n")

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

----

CAM Generation Rules
--------------------

According to ETSI standards, CAMs are generated when:

1. **Time-based**: At least every 1 second (T_GenCamMax)
2. **Position change**: When position changes by more than 4 meters
3. **Speed change**: When speed changes by more than 0.5 m/s
4. **Heading change**: When heading changes by more than 4 degrees

The minimum interval between CAMs is 100ms (T_GenCamMin).

----

See Also
--------

- :doc:`/getting_started` — Complete tutorial with CA Basic Service
- :doc:`local_dynamic_map` — Where received CAMs are stored
- :doc:`den_service` — Decentralized Environmental Notifications (hazard warnings)
- :doc:`/modules/btp` — Transport layer (BTP port 2001)