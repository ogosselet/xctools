Airspace Module
===============

Geo Coordinates Format
----------------------

There is a mix of multiple coordinates format in the AIXM file.
This is mainly true for "border" definition.
We can find point like:

.. code-block:: xml

    <Gbv>
        <codeType>GRC</codeType>
        <geoLat>51.089056N</geoLat>
        <geoLong>002.545428E</geoLong>
        <codeDatum>WGE</codeDatum>
        <valCrc>DEA229FF</valCrc>
    </Gbv>

=> this needs to be interpreted as "Decimal Degrees"

or

.. code-block:: xml

    <Gbv>
        <codeType>GRC</codeType>
        <geoLat>510521.37N</geoLat>
        <geoLong>0023242.99E</geoLong>
        <codeDatum>WGE</codeDatum>
        <valCrc>388AF379</valCrc>
    </Gbv>

=> this needs to be interpreted as "Degrees Minutes Seconds" with Decimal


Airspace Geographical Definition
--------------------------------

For Airspace with a reference to the border as show in AIXM extract below:

**Geo. definition sample**

.. code-block:: xml

    <Abd>
        <AbdUid mid="100760256">
            <AseUid mid="100760256">
                <codeType>D</codeType>
                <codeId>EBD26</codeId>
            </AseUid>
        </AbdUid>
        <Avx>
            <codeType>GRC</codeType>
            <geoLat>494735N</geoLat>
            <geoLong>0054237E</geoLong>
            <codeDatum>WGE</codeDatum>
            <valCrc>2847BD34</valCrc>
        </Avx>
        <Avx>
            <GbrUid mid="19048558">
                <txtName>BELGIUM_FRANCE</txtName>
            </GbrUid>
            <codeType>FNT</codeType>
            <geoLat>494137N</geoLat>
            <geoLong>0051624E</geoLong>
            <codeDatum>WGE</codeDatum>
            <valCrc>7A533BA3</valCrc>
        </Avx>
        <Avx>
            <codeType>GRC</codeType>
            <geoLat>500656N</geoLat>
            <geoLong>0045209E</geoLong>
            <codeDatum>WGE</codeDatum>
            <valCrc>DA2F2D08</valCrc>
        </Avx>
        <Snip> ... more data </Snip>
    </Abd>

**Border definition sample**

.. code-block:: xml

    <Gbr>
    <GbrUid mid="19048558">
        <txtName>BELGIUM_FRANCE</txtName>
    </GbrUid>
    <codeType>ST</codeType>
    <Gbv>
        <codeType>GRC</codeType>
        <geoLat>510521.37N</geoLat>
        <geoLong>0023242.99E</geoLong>
        <codeDatum>WGE</codeDatum>
        <valCrc>388AF379</valCrc>
    </Gbv>
    <Gbv>
        <codeType>GRC</codeType>
        <geoLat>51.089056N</geoLat>
        <geoLong>002.545428E</geoLong>
        <codeDatum>WGE</codeDatum>
        <valCrc>DEA229FF</valCrc>
    </Gbv>
    <Snip>
        ... more <Gbv></Gbv>
    </Snip>
    <Gbv>
        <codeType>GRC</codeType>
        <geoLat>51.058447N</geoLat>
        <geoLong>002.5621E</geoLong>
        <codeDatum>WGE</codeDatum>
        <valCrc>A396EB40</valCrc>
    </Gbv>
    <Gbv>
        <codeType>GRC</codeType>
        <geoLat>51.013853N</geoLat>
        <geoLong>002.575229E</geoLong>
        <codeDatum>WGE</codeDatum>
        <valCrc>0442B3AF</valCrc>
    </Gbv>


The <Avx> point of type <codeType>FNT is matching quite precisely the geographical border.
(as it can be confirme using google earth)
This point is not in the <Gbv> points of the border definition present in the AIXM source file.
It is quite easy to isolate the 2 "surrounding" <Gbv> points in the AIXM source file to define
where the usefull part of the border relevant for our Airspace is starting.

The next <Avx> point of type <codeType>GRC is again matching quite precisely the geographical border.
It is quite easy to isolate where the border is stoping using a similar technique.

Based on these 4 points, it is possible to define in which direction we have to walk the <Gbv> points
of the border definition and add all the relevant border points to the Airspace definition

Usage
-----

.. code-block:: python

    from aixm_parser import AixmSource, Airspace

    # Open an AIXM 4.5 src. file
    aixm_source = AixmSource('your_aixm_4.5_source_file.xml')

    # Working on a specific Airspace identified by its "mid" in the src. file
    airspace = Airspace(aixm_source, mid)

    # Trigger the parsing process
    airspace.parse_airspace()

    # Iterate to get all the points of the polygon
    for points in airspace.gis_data:
        print("Long: {} - Lat: {}".format(point[1], point[0]))

