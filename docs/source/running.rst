.. _running:

****************
Running Twitcher
****************

.. contents::
    :local:
    :depth: 2


Running `twitcherctl`
=====================


The ``twitcherctl`` is a command line tool to control the twitcher service.
It uses the XML-RPC api of twitcher to generate access tokens and to register OWS services.

``twitcherctl`` is part of the twitcher installation.
When you have installed twitcher from GitHub then start ``twitcherctl`` with:

.. code-block:: console

   $ twitcherctl -h


`twitcherctl` Commands and Options
----------------------------------

``twitcherctl`` has the following command line options:

-h, --help

   Print usage message and exit

-s, --serverurl

   URL on which twitcher server is listening (default "https://localhost:38083/").

-u, --username

   Username to use for authentication with server

-p, --password

   Password to use for authentication with server

-k, --insecure

   Don't validate the server's certificate.

List of available commands:

gentoken
    Generates an access token.
revoke
    Removes given access token.
list
    Lists all registered OWS services used by OWS proxy.
clear
    Removes all OWS services from the registry.
register
   Adds OWS service to the registry to be used by the OWS proxy.
unregister
   Removes OWS service from the registry.


Generate an access token
------------------------

See the available options:

.. code-block:: console

   $ twitcherctl -k gentoken -h

Generate an access token valid for 24 hours (use ``-k`` to avoid validation of HTTPS server certificate):

.. code-block:: console

   $ twitcherctl -k gentoken -H 24


Register an OWS Service for the OWS Proxy
-----------------------------------------

See the available options:

.. code-block:: console

   twitcherctl -k register -h

Register a local WPS service:

.. code-block:: console

   $ twitcherctl -k register http://localhost:5000/wps
   tiny_buzzard

You can use the ``--name`` option to provide a name (used by the OWS proxy).
Otherwise a nice name will be generated.


Show Status of Twitcher
-----------------------

Currently the ``status`` command shows only the registered OWS services:

.. code-block:: console

   $ twitcherctl -k list
   [{'url': 'http://localhost:5000/wps', 'proxy_url': 'https://localhost:38083/ows/proxy/tiny_buzzard', 'type': 'wps', 'name': 'tiny_buzzard'}]


Use Twitcher components in your Pyramid Application
===================================================

Instead of running twitcher as a service you can also include twitcher components
(OWS Security Middleware, OWS Proxy) in a Pyramid application.

Include OWS Security Middleware
-------------------------------

Use the Pyramid ``include`` statement. See the ``twitcher/__init__py`` as an example. [..]


Include OWS Proxy
-----------------

Use the Pyramid ``include`` statement. See the ``twitcher/__init__py`` as an example. [..]
