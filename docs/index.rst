.. veracross-client documentation master file, created by
   sphinx-quickstart on Mon Sep 11 11:07:48 2023.
   This file provides an overview of the veracross-client project.

Welcome to veracross-client's documentation!
============================================

This project provides a Python wrapper for the Veracross API, allowing Veracross administrators to access, manipulate, and manage data programmatically with Python.

Installation
------------

Install the latest version of veracross-client:

.. code-block:: bash

   pip install --upgrade veracross-client

Getting Started
---------------

1. Create an OAuth Application in Veracross following the instructions in the `Veracross Community documentation <https://community.veracross.com/s/article/OAuth-Applications-and-Veracross-Overview>`_.

2. Configure the OAuth Application's scopes to access the desired data.

3. Use `sample_config.json` in this repository as a template to create a `config.json` file:

.. code-block:: json

   {
       "client_id": "OAuth application client id",
       "client_secret": "OAuth application client secret",
       "school_route": "school route that appears in Veracross URL"
   }

4. Connect to the Veracross API:

.. code-block:: python

   import veracross_client as vc
   import json

   secrets = json.loads(open('config.json').read())

   client = vc.VeracrossClient(school_route=secrets['school_route'],
                               client_id=secrets['client_id'],
                               client_secret=secrets['client_secret'],
                               scopes=["_scope 1_", "_scope 2_", ...])

Contributing
------------

The wrapper is in development. Report any issues you encounter, specifying the problematic method and a description of the error.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
