Methodology
===========

The methodology behind F|Heat involves several key steps:

1. **Data Loading**: Downloading shape(.shp)-files for buildings, parcels, and streets. The plugin starts at the very beginning of the planning process by first downloading the shape files of the buildings, parcels and streets of the city or district to be analysed. The city name is selected from a drop-down list.
2. **Customization**: Preparing the files for further calculations with added attributes.
3. **Status quo Analysis**: The heat line density [kWh/m*a] is added to the street shape file. The parcels of neighbouring buildings are then merged into a larger polygon and supplemented with attributes that make it easier to find suitable areas for heat networks. Both layers are automatically given a style that makes high heat densities [kWh/ha*a] easily recognisable. Heat line densities and heat densities are labelled in accordance with federal guidelines for heat planning.
4. **Network Analysis**: The user can manually draw a polygon that acts as a supply area for a pipe-bound supply via a heating network. This polygon defines the buildings to be taken into account. Without a polygon, all buildings loaded in the project are taken into account in the network design and connected. The user must add a heat source as a point layer at a possible location for a heating centre. In addition, the user can select streets in the street file that are not to be included in the grid analysis, i.e. where no grid is to run and no buildings are to be connected. The tool generates a radiant network with the function of defining the shortest route to the heat source. The resulting heat requirements per route metre and year are used to determine the required pipe dimensions. The resulting network is saved as a shape file and a summary of the network is also saved.

The result is a shape file and a tabular summary, which can be used for further detailed planning.

Current Database
----------------
The current database is based on open data sources that are freely accessible.

- Shape files of the house perimeters with heat demand and street centre line (NRW): `OpenGeodata.NRW <https://opengeodata.nrw.de/produkte/umwelt_klima/klima/kwp/>`_
- Shape files of the parcels: `WFS NRW <https://www.wfs.nrw.de/geobasis/wfs_nw_inspire-flurstuecke_alkis>`_
- Velocity in the pipes adopted from Nussbaumer and Thalmann [1]_.
- Internal diameter and U-values (average value from various manufacturer specifications):
    - `Rehau <https://www.rehau.com/downloads/99896/rauthermex-rauvitherm-technische-information.pdf>`_
    - `Enerpipe <https://www.enerpipe.de/typo3conf/ext/so_bp_base/Resources/Public/JavaScript/Dist/pdfjs/web/viewer.html?file=/fileadmin/daten/02_produkte/06_Rohre-und-Verbindungstechnik/Rohrsysteme_TI_821000100_04-2021_web.pdf#page=1>`_
    - `Isoplus <https://www.isoplus.de/fileadmin/data/downloads/documents/germany/products/Doppelrohr-8-Seiten_DEUTSCH_Web.pdf>`_

.. TODO: Add RWT Jagdt table description

Limitations
-----------
The content of the download is designed for NRW, as there is no standardised nationwide data source yet.
The further steps of the plugin can also be carried out for other federal states, provided that the data structure is the same and the attributes have the same names.
Unlike many other planning software programmes, the plugin is free and open source. 
These are also developed for detailed planning and do not offer the possibility of carrying out rough designs in just a few minutes. Tools such as nPro, for example, are also primarily developed for neighbourhood planning and not for municipal heat planning.


References
----------

.. [1] Nussbaumer, T., Thalmann S. (2016). Influence of system design on heat distribution costs in district heating. Energy, 230, 496–505. https://doi.org/10.1016/j.energy.2016.02.062.
