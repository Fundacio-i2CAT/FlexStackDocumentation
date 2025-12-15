.. _den_service:

Decentralized Environmental Notification (DEN) Service
======================================================

The DEN Service broadcasts **hazard warnings** to nearby vehicles using **Decentralized Environmental 
Notification Messages (DENMs)**. While CAMs say "I'm here," DENMs say "Watch out for this!"

.. note::

   The DEN Service implements ETSI TS 103 831 V2.2.1 (2024-04). DENMs are event-driven messages 
   that warn about road hazards, accidents, emergency vehicles, and other dangerous situations.

What DENMs Are For
------------------

DENMs alert drivers to hazardous situations:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Use Case
     - Description
   * - 🚑 **Emergency Vehicle**
     - Ambulance, fire truck, or police approaching
   * - 🚧 **Road Hazard**
     - Obstacle on road, slippery conditions, road works
   * - 💥 **Accident**
     - Collision ahead, stationary vehicle
   * - ⚠️ **Dangerous Situation**
     - Wrong-way driver, traffic jam end warning
   * - 🌧️ **Weather**
     - Fog, heavy rain, ice on road

CAM vs DENM
-----------

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Aspect
     - CAM
     - DENM
   * - **Purpose**
     - "I am here"
     - "Watch out for this"
   * - **Trigger**
     - Periodic (time/position based)
     - Event-driven (hazard detected)
   * - **Lifetime**
     - Single transmission
     - Persists until terminated
   * - **BTP Port**
     - 2001
     - 2002

Architecture
------------

The DEN Service consists of three components:

.. mermaid::

   flowchart TB
       subgraph "Application Layer"
           EVA[Emergency Vehicle<br/>Approaching Service]
           LCRW[Longitudinal Collision<br/>Risk Warning]
           APP[Other Applications]
       end
       
       subgraph "DEN Service"
           DEN[DEN Service]
           TM[Transmission<br/>Management]
           RM[Reception<br/>Management]
           COD[DEN Coder]
       end
       
       subgraph "Transport"
           BTP[BTP Router<br/>Port 2002]
       end
       
       subgraph "Optional"
           LDM[(Local Dynamic Map)]
       end
       
       EVA --> DEN
       LCRW --> DEN
       APP --> DEN
       DEN <--> TM
       DEN <--> RM
       DEN <--> COD
       DEN <-->|"Send/Receive"| BTP
       RM -.->|"Store"| LDM
       
       style DEN fill:#ffebee,stroke:#c62828
       style EVA fill:#fff3e0
       style LCRW fill:#fff3e0

**Components:**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Component
     - Description
   * - **DEN Service**
     - Main service handling DENM creation, management, and lifecycle
   * - **Transmission Management**
     - Handles message triggering, updates, and termination
   * - **Reception Management**
     - Processes incoming DENMs (automatic, no setup needed)
   * - **DEN Coder**
     - Encodes/decodes DENM ASN.1 format

----

Getting Started
---------------

Prerequisites
~~~~~~~~~~~~~

The DEN Service requires:

- **BTP Router** — for transport (port 2002)
- **Vehicle Data** — your station's information
- **Location Service** — for position updates (recommended)

Optional but recommended:

- **Local Dynamic Map** — for storing received DENMs

Step 1: Create DEN Service
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from flexstack.facilities.decentralized_environmental_notification_service.den_service import (
       DecentralizedEnvironmentalNotificationService,
   )
   from flexstack.facilities.ca_basic_service.cam_transmission_management import VehicleData

   # Configure vehicle data
   vehicle_data = VehicleData(
       station_id=12345,
       station_type=5,  # Passenger car
       drive_direction="forward",
       vehicle_length={"vehicleLengthValue": 42, "vehicleLengthConfidenceIndication": "unavailable"},
       vehicle_width=18,
   )

   # Create DEN Service
   den_service = DecentralizedEnvironmentalNotificationService(
       btp_router=btp_router,
       vehicle_data=vehicle_data,
   )

That's it! The DEN Service is now ready. Reception management is automatic — incoming DENMs 
will be processed without any additional setup.

Step 2: Use an Application Service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The DEN Service is typically used through **application layer services** that implement 
specific use cases. FlexStack provides two built-in applications:

1. **Emergency Vehicle Approaching Service** — alerts about approaching emergency vehicles
2. **Longitudinal Collision Risk Warning** — warns about collision risks ahead

----

Emergency Vehicle Approaching Service
-------------------------------------

This service broadcasts DENMs when an emergency vehicle (ambulance, fire truck, police) 
needs to alert nearby traffic.

.. code-block:: python

   from flexstack.applications.road_hazard_signalling_service.emergency_vehicle_approaching_service import (
       EmergencyVehicleApproachingService,
   )
   from flexstack.utils.static_location_service import generate_tpv_dict_with_current_timestamp

   # Create the application service
   emergency_service = EmergencyVehicleApproachingService(
       den_service=den_service,
       duration=10000,  # DENM validity duration in ms
   )

   # Trigger a DENM (e.g., when emergency lights are activated)
   position = generate_tpv_dict_with_current_timestamp(
       latitude=41.386931,
       longitude=2.112104,
   )
   emergency_service.trigger_denm_sending(position)

**Parameters:**

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Parameter
     - Type
     - Description
   * - ``den_service``
     - ``DENService``
     - The DEN Service instance
   * - ``duration``
     - ``int``
     - How long the DENM remains valid (milliseconds)

----

DENM Lifecycle
--------------

Unlike CAMs (which are fire-and-forget), DENMs have a **lifecycle**:

.. mermaid::

   stateDiagram-v2
       [*] --> Active: Trigger
       Active --> Active: Update
       Active --> Terminated: Cancel/Expire
       Terminated --> [*]
       
       note right of Active: DENM is valid and<br/>being rebroadcast
       note right of Terminated: Event is over,<br/>DENM cancelled

**DENM Actions:**

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Action
     - Description
   * - **Trigger**
     - Start a new DENM (hazard detected)
   * - **Update**
     - Modify an existing DENM (situation changed)
   * - **Terminate**
     - Cancel the DENM (hazard cleared)

Each DENM is identified by an **ActionID** (station ID + sequence number), allowing 
receivers to track updates and terminations.

----

DENM Message Structure
----------------------

A DENM contains four containers:

.. mermaid::

   flowchart LR
       subgraph DENM[DENM Message]
           H[ITS PDU Header]
           MC[Management Container]
           SC[Situation Container]
           LC[Location Container]
           AC[À la Carte Container]
       end
       
       H --> MC --> SC --> LC --> AC

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Container
     - Contents
   * - **Management**
     - Action ID, detection time, reference time, event position, validity duration
   * - **Situation**
     - Cause code, sub-cause code, severity, linked cause (optional)
   * - **Location**
     - Event area, road type, lane position, traces
   * - **À la Carte**
     - Additional optional data (road works, stationary vehicle, etc.)

----

Complete Example
----------------

Here's a complete script demonstrating the Emergency Vehicle Approaching Service:

.. code-block:: python
   :linenos:

   #!/usr/bin/env python3
   """
   Emergency Vehicle Approaching Service Example
   
   Broadcasts DENMs to alert nearby vehicles about an approaching emergency vehicle.
   Run with: sudo python emergency_vehicle_example.py
   """

   import logging
   import random
   import time

   from flexstack.linklayer.raw_link_layer import RawLinkLayer
   from flexstack.geonet.router import Router as GNRouter
   from flexstack.geonet.mib import MIB
   from flexstack.geonet.gn_address import GNAddress, M, ST, MID
   from flexstack.btp.router import Router as BTPRouter
   from flexstack.utils.static_location_service import (
       ThreadStaticLocationService,
       generate_tpv_dict_with_current_timestamp,
   )
   from flexstack.facilities.ca_basic_service.cam_transmission_management import VehicleData
   from flexstack.facilities.decentralized_environmental_notification_service.den_service import (
       DecentralizedEnvironmentalNotificationService,
   )
   from flexstack.applications.road_hazard_signalling_service.emergency_vehicle_approaching_service import (
       EmergencyVehicleApproachingService,
   )

   logging.basicConfig(level=logging.INFO)

   # Configuration
   POSITION = [41.386931, 2.112104]  # Barcelona
   MAC_ADDRESS = bytes([random.randint(0, 255) | 0x02 for _ in range(6)])
   STATION_ID = random.randint(1, 2147483647)


   def main():
       # Location Service
       location_service = ThreadStaticLocationService(
           period=1,
           latitude=POSITION[0],
           longitude=POSITION[1],
       )

       # GeoNetworking
       mib = MIB(
           itsGnLocalGnAddr=GNAddress(
               m=M.GN_MULTICAST,
               st=ST.SPECIAL_VEHICLE,  # Emergency vehicle
               mid=MID(MAC_ADDRESS),
           ),
       )
       gn_router = GNRouter(mib=mib, sign_service=None)
       location_service.add_callback(gn_router.refresh_ego_position_vector)

       # BTP
       btp_router = BTPRouter(gn_router)
       gn_router.register_indication_callback(btp_router.btp_data_indication)

       # Vehicle Data (emergency vehicle)
       vehicle_data = VehicleData(
           station_id=STATION_ID,
           station_type=10,  # Special vehicle (emergency)
           drive_direction="forward",
           vehicle_length={"vehicleLengthValue": 70, "vehicleLengthConfidenceIndication": "unavailable"},
           vehicle_width=25,
       )

       # DEN Service
       den_service = DecentralizedEnvironmentalNotificationService(
           btp_router=btp_router,
           vehicle_data=vehicle_data,
       )

       # Emergency Vehicle Approaching Service
       emergency_service = EmergencyVehicleApproachingService(
           den_service=den_service,
           duration=10000,  # 10 second validity
       )

       # Trigger DENM (simulating emergency lights activation)
       print("🚨 Triggering Emergency Vehicle DENM...")
       emergency_service.trigger_denm_sending(
           generate_tpv_dict_with_current_timestamp(POSITION[0], POSITION[1])
       )

       # Link Layer
       btp_router.freeze_callbacks()
       link_layer = RawLinkLayer(
           "lo",
           MAC_ADDRESS,
           receive_callback=gn_router.gn_data_indicate,
       )
       gn_router.link_layer = link_layer

       print("✅ Emergency Vehicle Service running!")
       print("📡 Broadcasting DENMs...")
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

Cause Codes
-----------

DENMs use standardized cause codes (defined in ETSI TS 102 894-2):

.. list-table::
   :header-rows: 1
   :widths: 15 30 55

   * - Code
     - Cause
     - Example Sub-causes
   * - 1
     - Traffic Condition
     - Traffic jam, slow traffic
   * - 2
     - Accident
     - Multi-vehicle, heavy accident
   * - 3
     - Road Works
     - Construction, maintenance
   * - 6
     - Adverse Weather
     - Fog, rain, ice, wind
   * - 9
     - Hazardous Location
     - Obstacle, animal on road
   * - 12
     - Wrong Way Driver
     - Vehicle going wrong direction
   * - 14
     - Rescue/Recovery
     - Emergency vehicle, recovery in progress
   * - 15
     - Emergency Vehicle
     - Approaching ambulance/fire/police
   * - 91
     - Vehicle Breakdown
     - Stationary disabled vehicle
   * - 94
     - Stationary Vehicle
     - Stopped vehicle (various reasons)

----

See Also
--------

- :doc:`/getting_started` — Complete V2X tutorial
- :doc:`ca_basic_service` — Cooperative Awareness Messages
- :doc:`local_dynamic_map` — Store and query received DENMs
- :doc:`/modules/btp` — Transport layer (BTP port 2002)
- :doc:`/modules/applications` — Application layer services