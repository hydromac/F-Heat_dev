# -*- coding: utf-8 -*-
"""
/***************************************************************************
 HeatNetTool
                                 A QGIS plugin
 This plugin provides tools for district heating planning
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-03-04
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Lars Goray
        email                : lars.goray@fh-muenster.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog
from qgis.core import QgsProject, QgsMapLayer, QgsVectorLayer

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .heat_net_tool_dialog import HeatNetToolDialog

import os.path
import subprocess
import pandas as pd
import geopandas as gpd
import os
from pathlib import Path

# Import code for net analysis
from .net_analysis import get_closest_point, calculate_GLF, calculate_volumeflow, calculate_diameter_velocity_loss, Streets, Source, Buildings, Graph, Net, Result

# Project path
project_file_path = QgsProject.instance().fileName()
project_dir = os.path.dirname(project_file_path)
# currect path of this script
current_dir = os.path.dirname(__file__)

# Project CRS
project_crs = QgsProject.instance().crs()
epsg_code = project_crs.authid()

class HeatNetTool:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'HeatNetTool_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Heat Net Tool ')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('HeatNetTool', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/heat_net_tool/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Toolbox for planning district heating networks'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Heat Net Tool '),
                action)
            self.iface.removeToolBarIcon(action)
    
    def select_output_file(self, dir, lineEdit, filetype):

        filename, _filter = QFileDialog.getSaveFileName(
            self.dlg, "Select output file ",dir, filetype)
        lineEdit.setText(filename)

    def get_all_loaded_layers(self):
        """Get a list of all loaded layers in the project, including layers within groups."""
        root = QgsProject.instance().layerTreeRoot()
        all_layers = root.layerOrder()
        loaded_layers = []

        for layer in all_layers:
            if isinstance(layer, QgsMapLayer):
                loaded_layers.append(layer)

        return loaded_layers

    def load_layers_to_combobox(self, combobox):
        '''loads layers to selected combobox'''
        # Fetch the currently loaded layers
        layers = self.get_all_loaded_layers()
        # Clear the contents of the comboBox from previous runs
        combobox.clear()
        # Add a default translated item as the first item in the ComboBox
        combobox.addItem(self.tr("Select Layer"))
        # Populate the comboBox with names of all the loaded layers
        combobox.addItems([layer.name() for layer in layers])
        # Set the default item as the current index
        combobox.setCurrentIndex(0)
    
    def load_attributes_to_combobox(self, layer_name, combobox):
        """Load attributes of the selected layer to the given combobox."""
        # Find the layer by its name
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]  # Assuming unique names
        # Clear the contents of the comboBox from previous runs
        combobox.clear()
        # Add a default item as the first item in the ComboBox
        combobox.addItem(self.tr("Select Attribute"))
        # Populate the comboBox with names of all the attributes of the layer
        for field in layer.fields():
            combobox.addItem(field.name())

        # Set the default item as the current index
        combobox.setCurrentIndex(0)

    def load_attributes(self, combobox_in, combobox_out):
        """Load attributes of the selected layer in combobox_in to the given combobox_out."""
        # Get the current layer name selected in the specified combobox
        layer_name = getattr(self.dlg, combobox_in).currentText()

        layers = self.get_all_loaded_layers()

        # Load attributes to the specified combobox
        if layer_name in [layer.name() for layer in layers]:
            self.load_attributes_to_combobox(layer_name, getattr(self.dlg, combobox_out))

    def install_package(self,package_list):
        """installs python packages with pip"""
        for package in package_list:
            try:
                # Führt den Befehl "pip install" aus, um das Paket zu installieren
                subprocess.check_call(["pip", "install", package])
                print(f"{package} wurde erfolgreich installiert.")
            except subprocess.CalledProcessError:
                print(f"Fehler beim Installieren von {package}.")

    def get_layer_path_from_combobox(self, combobox):
        """
        Get the path of the selected layer from the given ComboBox.

        :param combobox: The QComboBox object representing the layer selection.
        :type combobox: QComboBox

        :return: The path of the selected layer.
        :rtype: str
        """
        # Get the name of the selected layer from the ComboBox
        selected_layer_name = combobox.currentText()

        # Find the layer in the project
        layers = QgsProject.instance().mapLayersByName(selected_layer_name)

        if layers:
            # Assume we take the first found layer if multiple layers have the same name
            selected_layer = layers[0]
            # Extract the path from the layer information
            path = selected_layer.source()

            # Check if '|' character exists in the path
            if '|' in path:
                # Split the path and layer name
                path_parts = path.split('|')
                path = path_parts[0]  # Path is the first part
                # Layer name is the second part, remove 'layername='
                selected_layer_name = path_parts[1].replace('layername=', '')

            return path, selected_layer_name
        else:
            return None, None

    def add_shapefile_to_project(self, shapefile_path):
        """Add the generated network shapefile to the QGIS project."""
        layer_name = os.path.splitext(os.path.basename(shapefile_path))[0]
        layer = QgsVectorLayer(path = shapefile_path, baseName = layer_name, providerLib = 'ogr')
        if not layer.isValid():
            print("Layer failed to load!")
            return
        QgsProject.instance().addMapLayer(layer)

    def update_progress(self, progressBar, value):
        progressBar.setValue(value)

    def network_analysis(self):

        self.update_progress(self.dlg.net_progressBar, 0)

        # pipe info
        current_dir = os.path.dirname(__file__)
        excel_file_path = Path(current_dir) / 'pipe_data.xlsx'
        pipe_info = pd.read_excel(excel_file_path, sheet_name='pipe_data')

        dn_list = pipe_info['DN'].to_list()

        # Load Profiles
        load_profiles = ['EFH', 'MFH', 'GHA', 'GMK', 'GKO']

        # Temperatures from SpinBox
        t_supply = self.dlg.net_doubleSpinBox_supply.value()
        t_return = self.dlg.net_doubleSpinBox_return.value()

        # Layer paths
        source_path, source_layer = self.get_layer_path_from_combobox(self.dlg.net_comboBox_source)
        streets_path, streets_layer = self.get_layer_path_from_combobox(self.dlg.net_comboBox_streets)
        buildings_path, buildings_layer = self.get_layer_path_from_combobox(self.dlg.net_comboBox_buildings)
        polygon_path, polygon_layer  = self.get_layer_path_from_combobox(self.dlg.net_comboBox_polygon)

        heat_attribute = self.dlg.net_comboBox_heat.currentText()
        power_attribute = self.dlg.net_comboBox_power.currentText()

        self.update_progress(self.dlg.net_progressBar, 2)

        # Instantiate classes
        buildings = Buildings(buildings_path, heat_attribute, buildings_layer)
        source = Source(source_path, source_layer)
        streets = Streets(streets_path, streets_layer)
        
        # check if polygon checkbox is checked
        if self.dlg.net_checkBox_polygon.isChecked():
            # load polygon as gdf
            if polygon_layer == None:
                polygon = gpd.read_file(polygon_path)
            else: 
                polygon = gpd.read_file(polygon_path, layer=polygon_layer)

            # only buildings within polygon
            buildings.gdf = gpd.sjoin(buildings.gdf, polygon, how="inner", predicate="within")

        # Drop unwanted routes if existing
        try:
            streets.gdf = streets.gdf[streets.gdf['possible_route']==1]
        except:
            pass

        self.update_progress(self.dlg.net_progressBar, 5)

        # create connection points
        buildings.add_centroid()
        buildings.closest_points_buildings(streets.gdf)
        source.closest_points_sources(streets.gdf)
        streets.add_connection_to_streets(buildings.gdf, source.gdf)

        self.update_progress(self.dlg.net_progressBar, 15)

        # Graph erstellen
        graph = Graph()
        graph.create_street_network(streets.gdf)
        self.update_progress(self.dlg.net_progressBar, 20)
        graph.connect_centroids(buildings.gdf)
        self.update_progress(self.dlg.net_progressBar, 25)
        graph.connect_source(source.gdf)
        graph.add_attribute_length()
        #graph.test_connection(source.gdf)

        self.update_progress(self.dlg.net_progressBar, 30)

        net = Net(t_supply,t_return)
        net.network_analysis(graph.graph, buildings.gdf, source.gdf, pipe_info, power_att=power_attribute, progressBar=self.dlg.net_progressBar)
        #net.plot_network(streets.gdf,buildings.gdf,source.gdf,filename='../Netz.png')

        # GeoDataFrame aus Netz erstellen
        net.ensure_power_attribute()
        net.graph_to_gdf(crs = epsg_code)
        
        # path to save net shape file and result
        shape_path = self.dlg.net_lineEdit_net.text()
        result_path = self.dlg.net_lineEdit_result.text()

        # save net shape
        net.gdf.to_file(shape_path)

        # load net as layer
        self.add_shapefile_to_project(shape_path)
        
        self.update_progress(self.dlg.net_progressBar,100)



    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = HeatNetToolDialog()

            # install python packages
            package_list = ['openpyxl','networkx','geopandas']
            self.dlg.intro_pushButton_load_packages.clicked.connect(lambda: self.install_package(package_list))
            
            # select output file
            self.dlg.net_pushButton_net_output.clicked.connect(lambda: self.select_output_file(project_dir, self.dlg.net_lineEdit_net,'*.gpkg;;*.shp'))
            self.dlg.net_pushButton_result.clicked.connect(lambda: self.select_output_file(project_dir, self.dlg.net_lineEdit_result,'*.txt'))
        
        ### Network Analysis ###   
        
        # Load layers into all the comboBoxes
        self.load_layers_to_combobox(self.dlg.net_comboBox_buildings)
        self.load_layers_to_combobox(self.dlg.net_comboBox_streets)
        self.load_layers_to_combobox(self.dlg.net_comboBox_source)
        self.load_layers_to_combobox(self.dlg.net_comboBox_polygon)
        
        # Connect signal for net_comboBox_buildings to load attributes on change
        self.dlg.net_comboBox_buildings.currentIndexChanged.connect(lambda: self.load_attributes('net_comboBox_buildings', 'net_comboBox_heat'))
        self.dlg.net_comboBox_buildings.currentIndexChanged.connect(lambda: self.load_attributes('net_comboBox_buildings', 'net_comboBox_power'))

        self.dlg.net_pushButton_start.clicked.connect(self.network_analysis)

        # show the dialog
        self.dlg.show()