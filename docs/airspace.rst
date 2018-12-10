Airspace Module
===============

Format
------

There is a mix & match of multiple coordinates format in the AIXM file.
This is mainly true for "border" definition.
We cn find point like:

<Gbv>
    <codeType>GRC</codeType>
    <geoLat>51.089056N</geoLat>
    <geoLong>002.545428E</geoLong>
    <codeDatum>WGE</codeDatum>
    <valCrc>DEA229FF</valCrc>
</Gbv>

=> this needs to be interpreted as "Decimal Degrees"

or

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

The <Avx> point of type <codeType>FNT is matching quite precisely the geographical border.
(as I could confirm using google earth) 
This point is not in the <Gbv> points of the border definition present in the AIXM source file.
It is quite easy to isolate the 2 "surrounding" <Gbv> points in the AIXM source file.

The next <Avx> point of type <codeType>GRC is again matching quite precisely the geographical border.
Using the same technique it is quite easy to isolate the 2 "surrounding" <Gbv> points in the AIXM source file

Based on these 6 points, it is possible to define in which direction we have to walk the <Gbv> points
of the border definition and add all the relevant border points to the Airspace definition



point just before & just after are matching border points
Looks like it will not be required to extrapolate the Airspace geometry intersection with the border

