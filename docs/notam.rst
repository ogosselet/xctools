Notam Module
============

Further parses & normalizes the Notam information. 
Creates an `XCTools Notam <./code.html#notam.notam.Notam>`_  from its dictionary representation 
as produced by the `Briefing module <./briefing.html>`_ 

Usage
-----

.. code-block:: python

    import ast

    from notam import Notam

    #notam_dict_str = a string representation of a Notam as extracted and normalized by the Briefing module

    notam_dict_str = "{'a': '', 'upper': 'FL070', 'c': '18/09/14 14:00', 'b': '18/09/12 06:00', 'e': 'EBR20-BRASSCHAAT ACT', 'src': 'NATS', 'lower': 'GND', 'q': 'EBBU/QRRCA/IV/BO/W/000/070/5121N00435E004', 'sched': 'DAILY 0600-1400', 'ref': 'B4404/18'}"

    notam = Notam(ast.literal_eval(notam_dict_str))
    print(notam.reference)
    # B4404/18
    print(notam.text)
    # EBR20-BRASSCHAAT ACT
    print(notam.sched)
    # DAILY 0600-1400
    print(notam.scope)
    # W
    notam.start_time
    # datetime.datetime(2018, 9, 12, 6, 0)
    print(notam.start_time)
    # 2018-09-12 06:00:00

This module further parse the Notam information and allows easier access to some handy information inside
the Q Line directly using specific object attributes.

This will be extended with additional features like the capability to find the relevant Airspace in the
Notam text, etc ... 