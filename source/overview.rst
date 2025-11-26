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


