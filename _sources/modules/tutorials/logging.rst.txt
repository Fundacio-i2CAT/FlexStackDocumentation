Logging
=======

Logging is an ongoing effort in the Flexstack. Logs have been created
for most of the fundamental components, ranging two levels; Information
and Debug.

Logging Configuration
---------------------

Simple Configuration Logging
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The easiest way to configure Logging in the Flexstack is through the
Python logging library;

.. code:: py

   import logging

   logging.basicConfig(level=logging.INFO) #logging.DEBUG for Debug-level logs.

This will show logs for all the components, in a specific level.

File Configuration Logging
~~~~~~~~~~~~~~~~~~~~~~~~~~

Another way of configuring logging is through a .ini file. Detailed
information about Logging can be found in the `Logging Python
Library <https://docs.python.org/3/library/logging.html>`__.

A useful configuration .ini file would be;

.. code:: ini

   [loggers]
   keys=root

   [handlers]
   keys=consoleHandler

   [formatters]
   keys=sampleFormatter

   # ------------------------- Root Logger ------------------------- #
   # Add the handlers to the root logger if you want to log everything
   [logger_root]
   level=INFO
   handlers=consoleHandler

   # ------------------------- Applications Loggers ------------------------- #


   # ------------------------- Faclities Loggers ------------------------- #
   [logger_ca_basic_service]
   level=DEBUG
   propagate=1
   handlers=
   qualname=ca_basic_service

   [logger_vru_basic_service]
   level=DEBUG
   propagate=1
   handlers=
   qualname=vru_basic_service

   [logger_cp_service]
   level=DEBUG
   propagate=1
   handlers=
   qualname=cp_service

   [logger_local_dynamic_map]
   level=DEBUG
   propagate=1
   handlers=
   qualname=local_dynamic_map

   # ------------------------- BTP Loggers ------------------------- #
   [logger_btp]
   level=DEBUG
   propagate=1
   handlers=
   qualname=btp
   # ------------------------- GeoNetworking Loggers ------------------------- #

   # ------------------------- Link Layer Loggers ------------------------- #

   [logger_link_layer]
   level=DEBUG
   propagate=1
   handlers=
   qualname=link_layer

   # ------------------------- Security Loggers ------------------------- #

   # ------------------------- Utils Loggers ------------------------- #

   # ------------------------- Handlers ------------------------- #

   [handler_consoleHandler]
   class=StreamHandler
   level=DEBUG
   formatter=sampleFormatter
   args=(sys.stdout,)

   [handler_fileHandler]
   class=FileHandler
   level=DEBUG
   formatter=sampleFormatter
   args=('python.log', 'w')


   # ------------------------- Formatters ------------------------- #

   [formatter_sampleFormatter]
   format=%(asctime)s - %(name)s - %(levelname)s - %(message)s

To use this file configuration .ini file;

.. code:: py

   import logging
   import logging.config

   logging.config.fileConfig(fname="config.ini", disable_existing_loggers=False)
