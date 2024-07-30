import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, LineString
import networkx as nx
import matplotlib.pyplot as plt
from openpyxl import load_workbook
import sys
import os

def get_closest_point(line, point):
    '''
    Calculate the closest point on a line to a given point.

    Parameters
    ----------
    line : shapely.geometry.LineString
        The line on which to find the closest point.
    point : shapely.geometry.Point
        The point from which to find the closest point on the line.

    Returns
    -------
    shapely.geometry.Point
        The closest point on the line to the given point.
    '''
    closest_point = line.interpolate(line.project(point))
    return closest_point

def calculate_GLF(n):
    '''
    Calculate the simultaneity factor (Gleichzeitigkeitsfaktor).

    Parameters
    ----------
    n : int
        Number of buildings.

    Returns
    -------
    float
        The simultaneity factor.
    '''
    a = 0.4497
    b = 0.5512
    c = 53.8483
    d = 1.7627
    return a + (b / (1 + pow(n/c, d)))

def calculate_volumeflow(kW_GLF, htemp, ltemp):
    '''
    Calculate the volumetric flow rate in a pipeline.

    Parameters
    ----------
    kW_GLF : float
        Power with simultaneity factor applied.
    htemp : float
        Supply temperature.
    ltemp : float
        Return temperature.

    Returns
    -------
    float
        Volumetric flow rate in liters per second.
    '''
    #piecewise linear interpolation
    t = [0, 10, 20, 30, 40, 50, 60, 70, 80 , 90, 100] 
    d = [0.99984, 0.9997, 0.99821, 0.99565, 0.99222, 0.98803, 0.9832, 0.97778, 0.97182, 0.96535, 0.9584]
    c = [4.2176, 4.1921, 4.1818, 4.1784, 4.1785, 4.1806, 4.1843, 4.1895, 4.1963, 4.205, 4.2159]
    density = np.interp(int(htemp), t, d)
    cp = np.interp(int(htemp), t, c)

    volumeflow = kW_GLF / (density * cp * (int(htemp) - int(ltemp))) # liter/s
    return volumeflow

def calculate_diameter_velocity_loss(volumeflow, htemp, ltemp, length, pipe_info):
    '''
    Calculate the diameter, velocity, and loss of pipelines.

    Parameters
    ----------
    volumeflow : float
        Volumetric flow rate.
    htemp : float
        Supply temperature.
    ltemp : float
        Return temperature.
    length : float
        Length of the pipeline.
    pipe_info : DataFrame
        DataFrame containing pipeline information with columns 'DN', 'di', 'U-Value', 'v_max'.

    Returns
    -------
    tuple
        A tuple containing:
        - DN (float): Nominal diameter.
        - velocity (float): Velocity in the pipeline.
        - loss (float): Heat loss.
    '''
    DN_list = pipe_info['DN']   
    di_list = pipe_info['di']   
    U_list = pipe_info['U-Value'] 
    v_list = pipe_info['v_max'] 
    mtemp = (htemp+ltemp)/2
    K = mtemp - 10  # Outside Temp. = 10°C for underground installation 

    vtemp = []
    for i,d_i in enumerate(di_list):
        r = d_i/2
        v = volumeflow * 1000 / (np.pi *  pow(r,2)) # dm^3/mm^2 --> Factor 1000
        vtemp.append(v)

        if v <= v_list[i]:
            break
    else:  
        v = min(vtemp, key=lambda x: abs(x-1))
        i = vtemp.index(v)

    loss = 8760 * 2 * (U_list[i] * K * length) / 1000 # 8760 h/a, 2* --> supply and return
    DN = DN_list[i] 

    return DN, v, loss

class Streets:
    '''
    A class to manage street geometries and to add connection points from buildings and energy sources to the streets.

    Attributes
    ----------
    gdf : GeoDataFrame
        A GeoDataFrame containing street geometries and attributes.

    Methods
    -------
    add_connection_to_streets(buildings, sources):
        Inserts connection points into the street lines based on buildings and energy sources.
    '''

    def __init__(self, path, layer = None):
        '''
        Initializes the Streets class with a GeoDataFrame from a specified path.

        Parameters
        ----------
        path : str
            The path to the file containing street geometries.
        layer : str, optional
            The layer to read from the file (default is None).
        '''
        if layer == None:
            self.gdf = gpd.read_file(path)
        else: 
            self.gdf = gpd.read_file(path, layer=layer)

    def add_connection_to_streets(self, buildings, sources):
        '''
        Inserts connection points from buildings and energy sources into the street lines.

        Parameters
        ----------
        buildings : GeoDataFrame
            A GeoDataFrame containing building geometries and attributes, including 'street_id' and 'Anschlusspunkt'.
        sources : GeoDataFrame
            A GeoDataFrame containing energy source geometries and attributes, including 'street_id' and 'Anschlusspunkt'.
        '''

        for df in [buildings, sources]:
            for index, row in df.iterrows():
                street_id = row['street_id']
                if not pd.isna(street_id):
                    anschlusspunkt = row['Anschlusspunkt']
                    line = self.gdf['geometry'][street_id]
                    line_coords = list(line.coords)

                    insertion_position = None
                    min_distance = float('inf')

                    # Find insertion position in the line
                    for i in range(1, len(line_coords)):
                        segment = LineString([line_coords[i-1], line_coords[i]])
                        distance = segment.distance(anschlusspunkt)

                        if distance < min_distance:
                            min_distance = distance
                            insertion_position = i

                    # Insert the connection point into the line coordinates
                    if (anschlusspunkt.x, anschlusspunkt.y) not in line_coords:
                        line_coords.insert(insertion_position, (anschlusspunkt.x, anschlusspunkt.y))
                        self.gdf.at[street_id, 'geometry'] = LineString(line_coords)

class Source:
    '''
    A class to manage energy source geometries and to find the closest points on street networks.

    Attributes
    ----------
    gdf : GeoDataFrame
        A GeoDataFrame containing source geometries and attributes.

    Methods
    -------
    closest_points_sources(streets):
        Finds the closest points on the street network for each energy source and adds these points to the GeoDataFrame.
    '''

    def __init__(self, path, layer = None):
        '''
        Initializes the Source class with a GeoDataFrame from a specified path.

        Parameters
        ----------
        path : str
            The path to the file containing source geometries.
        layer : str, optional
            The layer to read from the file (default is None).
        '''
        if layer == None:
            self.gdf = gpd.read_file(path)
        else: 
            self.gdf = gpd.read_file(path, layer=layer)
        
    def closest_points_sources(self, streets):
        '''
        Finds the closest point on the street network for each energy source and adds these points to the GeoDataFrame.

        Parameters
        ----------
        streets : GeoDataFrame
            A GeoDataFrame containing street geometries and attributes.
        '''
        # Iteration over each source and finding the closest point on the street network
        for index, row_s in self.gdf.iterrows():

            # Initialize variables for minimum distance and closest point
            min_distance = float('inf')
            closest_point = None
            source = row_s['geometry']

            # Iterate over each line in the street network
            for idx,row in streets.iterrows():
                line_coords = list(row['geometry'].coords)  # List of points that make up the line
                
                # Iterate over each line segment to find the closest point
                for i in range(1, len(line_coords)):
                    start_point = Point(line_coords[i-1])
                    end_point = Point(line_coords[i])
                    line_segment = LineString([start_point, end_point])

                    distance = line_segment.distance(source)

                    if distance < min_distance:
                        min_distance = distance
                        closest_point = get_closest_point(LineString([start_point, end_point]), source)
                        id = idx
            self.gdf.at[index, 'Anschlusspunkt'] = closest_point
            self.gdf.at[index, 'street_id'] = int(id)

class Buildings:
    '''
    A class to manage building geometries, add centroids, and find the closest points on street networks.

    Attributes
    ----------
    buildings_all : GeoDataFrame
        A GeoDataFrame containing all building geometries and attributes.
    gdf : GeoDataFrame
        A GeoDataFrame containing buildings with a specified heat attribute greater than zero.

    Methods
    -------
    add_centroid():
        Adds the centroid of each building's geometry to the GeoDataFrame.
    closest_points_buildings(streets):
        Finds the closest point on the street network for each building and adds these points to the GeoDataFrame.
    '''

    def __init__(self, path, heat_att, layer = None):
        '''
        Initializes the Buildings class with a GeoDataFrame from a specified path and filters buildings based on a heat attribute.

        Parameters
        ----------
        path : str
            The path to the file containing building geometries.
        heat_att : str
            The name of the attribute representing heat consumption.
        layer : str, optional
            The layer to read from the file (default is None).
        '''
        if layer == None:
            self.buildings_all = gpd.read_file(path)
        else: 
            self.buildings_all = gpd.read_file(path, layer=layer)
        
        # Filter buildings with heat consumption
        try:
            buildings_wvbr = self.buildings_all[self.buildings_all[heat_att]>0] 
        except:
            print('Check heat attribute!')

        self.gdf = buildings_wvbr
    
    def add_centroid(self):
        '''
        Adds the centroid of each building's geometry to the GeoDataFrame.

        Notes
        -----
        The centroid is computed for each polygon in the GeoDataFrame and added as a new column 'centroid'.
        '''
        self.gdf = self.gdf.copy() # Suppress warning
        self.gdf['centroid'] = self.gdf.loc[:, 'geometry'].centroid

    def closest_points_buildings(self, streets):
        '''
        Finds the closest point on the street network for each building and adds these points to the GeoDataFrame.

        Parameters
        ----------
        streets : GeoDataFrame
            A GeoDataFrame containing street geometries and attributes.

        Notes
        -----
        For each building, this method computes the closest point on the street network and adds it to the GeoDataFrame 
        along with the ID of the closest street.
        '''
        # Create spatial index for the streets
        sindex = streets.sindex

        # Iterate over each building centroid
        for index, row_p in self.gdf.iterrows():
            centroid = row_p['centroid']

            # Use spatial index to get the nearest lines to the centroid
            possible_matches_index = list(sindex.nearest(centroid))
            possible_matches = streets.iloc[[i[0] for i in possible_matches_index]]

            # Find the line closest to the centroid
            closest_line = possible_matches.geometry.distance(centroid).idxmin()

            # Compute the closest point on this line
            closest_point = get_closest_point(streets.at[closest_line, 'geometry'], centroid)

            self.gdf.loc[index, 'Anschlusspunkt'] = closest_point
            self.gdf.loc[index, 'street_id'] = int(closest_line)

class Graph:
    '''
    A class to represent and manipulate a street network graph using NetworkX.

    Attributes
    ----------
    graph : nx.Graph
        A NetworkX graph representing the street network.

    Methods
    -------
    create_street_network(streets):
        Creates a street network graph from a GeoDataFrame of streets.
    connect_centroids(buildings):
        Connects building centroids to the street network.
    connect_source(sources):
        Connects energy sources to the street network.
    add_attribute_length():
        Adds a 'length' attribute to each edge in the graph.
    plot_G():
        Plots the street network graph.
    get_connected_points(input_point):
        Returns the points connected to the given input point in the graph.
    plot_graph(input_point, connected_points):
        Plots the graph with connected points highlighted.
    graph_to_gdf():
        Converts the NetworkX graph to a GeoDataFrame.
    save_nodes_to_shapefile(filename):
        Saves the graph nodes as points in a shapefile, with node degree and coordinates annotated.
    '''
    def __init__(self):
        '''
        Initializes the Graph class with an empty NetworkX graph.
        '''
        self.graph = nx.Graph()
        
    def create_street_network(self, streets):
        '''
        Creates a street network graph from a GeoDataFrame of streets.

        Parameters
        ----------
        streets : GeoDataFrame
            A GeoDataFrame containing street geometries.
        '''
        # Dictionary with attributes for the edges
        edge_data = {'Typ': 'Straßenleitung'}  

        # Add nodes and edges
        for idx, row in streets.iterrows():
            geom = row['geometry']
            line_coords = list(geom.coords)

            # Iterate over each point on the line
            for i in range(len(line_coords)):
                node = line_coords[i]
                self.graph.add_node(node)

                # Connect point to previous point
                if i > 0:
                    prev_node = line_coords[i-1]
                    self.graph.add_edge(node, prev_node,**edge_data)
    
    def connect_centroids(self, buildings):
        '''
        Connects building centroids to the street network.

        Parameters
        ----------
        buildings : GeoDataFrame
            A GeoDataFrame containing building geometries and centroids.
        '''
        for index, row in buildings.iterrows():
            centroid = row['centroid']
            closest_point = row['Anschlusspunkt']
            if not pd.isna(closest_point):
                edge_data = {'Typ': 'Hausanschluss'}  # Dictionary mit dem Attribut, das die edge haben soll
                self.graph.add_edge(centroid.coords[0], (closest_point.x, closest_point.y), **edge_data)

    def connect_source(self, sources):
        '''
        Connects energy sources to the street network.

        Parameters
        ----------
        sources : GeoDataFrame
            A GeoDataFrame containing energy source geometries.
        '''
        for index, row in sources.iterrows():
            source = row['geometry']
            closest_point = row['Anschlusspunkt']
            if not pd.isna(source):
                edge_data = {'Typ': 'Quellenanschluss'}  # Dictionary mit dem Attribut, das die edge haben soll
                self.graph.add_edge(source.coords[0], (closest_point.x, closest_point.y), **edge_data)

    def add_attribute_length(self):
        '''
        Adds a 'length' attribute to each edge in the graph.
        '''
        for node1, node2 in self.graph.edges():
            geom = LineString([node1, node2])
            self.graph.edges[node1, node2]['length'] = geom.length

    def plot_G(self):
        '''
        Plots the street network graph.
        '''
        # set crs
        pos = {node: (node[0], node[1]) for node in self.graph.nodes}

        plt.figure()
        plt.title('Graph')
        nx.draw_networkx(self.graph, pos=pos, with_labels=False, font_size=6, node_size=3, node_color='blue', edge_color='gray')
        plt.show()

    
    def get_connected_points(self, input_point):
        '''
        Returns the points connected to the given input point in the graph.

        Parameters
        ----------
        input_point : tuple
            The input point coordinates.

        Returns
        -------
        list
            A list of points connected to the input point.
        '''
        # Check input point
        if input_point not in self.graph.nodes:
            print("Input point not in graph nodes.")
            return []

        # Get connected components
        for component in nx.connected_components(self.graph):
            if input_point in component:
                return list(component - {input_point})
        return []

    def plot_graph(self, input_point, connected_points):
        '''
        Plots the graph with connected points highlighted.

        Parameters
        ----------
        input_point : tuple
            The input point coordinates.
        connected_points : list
            A list of points connected to the input point.
        '''
        pos = {node: (node[0], node[1]) for node in self.graph.nodes}
        node_colors = ['blue' if node == input_point else 'red' for node in self.graph.nodes]

        # Color connected points
        for node in connected_points:
            node_colors[list(self.graph.nodes).index(node)] = '#00ff33'

        plt.figure(figsize=(20, 20))
        plt.title('Graph Network with connected and disconnected Points')

        # Legend
        legend_labels = {'Source': 'blue', 'Connected Points': '#00ff33', 'Disconnected Points': 'red'}
        legend_handles = [plt.Line2D([0], [0], marker='o', color=color, label=label, linestyle='None') for label, color in legend_labels.items()]
        plt.legend(handles=legend_handles, loc='upper right', fontsize=10)

        nx.draw(self.graph, pos, node_color=node_colors, font_size=6, node_size=10, with_labels=False)
        plt.show()

        
    def graph_to_gdf(self): # Methode ist ebenfalls in Net. Klassen zusammenfügen? --> Wegen übersichtlichkeit erstmal nicht
        '''
        Converts the NetworkX graph to a GeoDataFrame, including edge attributes.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame representing the graph edges.
        '''
        geometries = []
        attributes = {}

        for u, v, data in self.graph.edges(data=True):
            geometries.append(LineString([u, v]))

            # Collect attributes for each edge
            for key, value in data.items():
                if key in attributes:
                    attributes[key].append(value)
                else:
                    attributes[key] = [value]

        self.gdf = gpd.GeoDataFrame(attributes, geometry=geometries, crs='EPSG:25832')

    def save_nodes_to_shapefile(self, filename):
        """
        Saves the graph nodes as points in a shapefile, with node degree and coordinates annotated.

        Parameters
        ----------
        filename : str
            The file path to save the shapefile.
        """
        nodes_data = {'geometry': [], 'degree': [], 'x_coord': [], 'y_coord': []}

        for node in self.graph.nodes():
            nodes_data['geometry'].append(Point(node))
            nodes_data['degree'].append(self.graph.degree(node))
            nodes_data['x_coord'].append(node[0])
            nodes_data['y_coord'].append(node[1])

        nodes_gdf = gpd.GeoDataFrame(nodes_data, crs='EPSG:25832')
        nodes_gdf.crs= 'EPSG:25832'
        nodes_gdf.to_file(filename,driver='GPKG')

class Net:
    '''
    A class to represent and manipulate a network graph for heat distribution.

    Attributes
    ----------
    net : nx.Graph
        A NetworkX graph representing the network.
    htemp : float
        Supply temperature.
    ltemp : float
        Return temperature.

    Methods
    -------
    update_attribute(u, v, attribute, name):
        Adds or updates an attribute to an edge in the network graph.
    add_edge_attributes(pipe_info):
        Adds attributes to the network edges such as GLF, power_GLF, volumeflow, DN, velocity, and loss.
    network_analysis(G, buildings, sources, pipe_info, power_att, weight='length', progressBar=None):
        Calculates the network by finding the shortest path to each building.
    network_analysis_hz(G, buildings, sources, polygons, hz, pipe_info, power_att, weight='length'):
        Calculates the combined network of heating centers.
    plot_network(streets, buildings, sources, filename, title='Street network and calculated network'):
        Plots the street network, buildings, and calculated network, and saves the image.
    ensure_power_attribute():
        Ensures that each edge in the graph has the 'power' attribute.
    graph_to_gdf(crs='EPSG:25832'):
        Converts a NetworkX graph to a GeoDataFrame, including edge attributes.
    '''

    def __init__(self, htemp, ltemp):
        '''
        Initializes the Net class with an empty NetworkX graph, supply temperature, and return temperature.
        '''
        self.net = nx.Graph()
        self.htemp = htemp
        self.ltemp = ltemp

    def update_attribute(self, u, v, attribute, name):
        '''
        Adds or updates an attribute to an edge in the network graph.

        Parameters
        ----------
        u, v : nodes
            Nodes defining the edge.
        attribute : any
            Value of the attribute.
        name : str
            Name of the attribute.
        '''
        if name in self.net.edges[u, v]:
            self.net.edges[u, v][name] += attribute
        else:
            self.net.edges[u, v][name] = attribute

    def add_edge_attributes(self, pipe_info):
        '''
        Adds attributes to the network edges such as GLF, power_GLF, volumeflow, DN, velocity, and loss.

        Parameters
        ----------
        pipe_info : DataFrame
            DataFrame containing pipe information.
        '''
        for (u, v, data) in self.net.edges(data=True):
            n_building = data['n_building']
            power = data['power']
            length = data['length']

            GLF = calculate_GLF(n_building)
            power_GLF = power * GLF
            volumeflow = calculate_volumeflow(power_GLF, self.htemp, self.ltemp)
            diameter, velocity, loss = calculate_diameter_velocity_loss(volumeflow, self.htemp, self.ltemp, length, pipe_info)
            
            # Add attributes to the edges
            data['GLF'] = GLF
            data['power_GLF'] = power_GLF
            data['Volumeflow'] = volumeflow
            data['DN'] = diameter
            data['velocity'] = velocity
            data['loss'] = loss

    def network_analysis(self, G, buildings, sources, pipe_info, power_att, weight='length', progressBar=None):
        '''
        Calculates the network by finding the shortest path to each building.

        Parameters
        ----------
        G : nx.Graph
            The street network graph.
        buildings : GeoDataFrame
            GeoDataFrame of buildings.
        sources : GeoDataFrame
            GeoDataFrame of energy sources.
        pipe_info : DataFrame
            DataFrame containing pipe information.
        power_att : str
            Attribute name for power in the buildings GeoDataFrame.
        weight : str, optional
            Edge weight attribute for shortest path calculation (default is 'length').
        progressBar : callable, optional
            Progress bar function (default is None).
        '''

        start_point = (sources['geometry'][0].x, sources['geometry'][0].y)

        for idx, row in buildings.iterrows():
            end_point = (row['centroid'].x, row['centroid'].y)
            b1 = G.has_node(start_point)
            b2 = G.has_node(end_point)
            power = row[power_att]
            buildings_count = 1
            try:
                # Shortest path
                path = nx.shortest_path(G, start_point, end_point, weight=weight)
            
                # Add nodes and edges of the path to the network graph
                for i in range(len(path) - 1):
                    u, v = path[i], path[i+1]

                    # Copy all edge attributes
                    self.net.add_edge(u, v, **G.edges[u, v]) # hier steht self.net, weil das gar keine Funktion von mir ist

                    # Update attributes
                    self.update_attribute(u, v, power, 'power')    
                    self.update_attribute(u, v, buildings_count, 'n_building')
            except Exception as e: 
                print(f'Nor connection for:\n{row}')
                print(f'Error {e}')
                #sys.exit()
            
        # Add GLF, diameter, velocity, and loss attributes
        self.add_edge_attributes(pipe_info)      

    def plot_network(self, streets, buildings, sources, filename, title='Straßennetzwerk und berechnetes Netz'):
        '''
        Plots the street network, buildings, and calculated network, and saves the image.

        Parameters
        ----------
        streets : GeoDataFrame
            GeoDataFrame of streets.
        buildings : GeoDataFrame
            GeoDataFrame of buildings.
        sources : GeoDataFrame
            GeoDataFrame of energy sources.
        filename : str
            File name to save the image.
        title : str, optional
            Title of the plot (default is 'Street network and calculated network').
        '''
        # Node positions
        pos = {node: (node[0], node[1]) for node in self.net.nodes}

        # Create figure and axes
        fig, ax = plt.subplots(figsize=(15, 15))

        # Plot streets
        streets.plot(ax=ax, edgecolor='gray', zorder=1)

        # Plot buildings
        buildings.plot(ax=ax, facecolor='#ff8888', edgecolor='black', zorder=2)

        # Plot energy source as a point
        sources.plot(ax=ax, marker='o', markersize=15, color='green', zorder=3)

        # Plot network
        nx.draw_networkx_edges(self.net, pos=pos, ax=ax, edge_color='blue', width=1.0)

        # Enable grid and axis title
        #ax.grid(True)
        ax.set_title(title)

        # Save plot
        plt.savefig(filename, bbox_inches='tight')

        # Show plot
        plt.show()

    def ensure_power_attribute(self):
        """
        Ensures that each edge in the graph has the 'power' attribute.
        If an edge does not have the attribute, it is initialized with a value of 0.
        """
        for u, v in self.net.edges():
            if 'power' not in self.net[u][v]:
                self.net[u][v]['power'] = 0

    def graph_to_gdf(self, crs = 'EPSG:25832'):
        '''
        Converts a NetworkX graph to a GeoDataFrame, including edge attributes.

        Parameters
        ----------
        crs : str, optional
            Coordinate reference system (default is 'EPSG:25832').
        '''
        geometries = []
        attributes = {}

        for u, v, data in self.net.edges(data=True):
            geometries.append(LineString([u, v]))

            # Collect attributes for each edge
            for key, value in data.items():
                if key in attributes:
                    attributes[key].append(value)
                else:
                    attributes[key] = [value]

        # Create a GeoDataFrame from LineString objects and attributes
        self.gdf = gpd.GeoDataFrame(attributes, geometry=geometries, crs=crs)

class Result:
    '''
    A class to handle and process results for exporting to Excel.

    Attributes
    ----------
    path : str
        Path to the result file.
    data_dict : dict
        Dictionary containing result data.

    Methods
    -------
    create_data_dict(buildings, net, types, dn_list, heat_att, h_temp, l_temp):
        Creates a dictionary for the results to be used in Excel.
    create_df_from_dataDict(net_name='Netz'):
        Converts the dictionary to a result DataFrame.
    save_in_excel(col=0, index_bool=False, sheet_option='replace', sheet='Zusammenfassung'):
        Saves the DataFrame to an Excel sheet.
    '''

    def __init__(self,path):
        '''
        Initializes the Result class with the path to the result file.

        Parameters
        ----------
        path : str
            Path to the result file.
        '''
        self.path = path # Pfad zur Ergebnisdatei

    def create_data_dict(self, buildings, net, types, dn_list, heat_att, h_temp, l_temp):
        '''
        Creates a dictionary for the results to be used in Excel.

        Parameters
        ----------
        buildings : DataFrame
            DataFrame of buildings.
        net : DataFrame
            DataFrame of the network.
        types : list
            List of building types.
        dn_list : list
            List of possible pipe diameters.
        heat_att : str
            Attribute name for heat demand in the buildings DataFrame.
        h_temp : float
            Supply temperature.
        l_temp : float
            Return temperature.
        '''
        # Helper function
        def summarize_pipes(df,dn_list):
            '''
            Summarizes pipe lengths and losses in a DataFrame with all possible diameters.

            Parameters
            ----------
            df : DataFrame
                Input DataFrame.
            dn_list : list
                List of all possible diameters.
            '''
            result = pd.DataFrame({'DN':dn_list}, index = dn_list)
            result['Trassenlänge [m]'] = 0
            result['Verlust [MWh/a]'] = 0
            df = df.dropna(subset=['DN'])
            for idx, row in df.iterrows():
                i = int(row['DN'])
                result.loc[i, 'Trassenlänge [m]'] += row['length']
                result.loc[i, 'Verlust [MWh/a]'] += row['loss']
            return result
        
        # Accumulated building heat demand and count per load profile
        kum_b = buildings.groupby('Lastprofil').agg({heat_att: 'sum'}).reset_index()
        kum_b['count'] = buildings.groupby('Lastprofil').size().reset_index(name='count')['count']

        kum_b[heat_att]/=1000 #MW
        
        # Identify missing load profiles
        missing_types = set(types) - set(kum_b['Lastprofil'])

        if missing_types:
            # Create a DataFrame for missing types
            missing_df = pd.DataFrame({'Lastprofil': list(missing_types), 'count': 0, heat_att: 0})

            # Add missing types
            df = pd.concat([kum_b, missing_df], ignore_index=True)
        else:
            df = kum_b
        
        # Sort
        df_sorted = df.sort_values(by='Lastprofil', key=lambda x: x.map({val: i for i, val in enumerate(types)}))

        # power in MW
        gdf = net.copy()
        gdf['power_GLF']/=1000 #MW
        # Accumulated DN values
        kum_dn = gdf.groupby('DN').agg({'length': 'sum', 'loss': 'sum'}).reset_index()
        kum_dn['loss']/=1000 #MW

        # Length and loss of all diameters in chronological order
        length_loss = summarize_pipes(kum_dn,dn_list)

        data_dict = {}
        data_dict['Lastprofil'] = types
        data_dict['Anzahl'] = df_sorted['count'].tolist()
        data_dict['Wärmebedarf [MWh/a]'] = df_sorted[heat_att].tolist()
        data_dict['DN'] = dn_list
        data_dict['Trassenlänge [m]'] = length_loss['Trassenlänge [m]'].tolist()
        data_dict['Verlust [MWh/a]'] = length_loss['Verlust [MWh/a]'].tolist()
        data_dict['Vorlauftemp [°C]'] = [h_temp]
        data_dict['Ruecklauftemp [°C]'] = [l_temp]
        data_dict['Max. Leistung (inkl. GLF) [MW]'] = [gdf['power_GLF'].max()]
        data_dict['GLF'] = [calculate_GLF(sum(data_dict['Anzahl']))]

        self.data_dict = data_dict

    def create_df_from_dataDict(self,net_name='Netz'):
        '''
        Converts the dictionary to a result DataFrame.

        Parameters
        ----------
        net_name : str, optional
            Name of the network (default is 'Netz').
        '''
        # Convert the dictionary to a DataFrame
        df = pd.DataFrame.from_dict(self.data_dict, orient='index').transpose()

        # Sum selected columns and write the sum in one row
        sum_row = df[['Anzahl', 'Wärmebedarf [MWh/a]', 'Max. Leistung (inkl. GLF) [MW]', 'Trassenlänge [m]', 'Verlust [MWh/a]']].sum()
        sum_row['Lastprofil'] = 'Gesamt'
        df_sum = pd.DataFrame([sum_row], columns=['Lastprofil', 'Anzahl', 'Wärmebedarf [MWh/a]', 'Max. Leistung (inkl. GLF) [MW]', 'Trassenlänge [m]', 'Verlust [MWh/a]'], index=['Summe'])

        # Add the sum row to df
        df = pd.concat([df, df_sum])

        self.gdf = df

        # self.result_list.append(df)
        # sum_row['Typ']=net_name
        # self.sum_list.append(sum_row)
    
    def save_in_excel(self, col = 0, index_bool=False, sheet_option ='replace', sheet = 'Zusammenfassung'):
        '''
        Saves the DataFrame to an Excel sheet.

        Parameters
        ----------
        col : int, optional
            Starting column (default is 0).
        index_bool : bool, optional
            Whether to save the DataFrame with or without indices (default is False).
        sheet_option : str, optional
            Option for handling existing sheets ('replace', 'overlay', or 'new') (default is 'replace').
        sheet : str, optional
            Sheet name in the Excel file (default is 'Zusammenfassung').
        '''
        # Check if the file exists
        if os.path.exists(self.path):
            mode = 'a'  # # Append mode
            writer_args = {'if_sheet_exists': sheet_option}
        else:
            mode = 'w'  # # Write mode, creates a new file
            writer_args = {}

        # Open the Excel file in the appropriate mode and write the DataFrame to the specified sheet
        with pd.ExcelWriter(self.path, engine='openpyxl', mode=mode, **writer_args) as writer:
            self.gdf.to_excel(writer, sheet_name=sheet, index=index_bool, startcol=col)
        
        # Adjust column widths
        wb = load_workbook(filename = self.path)        
        ws = wb[sheet]
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter # Get the column name
            for cell in col:
                try: # Necessary to avoid error on empty cells
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length+1)
            ws.column_dimensions[column].width = adjusted_width
        wb.save(self.path)