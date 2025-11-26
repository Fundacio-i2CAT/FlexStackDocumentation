.. _btp:

Basic Transport Protocol (BTP)
==============================


Diagram
-------

.. image:: /_static/img/basic_transport_protocol.png
    :alt: Basic Transport Protocol

Usage
-----

Router Instantiation
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from flexstack.btp.router import Router as BTPRouter

.. code-block:: python

    btp_router = BTPRouter(gn_router)

Request Sending BTP Packet
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from flexstack.btp.router import BTPDataRequest

    request = BTPDataRequest()
    request.btp_type = CommonNH.BTP_B
    request.source_port = 0
    request.destination_port = 2001
    request.destinaion_port_info = 0
    request.gn_packet_transport_type = PacketTransportType()
    request.gn_destination_address = GNAddress()
    request.gn_area = Area()
    request.communication_profile = CommunicationProfile.UNSPECIFIED
    request.traffic_class = TrafficClass()
    request.data = b"payload_data"
    request.length = len(request.data)

    btp_router.btp_data_request(request)

Response Receiving BTP Packet
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from flexstack.btp.router import BTPDataIndication

    def btp_data_indication(btp_data_indication: BTPDataIndication) -> None:
        print(f"Received BTP data indication: {btp_data_indication.data}")

    btp_router.register_indication_callback_btp(port=2001, callback=btp_data_indication)


Example
-------

Here is an example of a basic script that sends and receives BTP packets with a basic Ethernet Layer 2 Linux Interface:


