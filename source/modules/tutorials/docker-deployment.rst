Docker Deployment
=================

The easist way to deploy the Flexstack is through a Dockerfile.

With the following Dockerfile you can directly deploy the Flexstack;

.. code:: py

   FROM python:3.9-slim

   WORKDIR /app

   COPY app.py .

   RUN apt-get update && apt-get install -y \
       gcc \
       python3-dev \
       build-essential \
       && rm -rf /var/lib/apt/lists/*

   RUN pip install --no-cache-dir v2xflexstack

   CMD ["python", "app.py"]

The only requirement would be to have the ``app.py`` Python script.
Which can be the following;

.. code:: py

   import argparse

   import logging
   import logging.config

   from flexstack.facilities.vru_awareness_service.vru_awareness_service import VRUAwarenessService
   from flexstack.facilities.vru_awareness_service.vam_transmission_management import DeviceDataProvider
   from flexstack.utils.static_location_service import ThreadStaticLocationService as LocationService

   from flexstack.btp.router import Router as BTPRouter

   from flexstack.geonet.router import Router
   from flexstack.geonet.mib import MIB
   from flexstack.geonet.gn_address import GNAddress, M, ST, MID

   from flexstack.linklayer.raw_link_layer import RawLinkLayer

   def parse_mac_address_to_int(mac_address: str):
       mac_address = mac_address.split(":")
       mac_address = [int(x, 16) for x in mac_address]
       return bytes(mac_address)

   parser = argparse.ArgumentParser(description="Run a C-ITS station.")
   parser.add_argument(
       "--station-id",
       type=int,
       default="1",
       help="Station ID for C-ITS Station",
   )
   parser.add_argument(
       "--mac-address",
       type=str,
       default="aa:bb:cc:11:22:33",
       help='The MAC address to send CAMs to (e.g. "aa:bb:cc:dd:ee:ff")',
   )
   args = parser.parse_args()


   logging.basicConfig(level=logging.INFO)

   # Geonet
   mac_address = parse_mac_address_to_int(args.mac_address)
   mib = MIB()
   gn_addr = GNAddress()
   gn_addr.set_m(M.GN_MULTICAST)
   gn_addr.set_st(ST.CYCLIST)
   gn_addr.set_mid(MID(mac_address))
   mib.itsGnLocalGnAddr = gn_addr
   gn_router = Router(mib=mib, sign_service=None)

   # Link-Layer
   ll = RawLinkLayer(iface="eth0", mac_address=mac_address,
                     receive_callback=gn_router.gn_data_indicate)
   gn_router.link_layer = ll

   # BTP
   btp_router = BTPRouter(gn_router)
   gn_router.register_indication_callback(btp_router.btp_data_indication)


   # Facility - Location Service
   location_service = LocationService()

   location_service.add_callback(gn_router.refresh_ego_position_vector)

   # Facility - Device Data Provider
   device_data_provider = DeviceDataProvider()
   device_data_provider.station_id = args.station_id
   device_data_provider.station_type = 2  # Cyclist

   # Facility - VRU Awareness Service
   vru_awareness_service = VRUAwarenessService(btp_router=btp_router,
                                               device_data_provider=device_data_provider)

   location_service.add_callback(vru_awareness_service.vam_transmission_management.location_service_callback)

   location_service.location_service_thread.join()

Once the Dockerfile and app.py files are created, inside the same
directory;

::

   project/
   ├── app.py
   ├── Dockerfile
   └── docker-compose.yml

Run the following commands;

.. code:: bash

   docker build -t flexstack .

Then;

.. code:: bash

   docker run flexstack

This will create one C-ITS station, with one Flexstack, so messages will
only be sent. To send and recieve messages we can create a
docker-compose file;

.. code:: yaml

   version: '3.8'

   services:
     flexstack1:
       build: .
       container_name: v2xflex_app
       volumes:
         - .:/app
       working_dir: /app
       command: ["--station-id", "1", "--mac-address", "aa:bb:cc:11:22:31"]
       networks:
         - v2xnet
     flexstack2:
       build: .
       container_name: v2xflex_app_2
       volumes:
         - .:/app
       working_dir: /app
       command: ["--station-id", "2", "--mac-address", "aa:bb:cc:11:22:32"]
       networks:
         - v2xnet
   networks:
     v2xnet:

With this we will be able to create two C-ITS instances that send and
recieve messages. Through a Docker-Compose network.
