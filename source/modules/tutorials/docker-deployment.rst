.. _docker_deployment:

Docker Deployment
=================

Deploy FlexStack V2X applications in isolated, reproducible containers using **Docker**. 
This guide shows you how to containerize your C-ITS stations and run multiple instances 
that communicate with each other.

.. note::

   Docker is the easiest way to deploy FlexStack — no system dependencies to manage, 
   consistent environments across machines, and easy scaling.

Why Use Docker?
---------------

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Benefit
     - Description
   * - 📦 **Isolation**
     - Each C-ITS station runs in its own container
   * - 🔄 **Reproducibility**
     - Same environment on development and production
   * - 📈 **Scalability**
     - Easily spawn multiple stations with Docker Compose
   * - 🌐 **Networking**
     - Built-in virtual networks for V2X communication
   * - 🚀 **Easy Deployment**
     - Single command to start your entire V2X system

----

Architecture
------------

.. mermaid::

   flowchart TB
       subgraph "Docker Host"
           subgraph "Container 1"
               FS1[FlexStack<br/>Station 1]
           end
           
           subgraph "Container 2"
               FS2[FlexStack<br/>Station 2]
           end
           
           subgraph "Container 3"
               FS3[FlexStack<br/>Station 3]
           end
           
           NET[Docker Network<br/>v2xnet]
       end
       
       FS1 <-->|"VAM/CAM"| NET
       FS2 <-->|"VAM/CAM"| NET
       FS3 <-->|"VAM/CAM"| NET
       
       style NET fill:#e3f2fd,stroke:#1565c0

----

Quick Start
-----------

Step 1: Create Project Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a directory with the following files:

.. code-block:: text

   my-v2x-project/
   ├── app.py              # Your FlexStack application
   ├── Dockerfile          # Container definition
   └── docker-compose.yml  # Multi-container setup

Step 2: Create the Dockerfile
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: dockerfile
   :linenos:

   FROM python:3.9-slim

   WORKDIR /app

   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       gcc \
       python3-dev \
       build-essential \
       && rm -rf /var/lib/apt/lists/*

   # Install FlexStack
   RUN pip install --no-cache-dir v2xflexstack

   # Copy application
   COPY app.py .

   # Run the application
   CMD ["python", "app.py"]

**What this does:**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Line
     - Description
   * - ``FROM python:3.9-slim``
     - Use lightweight Python 3.9 base image
   * - ``apt-get install``
     - Install C compiler for native extensions
   * - ``pip install v2xflexstack``
     - Install FlexStack package
   * - ``CMD ["python", "app.py"]``
     - Run your application on container start

Step 3: Create the Application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create ``app.py`` — a VRU station that broadcasts VAMs:

.. code-block:: python
   :linenos:

   #!/usr/bin/env python3
   """
   FlexStack Docker Application
   
   A C-ITS VRU station that sends and receives VAMs.
   """

   import argparse
   import logging

   from flexstack.facilities.vru_awareness_service.vru_awareness_service import (
       VRUAwarenessService,
   )
   from flexstack.facilities.vru_awareness_service.vam_transmission_management import (
       DeviceDataProvider,
   )
   from flexstack.utils.static_location_service import (
       ThreadStaticLocationService as LocationService,
   )
   from flexstack.btp.router import Router as BTPRouter
   from flexstack.geonet.router import Router as GNRouter
   from flexstack.geonet.mib import MIB
   from flexstack.geonet.gn_address import GNAddress, M, ST, MID
   from flexstack.linklayer.raw_link_layer import RawLinkLayer


   def parse_mac_address(mac_str: str) -> bytes:
       """Convert MAC address string to bytes."""
       parts = mac_str.split(":")
       return bytes(int(x, 16) for x in parts)


   def main():
       # Parse command line arguments
       parser = argparse.ArgumentParser(description="FlexStack C-ITS Station")
       parser.add_argument(
           "--station-id",
           type=int,
           default=1,
           help="Unique station identifier",
       )
       parser.add_argument(
           "--mac-address",
           type=str,
           default="aa:bb:cc:11:22:33",
           help="MAC address (e.g., aa:bb:cc:dd:ee:ff)",
       )
       parser.add_argument(
           "--interface",
           type=str,
           default="eth0",
           help="Network interface to use",
       )
       args = parser.parse_args()

       logging.basicConfig(
           level=logging.INFO,
           format="[%(levelname)s] Station %(station_id)s: %(message)s",
           defaults={"station_id": args.station_id},
       )
       logger = logging.getLogger(__name__)

       mac_address = parse_mac_address(args.mac_address)

       # GeoNetworking
       mib = MIB(
           itsGnLocalGnAddr=GNAddress(
               m=M.GN_MULTICAST,
               st=ST.CYCLIST,
               mid=MID(mac_address),
           ),
       )
       gn_router = GNRouter(mib=mib, sign_service=None)

       # Link Layer
       link_layer = RawLinkLayer(
           iface=args.interface,
           mac_address=mac_address,
           receive_callback=gn_router.gn_data_indicate,
       )
       gn_router.link_layer = link_layer

       # BTP
       btp_router = BTPRouter(gn_router)
       gn_router.register_indication_callback(btp_router.btp_data_indication)

       # Location Service
       location_service = LocationService()
       location_service.add_callback(gn_router.refresh_ego_position_vector)

       # VRU Awareness Service
       device_data = DeviceDataProvider(
           station_id=args.station_id,
           station_type=2,  # Cyclist
       )
       vru_service = VRUAwarenessService(
           btp_router=btp_router,
           device_data_provider=device_data,
       )
       location_service.add_callback(
           vru_service.vam_transmission_management.location_service_callback
       )

       logger.info(f"�� Station {args.station_id} started on {args.interface}")
       logger.info(f"📡 MAC: {args.mac_address}")
       logger.info("Broadcasting VAMs...")

       # Keep running
       location_service.location_service_thread.join()


   if __name__ == "__main__":
       main()

----

Running a Single Container
--------------------------

Build and Run
~~~~~~~~~~~~~

Build the Docker image:

.. code-block:: bash

   docker build -t flexstack .

Run a single C-ITS station:

.. code-block:: bash

   docker run --network host --privileged flexstack

.. warning::

   The ``--network host`` and ``--privileged`` flags are required for raw socket 
   access to network interfaces. This allows FlexStack to send/receive Ethernet frames.

With Custom Arguments
~~~~~~~~~~~~~~~~~~~~~

Override the station ID and MAC address:

.. code-block:: bash

   docker run --network host --privileged flexstack \
       python app.py --station-id 42 --mac-address aa:bb:cc:dd:ee:ff

----

Running Multiple Stations
-------------------------

Use Docker Compose to run multiple C-ITS stations that communicate with each other.

Docker Compose Setup
~~~~~~~~~~~~~~~~~~~~

Create ``docker-compose.yml``:

.. code-block:: yaml
   :linenos:

   version: '3.8'

   services:
     # First C-ITS Station (Cyclist)
     station1:
       build: .
       container_name: flexstack_station_1
       command: ["python", "app.py", "--station-id", "1", "--mac-address", "aa:bb:cc:11:22:01"]
       networks:
         - v2xnet
       cap_add:
         - NET_ADMIN
         - NET_RAW

     # Second C-ITS Station (Cyclist)
     station2:
       build: .
       container_name: flexstack_station_2
       command: ["python", "app.py", "--station-id", "2", "--mac-address", "aa:bb:cc:11:22:02"]
       networks:
         - v2xnet
       cap_add:
         - NET_ADMIN
         - NET_RAW

     # Third C-ITS Station (Cyclist)
     station3:
       build: .
       container_name: flexstack_station_3
       command: ["python", "app.py", "--station-id", "3", "--mac-address", "aa:bb:cc:11:22:03"]
       networks:
         - v2xnet
       cap_add:
         - NET_ADMIN
         - NET_RAW

   networks:
     v2xnet:
       driver: bridge

**Key Configuration:**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Setting
     - Purpose
   * - ``networks: v2xnet``
     - All stations share the same virtual network
   * - ``cap_add: NET_ADMIN, NET_RAW``
     - Required capabilities for raw socket access
   * - ``command``
     - Override default command with station-specific args

Start All Stations
~~~~~~~~~~~~~~~~~~

Launch all stations:

.. code-block:: bash

   docker-compose up

Or run in background:

.. code-block:: bash

   docker-compose up -d

View logs:

.. code-block:: bash

   docker-compose logs -f

Stop all stations:

.. code-block:: bash

   docker-compose down

----

Communication Flow
------------------

When multiple stations run in Docker Compose, they communicate through the shared network:

.. mermaid::

   sequenceDiagram
       participant S1 as Station 1<br/>(Cyclist)
       participant NET as Docker Network<br/>(v2xnet)
       participant S2 as Station 2<br/>(Cyclist)
       participant S3 as Station 3<br/>(Cyclist)
       
       loop Every ~500ms
           S1->>NET: Broadcast VAM
           NET->>S2: Receive VAM
           NET->>S3: Receive VAM
           
           S2->>NET: Broadcast VAM
           NET->>S1: Receive VAM
           NET->>S3: Receive VAM
           
           S3->>NET: Broadcast VAM
           NET->>S1: Receive VAM
           NET->>S2: Receive VAM
       end

----

Scaling Stations
----------------

Easily scale to many stations:

.. code-block:: bash

   # Run 5 instances of the station service
   docker-compose up --scale station1=5

Or define a scalable service in ``docker-compose.yml``:

.. code-block:: yaml

   services:
     cyclist:
       build: .
       networks:
         - v2xnet
       cap_add:
         - NET_ADMIN
         - NET_RAW
       deploy:
         replicas: 10

----

Advanced Configuration
----------------------

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Use environment variables for configuration:

.. code-block:: yaml

   services:
     station:
       build: .
       environment:
         - STATION_ID=1
         - MAC_ADDRESS=aa:bb:cc:11:22:33
         - LOG_LEVEL=DEBUG

Then in your ``app.py``:

.. code-block:: python

   import os

   station_id = int(os.getenv("STATION_ID", "1"))
   mac_address = os.getenv("MAC_ADDRESS", "aa:bb:cc:11:22:33")
   log_level = os.getenv("LOG_LEVEL", "INFO")

Volume Mounting
~~~~~~~~~~~~~~~

Mount local files for development (changes reflect immediately):

.. code-block:: yaml

   services:
     station:
       build: .
       volumes:
         - ./app.py:/app/app.py
       networks:
         - v2xnet

Health Checks
~~~~~~~~~~~~~

Add health checks to monitor station status:

.. code-block:: yaml

   services:
     station:
       build: .
       healthcheck:
         test: ["CMD", "python", "-c", "import flexstack"]
         interval: 30s
         timeout: 10s
         retries: 3

----

Troubleshooting
---------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Issue
     - Solution
   * - **Permission denied**
     - Add ``--privileged`` flag or ``cap_add: NET_ADMIN, NET_RAW``
   * - **Interface not found**
     - Check interface name with ``ip link`` inside container
   * - **Stations not communicating**
     - Ensure all stations are on the same Docker network
   * - **Build fails**
     - Check that ``gcc`` and ``build-essential`` are installed

Debug Commands
~~~~~~~~~~~~~~

Enter a running container:

.. code-block:: bash

   docker exec -it flexstack_station_1 /bin/bash

Check network interfaces:

.. code-block:: bash

   docker exec flexstack_station_1 ip link

View container logs:

.. code-block:: bash

   docker logs -f flexstack_station_1

----

Complete Project
----------------

Here's the complete project structure with all files:

.. code-block:: text

   my-v2x-project/
   ├── app.py              # Application code (see Step 3)
   ├── Dockerfile          # Container definition (see Step 2)
   └── docker-compose.yml  # Multi-container setup

**Quick commands:**

.. code-block:: bash

   # Build
   docker-compose build

   # Start all stations
   docker-compose up -d

   # View logs
   docker-compose logs -f

   # Stop everything
   docker-compose down

----

See Also
--------

- :doc:`/getting_started` — Complete V2X tutorial
- :doc:`/modules/facilities/vru_awareness_service` — VRU Awareness Service details
- :doc:`/modules/facilities/ca_basic_service` — For vehicle CAM stations
- :doc:`/modules/link_layer` — Network interface configuration
