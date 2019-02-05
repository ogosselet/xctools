# Introduction 
Un fichier source AIXM peut contenir les informations géographiques sur les frontières des pays à considérer pour la définition de zones de l' espace aérien. Cette information est stockée comme suit:
<Gbr>
    <GbrUid mid="19076981">
        <txtName>BELGIUM_NETHERLANDS</txtName>
    </GbrUid>
    <codeType>ST</codeType>
    [ <Gbv>...</Gbv>]
</Gbr>
La définition d'une zone particulière de l' espace aérien peut faire référence à une section de frontière délimitée par 2 points "sur" la frontière (mais pas nécessairement explicitement présent dans la liste des points <Gbv>)
Extraire cette information et l' ajouter à une description d' espace aérien OpenAir est une opération fastidieuse.
Le but de cette commande CLI serait de faciliter se travaille d' extraction pour assister dans la maintenance de la définition des espace aérien partiellement défini par une référence à une section de frontière
# Proposition de CLI
- airspace-cli border list
    Devrait retourner la liste des frontières présentent dans le fichier source sous la forme d' une table avec l' information
    <txtName> | mid_string
- airspace-cli border extract --src aixm_file --mid mid --limit "lon_1,lat_1,lon_2,lat_2" --format (wkt|openair|...)
    src: le fichier source AIXM 4.5
    mid: le mid de la frontière à considérer pour l' extraction
    limit: la longitude/latitude des points "limite" de la section de frontière à extraire 
    format: le format d' output (Wkt, OpenAir, ...)
Lorsque le format Openair est sélectionné la liste des points de la section de frontière doivent être retourné comme une liste de directive OpenAir "DP"
DP 50:41:11N 004:29:20E
DP 51:02:51N 004:59:55E
DP 51:10:05N 004:47:46E
...
# Implementation
- Créer un module python airspace-cli
- Modifier les Classes du module aixm_parser qui réalise l' extraction des sections de frontière pour faciliter leur "exposition" au module CLI
# Note:
Concernant la gestion des formats d' output de l' info géographique on peut commencer "simple" dans la structure du code mais il faudrait envisager d' avoir un format "interne" commun à toute les fonctions pour transmettre les coordonnées d'un point ou d'une liste de point et d' avoir un module de "formatage" qui permet de switcher l' output de
- [Float]
- [OpenAir DP lat lon]
- [Point WKT ou WKB]
Si la liste des points représente un polygone "complet", on pourrait rajouter un output format
- GeoJSON
- Polygon WKT, WK
- KML
- ...
