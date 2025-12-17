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
