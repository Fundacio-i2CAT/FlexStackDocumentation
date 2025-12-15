.. _vru_awareness_service:

VRU Awareness Service
=====================

The VRU Awareness Service protects **Vulnerable Road Users** — pedestrians, cyclists, and other 
unprotected road users — by broadcasting their presence to nearby vehicles using **VRU Awareness 
Messages (VAMs)**.

.. note::

   The VRU Awareness Service implements ETSI TS 103 300-3 V2.2.1. VAMs are similar to CAMs but 
   specifically designed for VRUs who need extra protection on the road.

What Are VRUs?
--------------

Vulnerable Road Users include anyone not protected by a vehicle body:

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Type
     - Station Type
     - Examples
   * - 🚶 **Pedestrian**
     - 1
     - Walkers, joggers, people with mobility aids
   * - 🚴 **Cyclist**
     - 2
     - Bicycles, e-bikes, cargo bikes
   * - 🛵 **Moped**
     - 3
     - Scooters, mopeds (< 50cc)
   * - 🏍️ **Motorcycle**
     - 4
     - Motorcycles, motorbikes
   * - 🛴 **Other**
     - Various
     - E-scooters, skateboards, wheelchairs

VAM vs CAM
----------

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Aspect
     - CAM
     - VAM
   * - **For**
     - Vehicles
     - Vulnerable Road Users
   * - **Purpose**
     - Vehicle awareness
     - VRU protection
   * - **BTP Port**
     - 2001
     - 2004
   * - **Clustering**
     - No
     - Yes (groups of VRUs)
   * - **Device**
     - Vehicle OBU
     - Smartphone, wearable, bike computer

Architecture
------------

The VRU Awareness Service consists of several components:

.. mermaid::

   flowchart TB
       subgraph "Application Layer"
           APP[VRU Application]
       end
       
       subgraph "VRU Awareness Service"
           VAS[VRU Basic Service<br/>Management]
           TM[VAM Transmission<br/>Management]
           RM[VAM Reception<br/>Management]
           CM[Cluster Management<br/>⚠️ Not Implemented]
           COD[VAM Coder]
       end
       
       subgraph "Data Providers"
           DDP[Device Data Provider]
           LOC[Location Service]
       end
       
       subgraph "Transport"
           BTP[BTP Router<br/>Port 2004]
       end
       
       APP --> VAS
       DDP --> VAS
       LOC --> TM
       VAS <--> TM
       VAS <--> RM
       VAS <--> CM
       VAS <--> COD
       VAS <-->|"Send/Receive"| BTP
       
       style VAS fill:#e3f2fd,stroke:#1565c0
       style CM fill:#ffebee,stroke:#c62828,stroke-dasharray: 5 5

**Components:**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Component
     - Description
   * - **VRU Basic Service**
     - Main service coordinating all VAM operations
   * - **VAM Transmission Management**
     - Handles when and how VAMs are sent
   * - **VAM Reception Management**
     - Processes incoming VAMs (automatic)
   * - **Cluster Management**
     - Groups nearby VRUs (⚠️ not yet implemented)
   * - **VAM Coder**
     - Encodes/decodes ASN.1 format
   * - **Device Data Provider**
     - Provides VRU device information

----

Getting Started
---------------

Step 1: Configure Device Data Provider
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unlike vehicles (which use ``VehicleData``), VRUs use a ``DeviceDataProvider``:

.. code-block:: python

   from flexstack.facilities.vru_awareness_service.vam_transmission_management import (
       DeviceDataProvider,
   )

   # Configure VRU device
   device_data = DeviceDataProvider(
       station_id=12345,      # Unique identifier
       station_type=2,        # 2 = Cyclist
   )

**Station Types for VRUs:**

.. list-table::
   :header-rows: 1
   :widths: 15 25 60

   * - Value
     - Type
     - Description
   * - 1
     - Pedestrian
     - Person on foot
   * - 2
     - Cyclist
     - Bicycle rider
   * - 3
     - Moped
     - Light motorized two-wheeler
   * - 4
     - Motorcycle
     - Motorcycle rider

Step 2: Set Up Prerequisites
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The VRU Awareness Service requires:

- **BTP Router** — for transport (port 2004)
- **Location Service** — for position updates

.. code-block:: python

   from flexstack.btp.router import Router as BTPRouter
   from flexstack.geonet.router import Router as GNRouter
   from flexstack.geonet.mib import MIB
   from flexstack.geonet.gn_address import GNAddress, M, ST, MID
   from flexstack.utils.static_location_service import ThreadStaticLocationService as LocationService
   from flexstack.linklayer.raw_link_layer import RawLinkLayer

   MAC_ADDRESS = b'\x00\x11\x22\x33\x44\x55'

   # Location Service
   location_service = LocationService()

   # GeoNetworking + BTP
   mib = MIB(
       itsGnLocalGnAddr=GNAddress(
           m=M.GN_MULTICAST,
           st=ST.CYCLIST,  # VRU type
           mid=MID(MAC_ADDRESS),
       ),
   )
   gn_router = GNRouter(mib=mib, sign_service=None)
   ll = RawLinkLayer(iface="lo", mac_address=MAC_ADDRESS, receive_callback=gn_router.gn_data_indicate)
   gn_router.link_layer = ll
   btp_router = BTPRouter(gn_router)
   gn_router.register_indication_callback(btp_router.btp_data_indication)
   location_service.add_callback(gn_router.refresh_ego_position_vector)

Step 3: Create VRU Awareness Service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from flexstack.facilities.vru_awareness_service.vru_awareness_service import (
       VRUAwarenessService,
   )

   # Create the VRU Awareness Service
   vru_service = VRUAwarenessService(
       btp_router=btp_router,
       device_data_provider=device_data,
   )

   # Connect location updates to trigger VAM transmission
   location_service.add_callback(
       vru_service.vam_transmission_management.location_service_callback
   )

That's it! The service will now:

- ✅ **Automatically send VAMs** when location updates arrive
- ✅ **Automatically receive VAMs** from other VRUs

----

VAM Generation Rules
--------------------

VAMs are generated when any of these conditions are met:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Trigger
     - Condition
   * - ⏱️ **Time elapsed**
     - Time since last VAM exceeds ``T_GenVamMax``
   * - 📍 **Position change**
     - Distance moved exceeds ``minReferencePointPositionChangeThreshold``
   * - 🏃 **Speed change**
     - Speed difference exceeds ``minGroundSpeedChangeThreshold``
   * - 🧭 **Direction change**
     - Heading change exceeds ``minGroundVelocityOrientationChangeThreshold``

This ensures VAMs are sent when relevant changes occur, not just periodically.

----

VAM Message Structure
---------------------

A VAM contains information specific to VRUs:

.. mermaid::

   flowchart LR
       subgraph VAM[VAM Message]
           H[ITS PDU Header]
           BC[VRU Basic Container]
           HFC[VRU High Frequency<br/>Container]
           LFC[VRU Low Frequency<br/>Container]
           CC[VRU Cluster<br/>Container]
       end
       
       H --> BC --> HFC --> LFC --> CC

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Container
     - Contents
   * - **Basic**
     - VRU type, reference position
   * - **High Frequency**
     - Speed, heading, acceleration (sent often)
   * - **Low Frequency**
     - Profile info, path history (sent less often)
   * - **Cluster**
     - Info about grouped VRUs (when clustering is active)

----

VRU Clustering
--------------

.. warning::

   VRU Clustering is **not yet implemented** in FlexStack.

Clustering allows multiple VRUs traveling together (e.g., a group of cyclists) to be 
represented by a single VAM, reducing network load while maintaining awareness.

.. mermaid::

   flowchart LR
       subgraph "Without Clustering"
           V1[VAM 1]
           V2[VAM 2]
           V3[VAM 3]
           V4[VAM 4]
       end
       
       subgraph "With Clustering"
           VC[Cluster VAM<br/>4 VRUs]
       end
       
       V1 & V2 & V3 & V4 -.->|"Future"| VC

----

Complete Example
----------------

Here's a complete script for a cyclist broadcasting VAMs:

.. code-block:: python
   :linenos:

   #!/usr/bin/env python3
   """
   VRU Awareness Service Example
   
   Broadcasts VAMs for a cyclist to alert nearby vehicles.
   Run with: sudo python vru_example.py
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
   from flexstack.facilities.vru_awareness_service.vru_awareness_service import (
       VRUAwarenessService,
   )
   from flexstack.facilities.vru_awareness_service.vam_transmission_management import (
       DeviceDataProvider,
   )

   logging.basicConfig(level=logging.INFO)

   # Configuration
   POSITION = [41.386931, 2.112104]  # Barcelona
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
               st=ST.CYCLIST,  # This is a cyclist
               mid=MID(MAC_ADDRESS),
           ),
       )
       gn_router = GNRouter(mib=mib, sign_service=None)
       location_service.add_callback(gn_router.refresh_ego_position_vector)

       # BTP
       btp_router = BTPRouter(gn_router)
       gn_router.register_indication_callback(btp_router.btp_data_indication)

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

       # Link Layer
       btp_router.freeze_callbacks()
       link_layer = RawLinkLayer(
           "lo",
           MAC_ADDRESS,
           receive_callback=gn_router.gn_data_indicate,
       )
       gn_router.link_layer = link_layer

       print("✅ VRU Awareness Service running!")
       print("🚴 Broadcasting VAMs as a cyclist...")
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

    .. grid-item-card:: 🚴 Cyclist Safety
        
        Cyclists broadcast their position to nearby vehicles, reducing collision risk at 
        intersections and blind spots.

    .. grid-item-card:: 🚶 Pedestrian Crossing
        
        Pedestrians with smartphones can alert approaching vehicles when crossing streets.

    .. grid-item-card:: 🛴 E-Scooter Awareness
        
        Electric scooter riders share their presence with traffic, especially important 
        in urban environments.

    .. grid-item-card:: 🏍️ Motorcycle Visibility
        
        Motorcyclists increase their visibility to cars and trucks that might not see them.

----

See Also
--------

- :doc:`/getting_started` — Complete V2X tutorial
- :doc:`ca_basic_service` — Vehicle Cooperative Awareness Messages
- :doc:`den_service` — Hazard warnings with DENMs
- :doc:`local_dynamic_map` — Store and query received VAMs
- :doc:`/modules/btp` — Transport layer (BTP port 2004)
