Sending and Recieving V2X Messages Through Ethernet
====================

To use the Flexstack with the `RawLinkLayer <link-layer.md>`__ a
networking interface must be used. In this section common issues will be
shown.

.. important::
   The RawLinkLayer only works with Linux-based Operating Systems (e.g., Ubuntu).

To run the Flexstack with `RawLinkLayer <link-layer.md>`__ a networking
interface must be chosen. To choose it the following steps can be
followed; 

1. Run ``route``. This will show the routing table of your device. In the first line of the table the **default** route is shown, and in the **Iface** column the networking interface used is shown. Here the active, and used networking interfaces can be seen. 
2. Choose your preferred networking interface. For testing purposes ethernet (eth) interfaces can be used.

Once a networking interface is chosen introuduce it to the
`RawLinkLayer <link-layer.md>`__ as seen in the script below (eth0
used);

.. code:: py

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
   device_data_provider.station_id = 1
   device_data_provider.station_type = 2  # Cyclist

   # Facility - VRU Awareness Service
   vru_awareness_service = VRUAwarenessService(btp_router=btp_router,
                                               device_data_provider=device_data_provider)

   location_service.add_callback(vru_awareness_service.vam_transmission_management.location_service_callback)

   # Applications would be declared here


   location_service.location_service_thread.join()

Then to run this script try running it with python .py. This will
probably raise one of the following errors;

.. code:: py

   PermissionError: [Errno 1] Operation not permitted

Or;

.. code:: py

   AttributeError: 'RawLinkLayer' object has no attribute 'sock'

To fix this use ``sudo``. Two options are possible; 

1. Enter the command ``sudo su`` to become root.

   .. code:: py

      sudo su
      source <name_of_virtual_environment>/bin/activate
      python <name_of_script>.py

2. Run the script with ``sudo`` directly.

   .. code:: py

      sudo env PATH=$PATH python <name_of_script>.py 

This should work and logging messages showing the components internal
logs should start appearing.
