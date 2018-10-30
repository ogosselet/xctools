Briefing Module
===============

Download a Pre-Flight Information Bullentins (PIB) containing published NOTAMs and generate a list of XCTools Notam objects.

XCTools target to support multiple sources to ensure:

- information reliability: a source might provide more precise information for a specific region (FIRs) of interest
- service continuity: it is possible that a source change the format of the data and that the XCTools community needs some time to rework the relevant module

=> it is required to be able to switch the system to an alternate source of briefing.

We expect contributions from the community if other sources are required.

Base Class/Module
-----------------

This base class define the interface/method that every specific source class should implement.

.. automodule:: briefing.source.base
    :members:
    :private-members:

NATS
----

The `NATS <http://www.nats-uk.ead-it.com/public/index.php.html>`_ is a UK based company providing Aeronautical Information Services.

NATS has proven to be a stable and reliable source of PIB information since we use it (2015).
Access to the NOTAM information requires user website registration.

.. automodule:: briefing.source.nats
    :members:
    :private-members:
