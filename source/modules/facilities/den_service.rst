Decentralized Environmental Notification (DEN) Service
======================================================

The **Decentralized Environmental Notification (DEN) Service** allows vehicles and infrastructure to share 
environmental hazard notifications using **Decentralized Environmental Notification Messages (DENM)**. 
These messages play a crucial role in cooperative intelligent transport systems (C-ITS), functioning alongside 
other facility-layer messages such as **Cooperative Awareness Messages (CAMs)** and **VRU Awareness Messages (VAMs)**.

**Required** components are:

- :ref:`link_layer`
- :ref:`GeoNetworking Router <geonetworking>`
- :ref:`BTP Router <btp>`
- :ref:`Location Service <location_service>`
- `DEN Service <#den_service>`__

**Optional** (but recommended) components are:

- `Local Dynamic Map <local_dynamic_map.rst>`__

.. important::
   `Logging <logging.rst>`__ is always an optional component but highly recommended.

A quickstart is available `here <#quickstart>`__, but continue reading for a detailed overview.

--------------

DENM Overview
-------------

The **Decentralized Environmental Notification Message (DENM)** is defined in `ETSI TS 103 831 V2.2.1 
(2024-04) <https://www.etsi.org/deliver/etsi_ts/103800_103899/103831/02.02.01_60/ts_103831v020201p.pdf>`__.

A DENM is composed of three core submodules within the **facilities layer**:

- `DEN Service <#den-service>`__
- `DEN Transmission Management <#den-transmission-management>`__
- `DEN Reception Management <#den-reception-management>`__

--------------

DEN Service
~~~~~~~~~~~

The **DEN Service** is responsible for handling DENM messages, including their creation, management, and transmission. 
It interfaces with all needed submodules like the **DEN Transmission Management**, **DEN Reception Management**, and **DEN Coder**.

Basic usage:

.. code:: py

   from flexstack.facilities.decentralized_environmental_notification_service.den_service import DecentralizedEnvironmentalNotificationService

   den_service = DecentralizedEnvironmentalNotificationService(btp_router=btp_router,
                                                               vehicle_data=vehicle_data)

The :ref:`BTP Router <btp>` and the Vehicle Data are required dependencies.

DEN Reception Management
~~~~~~~~~~~~~~~~~~~~~~~~~

The **DEN Reception Management** component handles incoming DENMs from other ITS stations. 
It processes and validates messages, ensuring they are appropriately relayed to the application layer.

This component does not require explicit instantiation, as it is automatically handled within the **DEN Service**.


DEN Transmission Management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **DEN Transmission Management** component ensures DENM messages are transmitted correctly. 
It manages message triggering, periodic updates, and termination based on specific event conditions.
Since this message can be addapted to cover several use cases, its implementation is strongly related with the applications layes.
In this case, the DEN Transmission Management covers 2 use cases:

- Emergency Vehicle Approaching Service
- Longitudinal Collision Risk Warning

--------------

Application Layer: Emergency Vehicle Approaching Service
--------------------------------------------------------

The **application layer** builds upon the **DEN Service** to implement higher-level functionalities. 
One example is the **Emergency Vehicle Approaching Service**, which is part of the **Road Hazard Signalling (RHS) application** 
described in `ETSI TS 101 539-1 V1.1.1 (2013-08) <https://www.etsi.org/deliver/etsi_ts/101500_101599/10153901/01.01.01_60/ts_10153901v010101p.pdf>`__.

The **Emergency Vehicle Approaching Service** is designed to:

- Alert nearby vehicles about an approaching emergency vehicle.
- Use DENMs to broadcast the emergency vehicle's position, speed, and trajectory.
- Enhance road safety by allowing other vehicles to react accordingly.

It relies on the **DEN Service** for message management and transmission.


An example of how to use this service is provided in the `Quickstart <#quickstart>`__ section below.

--------------

Quickstart
----------

The following example demonstrates how to set up the **Emergency Vehicle Approaching Service** using the **DEN Service**:

.. code:: py

   import logging
   import logging.config

   from flexstack.applications.road_hazard_signalling_service.emergency_vehicle_approaching_service import EmergencyVehicleApproachingService
   from flexstack.facilities.ca_basic_service.cam_transmission_management import VehicleData
   from flexstack.utils.static_location_service import ThreadStaticLocationService as LocationService

   from flexstack.btp.router import Router as BTPRouter

   from flexstack.geonet.router import Router
   from flexstack.geonet.mib import MIB
   from flexstack.geonet.gn_address import GNAddress, M, ST, MID

   from flexstack.linklayer.raw_link_layer import RawLinkLayer


   logging.basicConfig(level=logging.INFO)

   # Geonet
   mac_address = b"\x00\x00\x00\x00\x00\x00"
   mib = MIB()
   gn_addr = GNAddress()
   gn_addr.set_m(M.GN_MULTICAST)
   gn_addr.set_st(ST.CYCLIST)
   gn_addr.set_mid(MID(mac_address))
   mib.itsGnLocalGnAddr = gn_addr
   gn_router = Router(mib=mib, sign_service=None)

   # Link-Layer
   link_layer = RawLinkLayer("lo", mac_address=mac_address,
                     receive_callback=gn_router.gn_data_indicate)
   gn_router.link_layer = link_layer

   # BTP
   btp_router = BTPRouter(gn_router)
   gn_router.register_indication_callback(btp_router.btp_data_indication)

   # Facility - Location Service
   location_service = LocationService()
   location_service.add_callback(gn_router.refresh_ego_position_vector)

   # Application - Emergency Vehicle Approaching Service
   vehicle_data = VehicleData()
   vehicle_data.station_id = 10  # Station Id of the ITS PDU Header
   vehicle_data.station_type = 5  # Station Type as specified in ETSI TS 102 894-2 V2.3.1 (2024-08)
   vehicle_data.drive_direction = "forward"

   denm_duration = 1000  # Each DENM is repeated for 1 second before updating
   denm_service = EmergencyVehicleApproachingService(btp_router=btp_router,
                                                     vehicle_data=vehicle_data,
                                                     duration=denm_duration)

   location_service.add_callback(denm_service.trigger_denm_sending)

   # Start sending DENMs
   location_service.location_service_thread.join()

Logging has been included to provide a way of visualizing the sent
messages. View `Logging <logging.rst>`__ to get more detailed information on how to use
it.

--------------

You can explore the examples scripts avaialble, expand upon them or use
them as a baseline to create your own. If you have any questions about
the agents, feel free to post in the `forum <forum-url>`__.