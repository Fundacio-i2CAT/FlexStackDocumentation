.. _local_dynamic_map:

Local Dynamic Map
=================

The **Local Dynamic Map (LDM)** is FlexStack's intelligent data storage system. It collects, 
organizes, and serves V2X messages — giving your applications a real-time view of the 
surrounding traffic environment.

.. note::

   The LDM implements ETSI EN 302 895 V1.1.1. Think of it as a database that automatically 
   manages message validity based on time and location.

What the LDM Does
-----------------

.. mermaid::

   flowchart LR
       subgraph "Data Providers"
           CAM[CA Basic Service<br/>CAMs]
           DEN[DEN Service<br/>DENMs]
           VRU[VRU Service<br/>VAMs]
       end
       
       subgraph "LDM"
           DB[(LDM Database)]
           MT[Maintenance<br/>Auto-cleanup]
       end
       
       subgraph "Data Consumers"
           APP1[Collision Warning App]
           APP2[Traffic Analysis App]
           APP3[Navigation App]
       end
       
       CAM -->|"Publish"| DB
       DEN -->|"Publish"| DB
       VRU -->|"Publish"| DB
       DB -->|"Query"| APP1
       DB -->|"Subscribe"| APP2
       DB -->|"Query"| APP3
       MT -.->|"Remove expired"| DB
       
       style DB fill:#e3f2fd,stroke:#1565c0

**Key Features:**

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Feature
     - Description
   * - 📥 **Data Collection**
     - Receives messages from CAM, DENM, VAM services
   * - 🗄️ **Organized Storage**
     - Stores messages with timestamps and locations
   * - 🔍 **Query Interface**
     - Find specific messages by station ID, type, or location
   * - 📡 **Subscriptions**
     - Get notified when new messages arrive
   * - 🧹 **Auto Maintenance**
     - Automatically removes expired or out-of-area messages

----

Architecture
------------

The LDM consists of two main components:

.. mermaid::

   flowchart TB
       subgraph "LDM Service"
           REG[Registration<br/>Providers & Consumers]
           PUB[Publish Interface<br/>IF-LDM-3]
           QRY[Query Interface<br/>IF-LDM-4]
           SUB[Subscribe Interface<br/>IF-LDM-4]
       end
       
       subgraph "LDM Maintenance"
           TIME[Time Validity<br/>Check]
           AREA[Area of Maintenance<br/>Check]
           CLEAN[Cleanup<br/>Service]
       end
       
       subgraph "Storage"
           DB[(LDM Database)]
       end
       
       subgraph "Location"
           LOC[Location Service]
       end
       
       REG --> DB
       PUB --> DB
       QRY --> DB
       SUB --> DB
       TIME --> CLEAN
       AREA --> CLEAN
       CLEAN --> DB
       LOC --> AREA
       
       style DB fill:#fff3e0,stroke:#e65100

**Components:**

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Component
     - Description
   * - **LDM Service**
     - Handles registration, publishing, queries, and subscriptions
   * - **LDM Maintenance**
     - Removes expired messages and those outside the area
   * - **IF-LDM-3**
     - Interface for Data Providers (publish data)
   * - **IF-LDM-4**
     - Interface for Data Consumers (query/subscribe)

----

Supported Data Types
--------------------

The LDM can store various V2X message types:

.. list-table::
   :header-rows: 1
   :widths: 15 25 60

   * - Type
     - Access Permission
     - Description
   * - **CAM**
     - ``AccessPermission.CAM``
     - Cooperative Awareness Messages from vehicles
   * - **DENM**
     - ``AccessPermission.DENM``
     - Decentralized Environmental Notifications
   * - **VAM**
     - ``AccessPermission.VAM``
     - VRU Awareness Messages
   * - **MAPEM**
     - ``AccessPermission.MAPEM``
     - Map topology messages
   * - **SPATEM**
     - ``AccessPermission.SPATEM``
     - Signal phase and timing

----

Getting Started
---------------

Step 1: Create the LDM
~~~~~~~~~~~~~~~~~~~~~~

Use the ``LDMFactory`` to create an LDM instance:

.. code-block:: python

   from flexstack.facilities.local_dynamic_map.factory import LDMFactory
   from flexstack.facilities.local_dynamic_map.ldm_classes import (
       Location,
       GeometricArea,
       Circle,
   )

   # Define LDM location (your position)
   ldm_location = Location.initializer(
       latitude=int(41.386931 * 10**7),   # Scaled integer format
       longitude=int(2.112104 * 10**7),
   )

   # Define area of interest (5 km radius)
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

**LDM Configuration Options:**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Parameter
     - Description
   * - ``ldm_maintenance_type``
     - ``"Reactive"`` — cleans up on access
   * - ``ldm_service_type``
     - ``"Reactive"`` — processes requests on demand
   * - ``ldm_database_type``
     - ``"Dictionary"`` — in-memory Python dict storage

Step 2: Connect Location Updates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Keep the LDM's area of maintenance updated with your position:

.. code-block:: python

   from flexstack.utils.static_location_service import ThreadStaticLocationService

   location_service = ThreadStaticLocationService(
       period=1000,
       latitude=41.386931,
       longitude=2.112104,
   )

   # Update LDM location when position changes
   location_service.add_callback(ldm_location.location_service_callback)

Step 3: Connect to Facility Services
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The LDM works best when connected to facility services like CA Basic Service:

.. code-block:: python

   from flexstack.facilities.ca_basic_service.ca_basic_service import (
       CooperativeAwarenessBasicService,
   )

   # CA Basic Service automatically publishes to LDM
   ca_basic_service = CooperativeAwarenessBasicService(
       btp_router=btp_router,
       vehicle_data=vehicle_data,
       ldm=ldm,  # Pass the LDM here
   )

----

Data Providers
--------------

Data Providers publish messages to the LDM. Facility services (CAM, DENM, VAM) 
automatically register as providers when you pass the LDM to them.

Register a Custom Provider
~~~~~~~~~~~~~~~~~~~~~~~~~~

For custom applications that need to publish data:

.. code-block:: python

   from flexstack.facilities.local_dynamic_map.ldm_classes import (
       RegisterDataProviderReq,
       AccessPermission,
       TimeValidity,
   )
   from flexstack.facilities.local_dynamic_map.ldm_constants import CAM

   # Register as a data provider
   ldm.ldm_if_ldm_3.register_data_provider(
       RegisterDataProviderReq(
           application_id=CAM,
           access_permissions=[AccessPermission.CAM],
           time_validity=TimeValidity(5),  # Messages valid for 5 seconds
       )
   )

Publish Data
~~~~~~~~~~~~

.. code-block:: python

   from flexstack.facilities.local_dynamic_map.ldm_classes import (
       AddDataProviderReq,
       TimestampIts,
       Location,
       TimeValidity,
   )

   # Publish a CAM to the LDM
   timestamp = TimestampIts.initialize_with_utc_timestamp_seconds()
   
   response = ldm.ldm_if_ldm_3.add_provider_data(
       AddDataProviderReq(
           application_id=CAM,
           timestamp=timestamp,
           location=Location.location_builder_circle(
               latitude=cam["cam"]["camParameters"]["basicContainer"]["referencePosition"]["latitude"],
               longitude=cam["cam"]["camParameters"]["basicContainer"]["referencePosition"]["longitude"],
               altitude=cam["cam"]["camParameters"]["basicContainer"]["referencePosition"]["altitude"]["altitudeValue"],
               radius=0,
           ),
           data_object=cam,
           time_validity=TimeValidity(5),
       )
   )

----

Data Consumers
--------------

Data Consumers retrieve messages from the LDM using queries or subscriptions.

Register as a Consumer
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from flexstack.facilities.local_dynamic_map.ldm_classes import (
       RegisterDataConsumerReq,
       RegisterDataConsumerResp,
       AccessPermission,
       GeometricArea,
       Circle,
   )
   from flexstack.facilities.local_dynamic_map.ldm_constants import CAM

   # Register to consume CAMs and VAMs
   response: RegisterDataConsumerResp = ldm.if_ldm_4.register_data_consumer(
       RegisterDataConsumerReq(
           application_id=CAM,
           access_permisions=(
               AccessPermission.CAM,
               AccessPermission.VAM,
               AccessPermission.DENM,
           ),
           area_of_interest=GeometricArea(
               circle=Circle(radius=5000),  # 5 km radius
               rectangle=None,
               ellipse=None,
           ),
       )
   )

   if response.result == 2:
       print("Registration failed!")
       exit(1)

----

Querying the LDM
----------------

Query for specific messages using filters:

.. mermaid::

   flowchart LR
       APP[Application] -->|"Query Request"| LDM[(LDM)]
       LDM -->|"Filtered Results"| APP
       
       subgraph "Query Options"
           F[Filter by field]
           O[Order results]
           T[Filter by type]
       end

Basic Query
~~~~~~~~~~~

.. code-block:: python

   from flexstack.facilities.local_dynamic_map.ldm_classes import (
       RequestDataObjectsReq,
       RequestDataObjectsResp,
       Filter,
       FilterStatement,
       ComparisonOperators,
       OrderTupleValue,
       OrderingDirection,
   )
   from flexstack.facilities.local_dynamic_map.ldm_constants import CAM, VAM

   # Create a query for CAMs and VAMs
   request = RequestDataObjectsReq(
       application_id=CAM,
       data_object_type=[CAM, VAM],
       priority=0,
       order=(OrderTupleValue("timeStamp", OrderingDirection.ASCENDING),),
       filter=None,  # No filter = return all
   )

   # Execute the query
   result: RequestDataObjectsResp = ldm.request_data_objects(request)

   for obj in result.data_objects:
       print(f"Station: {obj['dataObject']['header']['stationId']}")

Filtered Query
~~~~~~~~~~~~~~

Find messages from a specific station:

.. code-block:: python

   # Filter: header.stationId == 12345
   filter = Filter(
       FilterStatement(
           "header.stationId",
           ComparisonOperators.EQUAL,
           12345,
       )
   )

   request = RequestDataObjectsReq(
       application_id=CAM,
       data_object_type=[CAM],
       priority=0,
       order=(OrderTupleValue("timeStamp", OrderingDirection.DESCENDING),),
       filter=filter,
   )

   result = ldm.request_data_objects(request)

**Available Comparison Operators:**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Operator
     - Description
   * - ``EQUAL``
     - Field equals value
   * - ``NOT_EQUAL``
     - Field does not equal value
   * - ``GREATER_THAN``
     - Field is greater than value
   * - ``LESS_THAN``
     - Field is less than value

----

Subscribing to Updates
----------------------

Get notified when new messages arrive:

.. mermaid::

   sequenceDiagram
       participant App as Application
       participant LDM as LDM
       participant CAM as CA Basic Service
       
       App->>LDM: Subscribe (filter, callback)
       LDM-->>App: Subscription confirmed
       
       loop Every matching message
           CAM->>LDM: New CAM arrives
           LDM->>App: Callback with data
       end

Subscribe Example
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from flexstack.facilities.local_dynamic_map.ldm_classes import (
       SubscribeDataobjectsReq,
       SubscribeDataObjectsResp,
       SubscribeDataobjectsResult,
       Filter,
       FilterStatement,
       ComparisonOperators,
       OrderTupleValue,
       OrderingDirection,
       TimestampIts,
   )

   # Define callback function
   def on_new_message(data: RequestDataObjectsResp) -> None:
       for obj in data.data_objects:
           station_id = obj["dataObject"]["header"]["stationId"]
           print(f"📨 New message from station {station_id}")

   # Subscribe to CAMs (excluding our own)
   MY_STATION_ID = 12345
   
   response: SubscribeDataObjectsResp = ldm.if_ldm_4.subscribe_data_consumer(
       SubscribeDataobjectsReq(
           application_id=CAM,
           data_object_type=(CAM,),
           priority=1,
           filter=Filter(
               filter_statement_1=FilterStatement(
                   "header.stationId",
                   ComparisonOperators.NOT_EQUAL,
                   MY_STATION_ID,
               )
           ),
           notify_time=TimestampIts(0),  # Notify immediately
           multiplicity=1,
           order=(
               OrderTupleValue(
                   attribute="cam.generationDeltaTime",
                   ordering_direction=OrderingDirection.ASCENDING,
               ),
           ),
       ),
       on_new_message,  # Callback function
   )

   if response.result != SubscribeDataobjectsResult.SUCCESSFUL:
       print("Subscription failed!")

----

LDM Data Object
---------------

Messages are stored as LDM Data Objects:

.. code-block:: python

   # Example CAM stored in LDM
   data_object = {
       "header": {
           "protocolVersion": 2,
           "messageId": 2,
           "stationId": 12345
       },
       "cam": {
           "generationDeltaTime": 5000,
           "camParameters": {
               "basicContainer": {
                   "stationType": 5,
                   "referencePosition": {
                       "latitude": 413869310,
                       "longitude": 21121040,
                       # ... more fields
                   }
               },
               "highFrequencyContainer": {
                   # Speed, heading, etc.
               }
           }
       }
   }

----

Area of Maintenance
-------------------

The LDM only keeps messages within a defined geographical area:

.. mermaid::

   flowchart TB
       subgraph "Area of Maintenance"
           CENTER[Your Position<br/>📍]
           R1((5 km radius))
       end
       
       MSG1[Message A<br/>✅ Inside] --> CENTER
       MSG2[Message B<br/>✅ Inside] --> CENTER
       MSG3[Message C<br/>❌ Outside] -.->|"Rejected"| CENTER
       
       style CENTER fill:#e8f5e9,stroke:#2e7d32
       style MSG3 fill:#ffebee,stroke:#c62828

Messages outside the area of maintenance are automatically removed.

----

Complete Example
----------------

Here's a complete example using LDM with CA Basic Service:

.. code-block:: python
   :linenos:

   #!/usr/bin/env python3
   """
   Local Dynamic Map Example
   
   Stores and queries CAMs using the LDM.
   Run with: sudo python ldm_example.py
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
   from flexstack.facilities.ca_basic_service.ca_basic_service import (
       CooperativeAwarenessBasicService,
   )
   from flexstack.facilities.ca_basic_service.cam_transmission_management import VehicleData
   from flexstack.facilities.local_dynamic_map.factory import LDMFactory
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
   from flexstack.facilities.local_dynamic_map.ldm_constants import CAM

   logging.basicConfig(level=logging.INFO)

   # Configuration
   POSITION = [41.386931, 2.112104]
   MAC_ADDRESS = bytes([(random.randint(0, 255) & 0xFE) | 0x02] + 
                       [random.randint(0, 255) for _ in range(5)])
   STATION_ID = random.randint(1, 2147483647)


   def main():
       # Location Service
       location_service = ThreadStaticLocationService(
           period=1000,
           latitude=POSITION[0],
           longitude=POSITION[1],
       )

       # GeoNetworking
       mib = MIB(
           itsGnLocalGnAddr=GNAddress(
               m=M.GN_MULTICAST,
               st=ST.PASSENGER_CAR,
               mid=MID(MAC_ADDRESS),
           ),
       )
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

       # Register as LDM Consumer
       response: RegisterDataConsumerResp = ldm.if_ldm_4.register_data_consumer(
           RegisterDataConsumerReq(
               application_id=CAM,
               access_permisions=(AccessPermission.CAM,),
               area_of_interest=ldm_area,
           )
       )
       if response.result == 2:
           print("❌ LDM registration failed!")
           exit(1)

       # Subscribe to incoming CAMs
       def on_cam_received(data: RequestDataObjectsResp) -> None:
           if data.data_objects:
               station = data.data_objects[0]["dataObject"]["header"]["stationId"]
               print(f"📨 Received CAM from station {station}")

       sub_response: SubscribeDataObjectsResp = ldm.if_ldm_4.subscribe_data_consumer(
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
       if sub_response.result != SubscribeDataobjectsResult.SUCCESSFUL:
           print("❌ LDM subscription failed!")
           exit(1)

       # CA Basic Service with LDM
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

       # Link Layer
       btp_router.freeze_callbacks()
       link_layer = RawLinkLayer(
           "lo",
           MAC_ADDRESS,
           receive_callback=gn_router.gn_data_indicate,
       )
       gn_router.link_layer = link_layer

       print("✅ LDM with CA Basic Service running!")
       print("📡 Sending CAMs and listening for others...")
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

Use Cases
---------

.. grid:: 2
    :gutter: 3

    .. grid-item-card:: 🚗 Collision Avoidance
        
        Query the LDM to find nearby vehicles and calculate collision risks 
        based on their positions and trajectories.

    .. grid-item-card:: 🚦 Traffic Analysis
        
        Subscribe to all CAMs in an area to analyze traffic density, 
        average speeds, and flow patterns.

    .. grid-item-card:: ⚠️ Hazard Awareness
        
        Store DENMs in the LDM and query for active hazards along your 
        planned route.

    .. grid-item-card:: 🚴 VRU Protection
        
        Combine CAMs and VAMs in the LDM to detect vulnerable road users 
        near vehicles.

----

See Also
--------

- :doc:`/getting_started` — Complete V2X tutorial
- :doc:`ca_basic_service` — Cooperative Awareness Messages
- :doc:`den_service` — Decentralized Environmental Notifications
- :doc:`vru_awareness_service` — VRU Awareness Messages
- :doc:`/modules/btp` — Transport layer
