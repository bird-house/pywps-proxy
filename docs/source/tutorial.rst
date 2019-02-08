.. _tutorial:

********
Tutorial
********

.. contents::
    :local:
    :depth: 2

Using the OWSProxy with an external WPS application
===================================================


The ``OWSProxy`` is a proxy service for OWS services. Currently it only supports WPS.

First you need an external WPS. You can use `Emu WPS service <http://emu.readthedocs.io/en/latest/>`_ from Birdhouse.
Get it from GitHub and run the installation:

.. code-block:: sh

    $ git clone https://github.com/bird-house/emu.git
    $ cd emu
    $ make install
    $ make start

The Emu WPS service is available by default at the URL:
http://localhost:5000/wps?service=WPS&version=1.0.0&request=GetCapabilities


Make sure Twitcher is installed and running:

.. code-block:: sh

   $ cd ../twitcher  # cd into the twitcher installation folder
   $ make restart
   $ make status

Register a WPS service
----------------------

Register the Emu WPS service at the Twitcher ``OWSProxy``:

.. code-block:: sh

   $ bin/twitcherctl -k register --name emu http://localhost:5000/wps

If you don't provide a name with ``--name`` option then a nice name will be generated, for example ``sleepy_flamingo``.

Use the ``list`` command to see which WPS services are registered with OWSProxy:

.. code-block:: sh

   $ bin/twitcherctl -k list
   [{'url': 'http://localhost:5000/wps', 'proxy_url': 'https://localhost:8000/ows/proxy/emu', 'type': 'wps', 'name': 'emu'}]


Access a registered service
---------------------------

By default the registered service is available at the URL ``https://localhost:8000/ows/proxy/{service_name}``.
Replace the ``service_name`` with the registered name.

Run a ``GetCapabilities`` request for the registered Emu WPS service:

.. code-block:: sh

    $ curl -k "https://localhost:8000/ows/proxy/emu?service=wps&request=getcapabilities"


Run a ``DescribeProcess`` request:

.. code-block:: sh

    $ curl -k "https://localhost:8000/ows/proxy/emu?service=wps&request=describeprocess&identifier=hello&version=1.0.0"

Use tokens to run an execute request
------------------------------------

By default the WPS service is protected by the ``OWSSecurity`` wsgi middleware. You need to provide an access token to run an execute request.

Run an ``Exceute`` request:

.. code-block:: sh

    $ curl -k "https://localhost:8000/ows/proxy/emu?service=wps&request=execute&identifier=hello&version=1.0.0&datainputs=name=tux"

Now you should get an XML error response with a message that you need to provide an access token (see section above).

We need to generate an access token with ``twitcherctl``:

.. code-block:: sh

    $ bin/twitcherctl -k gentoken -H 24
    def456

By default the token has a limited life time of one hour. With the option ``-H`` you can extend the life time in hours (24 hours in this example).

You can provide the access token in three ways (see section above):

* as HTTP parameter,
* as part of the HTTP header
* or as part of the url path.

In the following example we provide the token as HTTP parameter:

.. code-block:: sh

    $ curl -k "https://localhost:8000/ows/proxy/emu?service=wps&request=execute&identifier=hello&version=1.0.0&datainputs=name=tux&token=def456"

.. warning::

   If you have set enviroment variables with your access token then they will *not* be available in the external service.


Use x509 certificates to control client access
==================================================

Since version 0.3.6 Twitcher is prepared to use x509 certificates for control client access.
By default it is configured to accept x509 proxy certificates from `ESGF`_.

Register the Emu WPS service at the Twitcher ``OWSProxy`` with ``auth`` option ``cert``:

.. code-block:: sh

   $ bin/twitcherctl -k register --name emu --auth cert http://localhost:5000/wps

The ``GetCapabilities``  and ``DescribeProcess`` requests are not blocked:

.. code-block:: sh

  $ curl -k "https://localhost:8000/ows/proxy/emu?service=wps&request=getcapabilities"
  $ curl -k "https://localhost:8000/ows/proxy/emu?service=wps&request=describeprocess&identifier=hello&version=1.0.0"

When you run an ``Exceute`` request without a certificate you should get an exception report:

.. code-block:: sh

  $ curl -k "https://localhost:8000/ows/proxy/emu?service=wps&request=execute&identifier=hello&version=1.0.0&datainputs=name=tux"

Now you should get an XML error response with a message that you need to provide a valid X509 certificate.

Get a valid proxy certificate from ESGF, you may use the `esgf-pyclient`_ to run a myproxy logon.
Let's say your proxy certificate is ``cert.pem``, then run the exceute request again using this certificate:

.. code-block:: sh

  $ curl --cert cert.pem --key cert.pem -k "https://localhost:8000/ows/proxy/emu?service=wps&request=execute&identifier=hello&version=1.0.0&datainputs=name=tux"


Use Birdy WPS command line client to run a Process
==================================================


Install the `birdy <http://birdy.readthedocs.io/en/latest/>`_ WPS command line client:

.. code-block:: sh

   $ conda install -c birdhouse birdhouse-birdy

If ``conda`` is not in your path ... it was installed by the twitcher installer and is by default in ``~/anaconda/bin``.

Generate a new access token:

.. code-block:: sh

   $ cd twitcher # cd into twitcher installation folder
   $ bin/twitcherctl -k gentoken
   98765

Check which WPS is registered (or register one as described above):

.. code-block:: sh

   $ bin/twitcherctl -k list
   [{'url': 'http://localhost:5000/wps', 'proxy_url': 'https://localhost:8000/ows/proxy/emu', 'type': 'wps', 'name': 'emu'}]


Set the ``WPS_SERVICE`` environment variable for birdy with the ``proxy_url`` and extended with **access token**:

.. code-block:: sh

   $ export WPS_SERVICE=https://localhost:8000/ows/proxy/emu/98765


Now, run birdy:

.. code-block:: sh

   $ birdy -h

You get a list of available WPS processes::

    usage: brdy [<options>] <command> [<args>]

    Emu: WPS processes for testing and demos.

    optional arguments:
      -h, --help            show this help message and exit
      --debug               enable debug mode

    command:
      List of available commands (wps processes)

      {helloworld,ultimatequestionprocess,dummyprocess,wordcount,inout,multiplesources,chomsky,zonal_mean}
                            Run "birdy <command> -h" to get additional help.
        helloworld          Hello World: Welcome user and say hello ...
        ultimatequestionprocess
                            Answer to Life, the Universe and Everything: Numerical
                            solution that is the answer to Life, Universe and
                            Everything. The process is an improvement to Deep
                            Tought computer (therefore version 2.0) since it no
                            longer takes 7.5 milion years, but only a few seconds
                            to give a response, with an update of status every 10
                            seconds.
        dummyprocess        Dummy Process: The Dummy process is used for testing
                            the WPS structure. The process will accept 2 input
                            numbers and will return the XML result with an add one
                            and subtract one operation
        wordcount           Word Counter: Counts words in a given text ...
        inout               Testing all Data Types: Just testing data types like
                            date, datetime etc ...
        multiplesources     Multiple Sources: Process with multiple different
                            sources ...
        chomsky             Chomsky text generator: Generates a random chomsky
                            text ...


Show params of ``helloworld process``:

.. code-block:: sh

   $ birdy helloworld -h


You get a list of input/output params as option::

    usage: birdy helloworld [-h] --user [USER]
                            [--output [{output} [{output} ...]]]

    optional arguments:
      -h, --help            show this help message and exit
      --user [USER]         Your name: Please enter your name
      --output [{output} [{output} ...]]
                            Output: output=Welcome message: None (default: all
                            outputs)


Run the ``helloworld`` process:

.. code-block:: sh

   $ birdy helloworld --user pingu

The process output::

    INFO:Execution status: ProcessAccepted
    INFO:Execution status: ProcessSucceeded
    INFO:Output:
    INFO:output=Hello pingu and welcome to WPS :)


If you don't provide a token or the token is invalid then you will get an error message::

   owslib.wps.WPSException : {'locator': 'AccessForbidden', 'code': 'NoApplicableCode', 'text': 'Access token is required to access this service.'}
   WARNING:Error: code=NoApplicableCode, locator=AccessForbidden, text=Access token is required to access this service.


.. _ESGF: https://esgf.llnl.gov/
.. _esgf-pyclient: https://github.com/ESGF/esgf-pyclient
