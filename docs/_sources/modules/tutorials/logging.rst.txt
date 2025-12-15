.. _logging:

Logging
=======

FlexStack includes comprehensive logging throughout its components, helping you **debug issues**, 
**monitor behavior**, and **understand message flow** in your V2X applications.

.. note::

   Logging uses Python's built-in ``logging`` module. You can configure it from simple 
   one-liners to detailed configuration files.

Log Levels
----------

FlexStack components emit logs at different severity levels:

.. list-table::
   :header-rows: 1
   :widths: 15 20 65

   * - Level
     - Constant
     - When to Use
   * - 🐛 **DEBUG**
     - ``logging.DEBUG``
     - Detailed diagnostic information (packet contents, state changes)
   * - ℹ️ **INFO**
     - ``logging.INFO``
     - General operational messages (service started, message sent)
   * - ⚠️ **WARNING**
     - ``logging.WARNING``
     - Something unexpected but recoverable happened
   * - ❌ **ERROR**
     - ``logging.ERROR``
     - A serious problem occurred
   * - 💀 **CRITICAL**
     - ``logging.CRITICAL``
     - System is unusable

----

Quick Start
-----------

One-Line Setup
~~~~~~~~~~~~~~

The simplest way to enable logging:

.. code-block:: python

   import logging

   # Show INFO and above (INFO, WARNING, ERROR, CRITICAL)
   logging.basicConfig(level=logging.INFO)

   # Show DEBUG and above (everything)
   logging.basicConfig(level=logging.DEBUG)

That's it! You'll now see logs from all FlexStack components.

**Example output:**

.. code-block:: text

   INFO:ca_basic_service:CAM sent - Station 12345, Generation time: 5000
   INFO:btp:BTP packet sent to port 2001
   DEBUG:geonetworking:GeoNetworking SHB packet created

Better Formatting
~~~~~~~~~~~~~~~~~

Add timestamps and more context:

.. code-block:: python

   import logging

   logging.basicConfig(
       level=logging.INFO,
       format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
       datefmt="%H:%M:%S",
   )

**Example output:**

.. code-block:: text

   14:32:15 [INFO] ca_basic_service: CAM sent - Station 12345
   14:32:15 [INFO] btp: BTP packet sent to port 2001
   14:32:16 [DEBUG] link_layer: Packet received (128 bytes)

----

Component Loggers
-----------------

Each FlexStack component has its own named logger:

.. mermaid::

   flowchart TB
       ROOT[Root Logger<br/>logging.root]
       
       ROOT --> FAC[Facilities]
       ROOT --> BTP[btp]
       ROOT --> GN[geonetworking]
       ROOT --> LL[link_layer]
       ROOT --> SEC[security]
       
       FAC --> CAM[ca_basic_service]
       FAC --> DEN[den_service]
       FAC --> VRU[vru_basic_service]
       FAC --> CP[cp_service]
       FAC --> LDM[local_dynamic_map]
       
       style ROOT fill:#e3f2fd,stroke:#1565c0

**Logger Names:**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Logger Name
     - Component
   * - ``ca_basic_service``
     - CA Basic Service (CAMs)
   * - ``vru_basic_service``
     - VRU Awareness Service (VAMs)
   * - ``den_service``
     - DEN Service (DENMs)
   * - ``cp_service``
     - CP Service (CPMs)
   * - ``local_dynamic_map``
     - Local Dynamic Map
   * - ``btp``
     - BTP Router
   * - ``geonetworking``
     - GeoNetworking Router
   * - ``link_layer``
     - Link Layer (RawLinkLayer, etc.)
   * - ``security``
     - Security services

----

Filtering by Component
----------------------

Control logging for specific components:

.. code-block:: python

   import logging

   # Set default level
   logging.basicConfig(level=logging.WARNING)

   # Enable DEBUG only for CA Basic Service
   logging.getLogger("ca_basic_service").setLevel(logging.DEBUG)

   # Enable INFO for BTP
   logging.getLogger("btp").setLevel(logging.INFO)

   # Silence link_layer completely
   logging.getLogger("link_layer").setLevel(logging.CRITICAL)

This lets you focus on the components you're debugging without noise from others.

----

Logging to File
---------------

Save logs to a file for later analysis:

.. code-block:: python

   import logging

   logging.basicConfig(
       level=logging.DEBUG,
       format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
       handlers=[
           logging.FileHandler("flexstack.log"),  # Write to file
           logging.StreamHandler(),                # Also print to console
       ],
   )

**Multiple files by component:**

.. code-block:: python

   import logging

   # Main logger
   logging.basicConfig(level=logging.INFO)

   # Separate file for CAM logs
   cam_handler = logging.FileHandler("cam_messages.log")
   cam_handler.setLevel(logging.DEBUG)
   logging.getLogger("ca_basic_service").addHandler(cam_handler)

   # Separate file for errors only
   error_handler = logging.FileHandler("errors.log")
   error_handler.setLevel(logging.ERROR)
   logging.getLogger().addHandler(error_handler)

----

Configuration File
------------------

For complex setups, use a configuration file:

Create ``logging.ini``:

.. code-block:: ini
   :linenos:

   [loggers]
   keys=root,ca_basic_service,vru_basic_service,btp,link_layer,local_dynamic_map

   [handlers]
   keys=consoleHandler,fileHandler

   [formatters]
   keys=detailed,simple

   # ======================== Loggers ======================== #

   [logger_root]
   level=INFO
   handlers=consoleHandler

   [logger_ca_basic_service]
   level=DEBUG
   handlers=fileHandler
   qualname=ca_basic_service
   propagate=1

   [logger_vru_basic_service]
   level=DEBUG
   handlers=
   qualname=vru_basic_service
   propagate=1

   [logger_btp]
   level=INFO
   handlers=
   qualname=btp
   propagate=1

   [logger_link_layer]
   level=WARNING
   handlers=
   qualname=link_layer
   propagate=1

   [logger_local_dynamic_map]
   level=DEBUG
   handlers=
   qualname=local_dynamic_map
   propagate=1

   # ======================== Handlers ======================== #

   [handler_consoleHandler]
   class=StreamHandler
   level=DEBUG
   formatter=simple
   args=(sys.stdout,)

   [handler_fileHandler]
   class=FileHandler
   level=DEBUG
   formatter=detailed
   args=('flexstack.log', 'w')

   # ======================== Formatters ======================== #

   [formatter_detailed]
   format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
   datefmt=%Y-%m-%d %H:%M:%S

   [formatter_simple]
   format=[%(levelname)s] %(name)s: %(message)s

Load the configuration:

.. code-block:: python

   import logging
   import logging.config

   logging.config.fileConfig("logging.ini", disable_existing_loggers=False)

   # Now run your FlexStack application...

----

Common Patterns
---------------

Debug a Specific Issue
~~~~~~~~~~~~~~~~~~~~~~

When debugging CAM generation:

.. code-block:: python

   import logging

   # Quiet everything except what we care about
   logging.basicConfig(level=logging.WARNING)
   
   # Full debug for CAM service
   logging.getLogger("ca_basic_service").setLevel(logging.DEBUG)
   
   # Also see BTP to confirm packets are sent
   logging.getLogger("btp").setLevel(logging.DEBUG)

Production Logging
~~~~~~~~~~~~~~~~~~

For production deployments:

.. code-block:: python

   import logging
   from logging.handlers import RotatingFileHandler

   # Rotate logs when they reach 10MB, keep 5 backups
   handler = RotatingFileHandler(
       "flexstack.log",
       maxBytes=10*1024*1024,  # 10 MB
       backupCount=5,
   )
   handler.setFormatter(logging.Formatter(
       "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
   ))

   logging.basicConfig(
       level=logging.INFO,
       handlers=[handler],
   )

JSON Logging
~~~~~~~~~~~~

For log aggregation systems (ELK, Splunk):

.. code-block:: python

   import logging
   import json
   from datetime import datetime

   class JSONFormatter(logging.Formatter):
       def format(self, record):
           return json.dumps({
               "timestamp": datetime.utcnow().isoformat(),
               "level": record.levelname,
               "logger": record.name,
               "message": record.getMessage(),
           })

   handler = logging.StreamHandler()
   handler.setFormatter(JSONFormatter())
   logging.basicConfig(level=logging.INFO, handlers=[handler])

----

Complete Example
----------------

.. code-block:: python
   :linenos:

   #!/usr/bin/env python3
   """
   FlexStack with Custom Logging
   """

   import logging
   import random
   import time

   # ============ Configure Logging ============ #
   
   # Create formatters
   detailed_fmt = logging.Formatter(
       "%(asctime)s [%(levelname)-8s] %(name)-20s: %(message)s",
       datefmt="%H:%M:%S",
   )

   # Console handler (INFO and above)
   console = logging.StreamHandler()
   console.setLevel(logging.INFO)
   console.setFormatter(detailed_fmt)

   # File handler (DEBUG and above)
   file_handler = logging.FileHandler("debug.log", mode="w")
   file_handler.setLevel(logging.DEBUG)
   file_handler.setFormatter(detailed_fmt)

   # Configure root logger
   logging.basicConfig(level=logging.DEBUG, handlers=[console, file_handler])

   # Fine-tune specific loggers
   logging.getLogger("link_layer").setLevel(logging.WARNING)  # Less noise

   # ============ FlexStack Setup ============ #

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

   logger = logging.getLogger(__name__)

   POSITION = [41.386931, 2.112104]
   MAC_ADDRESS = bytes([(random.randint(0, 255) & 0xFE) | 0x02] + 
                       [random.randint(0, 255) for _ in range(5)])
   STATION_ID = random.randint(1, 2147483647)


   def main():
       logger.info("Starting FlexStack application...")

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

       # CA Basic Service
       vehicle_data = VehicleData(
           station_id=STATION_ID,
           station_type=5,
           drive_direction="forward",
           vehicle_length={"vehicleLengthValue": 40, "vehicleLengthConfidenceIndication": "unavailable"},
           vehicle_width=20,
       )
       ca_service = CooperativeAwarenessBasicService(
           btp_router=btp_router,
           vehicle_data=vehicle_data,
       )
       location_service.add_callback(
           ca_service.cam_transmission_management.location_service_callback
       )

       # Link Layer
       btp_router.freeze_callbacks()
       link_layer = RawLinkLayer(
           "lo",
           MAC_ADDRESS,
           receive_callback=gn_router.gn_data_indicate,
       )
       gn_router.link_layer = link_layer

       logger.info(f"✅ Station {STATION_ID} started")
       logger.info("📡 Broadcasting CAMs...")
       logger.debug(f"MAC Address: {MAC_ADDRESS.hex(':')}")

       try:
           while True:
               time.sleep(1)
       except KeyboardInterrupt:
           logger.info("Shutting down...")

       location_service.stop_event.set()
       location_service.location_service_thread.join()
       link_layer.sock.close()
       logger.info("Goodbye!")


   if __name__ == "__main__":
       main()

----

See Also
--------

- `Python Logging Documentation <https://docs.python.org/3/library/logging.html>`__ — Official Python logging guide
- :doc:`/getting_started` — Complete V2X tutorial
- :doc:`docker-deployment` — Logging in Docker containers
