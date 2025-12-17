Overview
========

FlexStack(R) is a software library implementing the ETSI C-ITS protocol stack. Its aim is to
facilitate and accelerate the development and integration of software applications on vehicles,
vulnerable road users (VRU), and roadside infrastructure that requires the exchange of V2X messages
(compliant with ETSI standards) with other actors of the V2X ecosystem.

Modules
-------

+-------------------+-------------------+----------------------------------------------------------+
| Module            | Service           | Features (Community Edition)                             |
+===================+===================+==========================================================+
| Link Layer        |                   | - CV2X, on Qualcomm-based chipsets (Telematics SDK)      |
|                   |                   | - IEEE 802.11p and Ethernet (Linux Layer 2 socket)       |
+-------------------+-------------------+----------------------------------------------------------+
| GeoNetworking     |                   | - Single Hop Broadcast (SHB)                             |
|                   |                   | - Geobroadcast (GBC)                                     |
+-------------------+-------------------+----------------------------------------------------------+
| BTP               |                   | BTP-A and BTP-B header processing                        |
+-------------------+-------------------+----------------------------------------------------------+
| Security          |                   | - Issue and verify IEEE 1609.2 (ETSI TS 103 097)         |
|                   |                   |   certificates.                                          |
|                   |                   | - Sign and verify ETSI C-ITS messages.                   |
+-------------------+-------------------+----------------------------------------------------------+
| Facilities        | CA Basic Service  | Processing and dissemination of Cooperative Awareness    |
|                   |                   | Messages (CAMs)                                          |
+                   +-------------------+----------------------------------------------------------+
|                   | VRU Awareness     | Processing and dissemination of VRU Awareness Messages   |
|                   |                   | (VAMs)                                                   |
+                   +-------------------+----------------------------------------------------------+
|                   | DEN Service       | Processing and dissemination of DEN Messages (DENMs)     |
+                   +-------------------+----------------------------------------------------------+
|                   | Local Dynamic Map | C-ITS messages data handling.                            |
+-------------------+-------------------+----------------------------------------------------------+
| Applications      | RHS Application   | Simple Emergency Vehicle Approaching application         |
|                   |                   | notification as an example for developers.               |
+-------------------+-------------------+----------------------------------------------------------+
| Utils             | Location Service  | - Location service that gets GPSD positions and feeds    |
|                   |                   |   them to the protocol stack                             |
|                   |                   | - Static Location service that serves a pre-configured   |
|                   |                   |   location.                                              |
+-------------------+-------------------+----------------------------------------------------------+


Architecture
------------

.. mermaid::

    flowchart TB
    %% Application Layer
    subgraph APP["Application Layer"]
        EX["Application"]
    end

    %% Facilities Layer
    subgraph FL["Facilities Layer"]
        LDM[("Local Dynamic Map (LDM)")]
        subgraph T[" "]
            CA["CA Basic Service"]
            VRUAW["VRU Awareness Service"]
            DEN["DEN Service"]
        end
    end

    %% Transport Layer
    subgraph TL["Transport Layer"]
        BTP["Basic Transport Protocol (BTP) Router"]
    end

    %% Network Layer
    subgraph NL["Network Layer"]
        GN["Geonetworking Router"]
    end

    %% Link Layer
    subgraph LL["Link Layer"]
        direction LR
        RWLL["RawLinkLayer"]
        CV2XLL["PythonCV2XLinkLayer"]
        RWLL ~~~|"Or"| CV2XLL
    end

    %% Connections
    EX <-->|"App-Fac SAP"| LDM
    LDM <--> VRUAW
    LDM <--> CA
    LDM <--> DEN
    VRUAW <-->|"Facilities-BTP SAP"| BTP
    CA <-->|"Facilities-BTP SAP"| BTP
    DEN <-->|"Facilities-BTP SAP"| BTP
    BTP <-->|"BTP-GN SAP"| GN
    GN <--> LL

    %% Styling
    style APP fill:#e3f2fd,stroke:#42a5f5,stroke-width:2px
    style FL fill:#e8f5e9,stroke:#66bb6a,stroke-width:2px
    style T fill:transparent,stroke:transparent
    style TL fill:#fff3e0,stroke:#ffa726,stroke-width:2px
    style NL fill:#f3e5f5,stroke:#ab47bc,stroke-width:2px
    style LL fill:#eeeeee,stroke:#bdbdbd,stroke-width:2px
    style LDM fill:#c8e6c9,stroke:#388e3c
    style VRUAW fill:#fff3e0,stroke:#f57c00
    style CA fill:#fffde7,stroke:#fbc02d
    style DEN fill:#ffebee,stroke:#e53935


Sequence Diagram
----------------

Setup
~~~~~

To set-up a basic V2X communication scenario using the FlexStack(R) library, the following
sequence of interactions between the different modules takes place:

.. mermaid::

   sequenceDiagram
       autonumber
       participant LS as Location Service
       participant FLC as Facility Layer Component
       participant BTP as BTP
       participant GN as GeoNet
       participant LL as Link Layer

       LL ->> GN: Register GN Data Indicate Callback
       GN ->> LL: Register Link Layer
       GN ->> BTP: Register BTP Indication Callback
       LS ->> GN: Add GN Refresh Ego Position Vector Callback
       LS ->> FLC: Add Facility Layer Callback

A sample code snippet illustrating the setup process is provided below. 

.. note::

   Please note that this is a simplified example for illustration purposes only. Refer to each module's sections to get detailed information on their setup and configuration.

.. code-block:: python

    gn_addr = GNAddress(m=M.GN_MULTICAST, st=ST.PASSENGER_CAR, mid=MID(mac_address))
    mib = MIB(itsGnLocalGnAddr=gn_addr)
    gn_router = Router(mib=mib, sign_service=None)

    ll = RawLinkLayer(
        iface="lo",
        mac_address=mac_address,
        receive_callback=gn_router.gn_data_indicate,
    )  # 1. Create and register GN data indicate callback

    gn_router.link_layer = ll  # 2. Register link layer

    btp_router = BTPRouter()
    gn_router.register_indication_callback(
        btp_router.btp_data_indication,
    )  # 3. Register BTP indication callback

    location_service = LocationService()
    location_service.add_callback(
        gn_router.refresh_ego_position_vector,
    )  # 4. Add GN refresh ego position vector callback

    vehicle_data = VehicleData(station_id=station_id)
    ca_basic_service = CooperativeAwarenessBasicService(btp_router=btp_router, vehicle_data=vehicle_data)
    location_service.add_callback(
        ca_basic_service.cam_transmission_management
        .location_update_callback,
    )  # 5. Add facility layer callback


The code snippet above demonstrates how to set up the interactions between the Location Service, GeoNetworking, BTP, and Facility Layer components in the FlexStack(R) library.


Message Transmission
~~~~~~~~~~~~~~~~~~~~~

Message transmissions are generally trigger by a location update received from the Location Service (e.g., new GPS position). The following sequence diagram illustrates the steps involved in transmitting a message through the protocol stack:

.. mermaid::

   sequenceDiagram
       
       participant LS as Location Service
       participant FLC as Facility Layer Component
       participant BTP as BTP
       participant GN as GeoNet
       participant LL as Link Layer

       loop Periodic Position Update
           LS ->> FLC: New GPS Position Received
           FLC ->> FLC: Encode Facility-Layer Headers

           FLC ->> BTP: Create BTP Data Request
           BTP ->> BTP: Encode & Append BTP Headers

           BTP ->> GN: Create GN Data Request
           GN ->> GN: Encode & Append GN Headers

           GN ->> LL: Send Message to Link Layer
       end

Message Reception
~~~~~~~~~~~~~~~~~

Message receptions are triggered by incoming messages at the Link Layer. The following sequence diagram illustrates the steps involved in receiving a message through the protocol stack:

.. mermaid::

   sequenceDiagram
       
       participant LS as Location Service
       participant FLC as Facility Layer Component
       participant BTP as BTP
       participant GN as GeoNet
       participant LL as Link Layer

       loop Link Layer Incoming Message
        LL ->> LL: Waiting for Incoming Messages
        LL ->> GN: Create GN Data Indicate
        GN ->> GN: Decode & Remove GN Headers

        GN ->> BTP: Create BTP Data Indicate
        BTP ->> BTP: Decode & Remove BTP Headers

        BTP ->> FLC: Call Facility-Layer Reception Callback
        FLC ->> FLC: Decode Message and Store to LDM
       end