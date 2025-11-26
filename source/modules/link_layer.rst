.. _link_layer:

Link Layer
==========

.. _cv2xlinklayer:

CV2XLinkLayer
-------------

Overview
~~~~~~~~

`cv2xlinklayer` is a C++ library that provides an interface for Cellular Vehicle-to-Everything (C-V2X) communication. It interacts with a telematics SDK (`telux_cv2x`) to establish and manage transmission (Tx) and reception (Rx) flows. The library is exposed to Python using `pybind11`, allowing Python scripts to send and receive C-V2X messages.

Components
~~~~~~~~~~

`cv2x_link_layer.cpp`
^^^^^^^^^^^^^^^^^^^^
This file implements the main logic of the C-V2X communication layer, including:

- Initialization of the `Cv2xRadioManager`.
- Setup of transmission (Tx) and reception (Rx) flows.
- Callbacks for handling C-V2X status updates and data reception.
- A `send` method for transmitting data.
- A `receive` method for reading incoming messages.
- Integration with `pybind11` for Python compatibility.

`cv2x_link_layer.hpp`
^^^^^^^^^^^^^^^^^^^^
This header file declares the `CV2XLinkLayer` class and its methods.

`CMakeLists.txt`
^^^^^^^^^^^^^^^^
This file defines the build process, including:

- Minimum required CMake version (`3.12`).
- Setting the project name (`cv2xlinklayer`).
- Enforcing C++11 standard.
- Finding and linking `pybind11` and `telux_cv2x`.
- Generating a shared library (`cv2xlinklayer.so`).

Building the Library
~~~~~~~~~~~~~~~~~~~~

Prerequisites
^^^^^^^^^^^^^
Ensure the following dependencies are installed:

- CMake (`>= 3.12`)
- `pybind11`
- `telux_cv2x` SDK
- A C++11-compliant compiler

Build Steps
^^^^^^^^^^^

.. code-block:: sh

    mkdir build && cd build
    cmake ..
    make

The output shared library (`cv2xlinklayer.so`) will be placed in the `lib` directory.

Using the Library in Python
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Importing the Module
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import cv2xlinklayer

Creating an Instance
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    link_layer = cv2xlinklayer.CV2XLinkLayer()

Sending Data
^^^^^^^^^^^^
.. code-block:: python

    data = "Hello, C-V2X!"
    link_layer.send(data)

Receiving Data
^^^^^^^^^^^^^^

.. code-block:: python

    received_data = link_layer.receive()
    print(received_data)

Complete Script
---------------

A whole script can be found below to transmit and receive in C-V2X:

.. code-block:: python

    # Configure logging
    import logging
    logging.basicConfig(level=logging.INFO)

    # Link Layer Imports
    from flexstack.linklayer.cv2x_link_layer import PythonCV2XLinkLayer

    # GeoNetworking imports
    from flexstack.geonet.router import Router as GNRouter
    from flexstack.geonet.mib import MIB
    from flexstack.geonet.gn_address import GNAddress, M, ST, MID

    # BTP Router imports
    from flexstack.btp.router import Router as BTPRouter

    # Location Service imports
    from flexstack.utils.static_location_service import ThreadStaticLocationService

    # Local Dynamic Map imports
    from flexstack.facilities.local_dynamic_map.factory import ldm_factory
    from flexstack.facilities.local_dynamic_map.ldm_classes import (
        Location,
        SubscribeDataobjectsReq,
        SubscribeDataObjectsResp,
        RegisterDataConsumerReq,
        RegisterDataConsumerResp,
        RequestDataObjectsResp,
    )
    from flexstack.facilities.local_dynamic_map.ldm_constants import CAM

    # CA Basic Service imports
    from flexstack.facilities.ca_basic_service.ca_basic_service import (
        CooperativeAwarenessBasicService,
    )
    from flexstack.facilities.ca_basic_service.cam_transmission_management import (
        VehicleData,
    )

    # Basic Configuration Parameters
    POSITION_COORDINATES = [41.386931, 2.112104]
    mac_address = b"\xaa\xbb\xcc\x11\x21\x11"
    station_id = int(mac_address[-1])

    # Instantiate a Location Service
    location_service = ThreadStaticLocationService(
        period=1000, latitude=POSITION_COORDINATES[0], longitude=POSITION_COORDINATES[1]
    )

    # Instantiate a GN router
    mib = MIB()
    gn_addr = GNAddress()
    gn_addr.set_m(M.GN_MULTICAST)
    gn_addr.set_st(ST.CYCLIST)
    gn_addr.set_mid(MID(mac_address))
    mib.itsGnLocalGnAddr = gn_addr
    gn_router = GNRouter(mib=mib, sign_service=None)
    location_service.add_callback(gn_router.refresh_ego_position_vector)

    # Instantiate a Link Layer
        #link_layer = RawLinkLayer("lo", mac_address, geonet_router.gn_data_indicate)
    link_layer = PythonCV2XLinkLayer(gn_router.gn_data_indicate)
    gn_router.link_layer = link_layer

    # Instantiate a BTP router
    btp_router = BTPRouter(gn_router)
    gn_router.register_indication_callback(btp_router.btp_data_indication)

    # Instantiate a Local Dynamic Map (LDM)
    ldm_location = Location.initializer()
    ldm = ldm_factory(
        ldm_location,
        ldm_maintenance_type="Reactive",
        ldm_service_type="Reactive",
        ldm_database_type="Dictionary",
    )
    location_service.add_callback(ldm_location.location_service_callback)

    # Subscribe to LDM
    register_data_consumer_reponse: RegisterDataConsumerResp = (
        ldm.if_ldm_4.register_data_consumer(
            RegisterDataConsumerReq(
                application_id=CAM,
                access_permisions=[CAM],
                area_of_interest=ldm_location,
            )
        )
    )
    if register_data_consumer_reponse.result == 2:
        exit(1)


    def ldm_subscription_callback(data: RequestDataObjectsResp) -> None:
        # We are printing any received CAM message.
        print(data.data_objects[0]["dataObject"]["header"]["stationId"])
        if data.data_objects[0]["dataObject"]["header"]["stationId"] != station_id:
            print(f'Received CAM from : {data.data_objects[0]["dataObject"]["header"]["stationId"]}')


    subscribe_data_consumer_response: SubscribeDataObjectsResp = (
        ldm.if_ldm_4.subscribe_data_consumer(
            SubscribeDataobjectsReq(
                application_id=CAM,
                data_object_type=[CAM],
                priority=None,
                filter=None,
                notify_time=0.5,
                multiplicity=None,
                order=None,
            ),
            ldm_subscription_callback,
        )
    )
    if subscribe_data_consumer_response.result.result != 0:
        exit(1)

    # Instantiate a CA Basic Service
    vehicle_data = VehicleData()
    vehicle_data.station_id = station_id  # Station Id of the ITS PDU Header
    vehicle_data.station_type = 5  # Station Type as specified in ETSI TS 102 894-2 V2.3.1 (2024-08)
    vehicle_data.drive_direction = "forward"
    vehicle_data.vehicle_length = {
        "vehicleLengthValue": 1023,  # as specified in ETSI TS 102 894-2 V2.3.1 (2024-08)
        "vehicleLengthConfidenceIndication": "unavailable",
    }
    vehicle_data.vehicle_width = 62

    ca_basic_service = CooperativeAwarenessBasicService(
        btp_router=btp_router,
        vehicle_data=vehicle_data,
    )
    location_service.add_callback(ca_basic_service.cam_transmission_management.location_service_callback)

    print("Press Ctrl+C to stop the program.")
    location_service.location_service_thread.join()

