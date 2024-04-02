import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, LineString
import networkx as nx
import matplotlib.pyplot as plt
from openpyxl import load_workbook
from openpyxl.drawing.image import Image
import subprocess
import sys

def get_closest_point(line, point):
    '''Ermittelt den nächstgelegenen Punkt auf der Linie zu einem Punkt'''
    closest_point = line.interpolate(line.project(point))
    return closest_point

def calculate_GLF(n):
    '''
    Gleichzeitigkeitsfaktor berechnen
    n: Anzahl Gebäude
    '''
    a = 0.4497
    b = 0.5512
    c = 53.8483
    d = 1.7627
    return a + (b / (1 + pow(n/c, d)))

def calculate_volumeflow(kW_GLF, htemp, ltemp):
    '''
    Berechnet den Volumenstrom in einer Rohrleitung
    kW_GLF: Leistung mit Gleichzeitigkeitsfaktor
    htemp: Vorlauftemperatur
    ltemp: Rücklauftemperatur
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
    Berechnet Durchmesser, Geschwindigkeit und Verlust der Rohrleitungen
    volumeflow: Volumenstrom
    htemp: Vorlauftemperatur
    ltemp: Rücklauftemperatur
    path_to_excel: Exceldatei mit Informationen zu den Rohrleitungen
    '''
    DN_list = pipe_info['DN']   # Liste der  Nenndurchmesser
    di_list = pipe_info['di']   # Liste der Innendurchmesser
    U_list = pipe_info['U-Wert'] # Liste der Wärmeübergangskoeffizienten
    v_list = pipe_info['Geschwindigkeit'] # Liste der max. Geschwindigkeit je Rohr

    mtemp = (htemp+ltemp)/2
    K = mtemp - 10  # Außentemperatur wird als 10°C angenommen (unterirdische Installation)

    vtemp = []
    for i,d_i in enumerate(di_list):
        r = d_i/2
        v = volumeflow * 1000 / (np.pi *  pow(r,2)) # dm^3/mm^2 --> Faktor 1000
        vtemp.append(v)

        if v <= v_list[i]:
            break
    else:  
        v = min(vtemp, key=lambda x: abs(x-1))
        i = vtemp.index(v)

    loss = 8760 * 2 * (U_list[i] * K * length) / 1000 # 8760 Stunden im Jahr, 2* wegen Vor- und Rücklauf 
    DN = DN_list[i] # Außendurchmesser

    return DN, v, loss

class Streets:
    def __init__(self, path):
        self.gdf = gpd.read_file(path)

    def add_connection_to_streets(self, buildings, sources):
        '''
        Anschlusspunkte in die Straßenlinien einfügen
        buildings: Geodataframe mit den Gebäuden
        streets: Geodataframe mit den Straßen
        sources: Geodataframe mit den Energiequellen
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

                    # Einfügeposition in der Linie finden
                    for i in range(1, len(line_coords)):
                        segment = LineString([line_coords[i-1], line_coords[i]])
                        distance = segment.distance(anschlusspunkt)

                        if distance < min_distance:
                            min_distance = distance
                            insertion_position = i

                    # Fügen Sie den ursprünglichen Anschlusspunkt in die Linienkoordinaten ein
                    if (anschlusspunkt.x, anschlusspunkt.y) not in line_coords:
                        line_coords.insert(insertion_position, (anschlusspunkt.x, anschlusspunkt.y))
                        self.gdf.at[street_id, 'geometry'] = LineString(line_coords)

class Source:
    def __init__(self, path):
        self.primary = gpd.read_file(path)
        self.gdf = gpd.read_file(path)  # hier werden im Verlauf die zusätzlichen Heizzentralen hinzugefügt, falls mit unterschiedlichen Gebieten gerechnet wird.

    def closest_points_sources(self, streets):
        '''
        Ermittelt für jede Quelle den nächsten Punkt (Anschlusspunkt) auf dem Straßennetz sowie die street-ID und fügt diese dem gdf hinzu
        streets: Geodataframe mit den Straßen
        '''
        # Iteration über jede Quelle und Suche des nächstgelegenen Punkts auf dem Linien-Netzwerk
        for index, row_s in self.gdf.iterrows():

            # Initialisieren der Variablen für den minimalen Abstand und den nächstgelegenen Punkt
            min_distance = float('inf')
            closest_point = None
            source = row_s['geometry']

            # Iteration über jede Linie im Linien-Netzwerk
            for idx,row in streets.iterrows():
                line_coords = list(row['geometry'].coords)  # Liste der Punkte, aus denen die Linie besteht
                
                # Iteration über jeden Linienabschnitt, um den nächstgelegenen Punkt zu finden
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
    def __init__(self, path, heat_att):
        self.buildings_all = gpd.read_file(path)
        
        # Nur Gebäude mit Wärmeverbrauch
        try:
            buildings_wvbr = self.buildings_all[self.buildings_all[heat_att]>0] 
        except:
            print('wvbr_att überprüfen!')

        self.gdf = buildings_wvbr
    
    def add_centroid(self):
        '''
        Fügt den Zentroid zu den Polygonen hinzu
        polygons: DataFrame der Polygon-Shapefile-Daten
        '''
        self.gdf = self.gdf.copy() # Damit keine Warnung kommt
        self.gdf['centroid'] = self.gdf.loc[:, 'geometry'].centroid

    def closest_points_buildings(self, streets):
        '''
        Ermittelt für jedes Polygon den nächsten Punkt (Anschlusspunkt) auf dem Straßennetz sowie die street-ID und fügt diese dem gdf hinzu
        streets: Geodataframe mit den Straßen
        '''
        # räumlichen Index für die Linien erstellen
        sindex = streets.sindex

        # Iteration über jeden Polygon-Zentroiden
        for index, row_p in self.gdf.iterrows():
            centroid = row_p['centroid']

            # Verwenden Sie den räumlichen Index, um die nächstgelegenen Linien zum Zentroiden zu erhalten
            possible_matches_index = list(sindex.nearest(centroid))
            possible_matches = streets.iloc[[i[0] for i in possible_matches_index]]

            # Finden Sie die Linie, die dem Zentroiden am nächsten liegt
            closest_line = possible_matches.geometry.distance(centroid).idxmin()

            # Ermitteln Sie den nächsten Punkt auf dieser Linie
            closest_point = get_closest_point(streets.at[closest_line, 'geometry'], centroid)

            self.gdf.loc[index, 'Anschlusspunkt'] = closest_point
            self.gdf.loc[index, 'street_id'] = int(closest_line)

class Graph:
    def __init__(self):
        # Graph erstellen
        self.graph = nx.Graph()
        
    def create_street_network(self, streets):
        '''
        Graph (Straßen-Netzwerk) erstellen, Knoten und Kannten hinzufügen
        streets: Geodataframe mit den Straßen
        '''
        # Dictionary mit den Attributen, das die edge haben soll
        edge_data = {'Typ': 'Straßenleitung'}  

        # Knoten hinzufügen
        for idx, row in streets.iterrows():
            geom = row['geometry']
            line_coords = list(geom.coords)

            # Iteration über jeden Punkt auf der Linie
            for i in range(len(line_coords)):
                node = line_coords[i]
                self.graph.add_node(node)

                # Verbindung zu vorherigem Punkt (außer beim ersten Punkt)
                if i > 0:
                    prev_node = line_coords[i-1]
                    self.graph.add_edge(node, prev_node,**edge_data)
    
    def connect_centroids(self, buildings):
        '''
        Fügt die Zentroiden der Gebäude zum Netz G hinzu
        G: networky-Graph
        buildings: Geodataframe mit den Gebäuden
        '''
        for index, row in buildings.iterrows():
            centroid = row['centroid']
            closest_point = row['Anschlusspunkt']
            if not pd.isna(closest_point):
                edge_data = {'Typ': 'Hausanschluss'}  # Dictionary mit dem Attribut, das die edge haben soll
                self.graph.add_edge(centroid.coords[0], (closest_point.x, closest_point.y), **edge_data)

    def connect_source(self, sources):
        '''
        Fügt Energiequellen dem Netz G hinzu
        G: networkx-Graph
        sources: Geodataframe mit den Energiequellen
        '''
        for index, row in sources.iterrows():
            source = row['geometry']
            closest_point = row['Anschlusspunkt']
            if not pd.isna(source):
                edge_data = {'Typ': 'Quellenanschluss'}  # Dictionary mit dem Attribut, das die edge haben soll
                self.graph.add_edge(source.coords[0], (closest_point.x, closest_point.y), **edge_data)

    def add_attribute_length(self):
        '''Kantenattribut Länge zu G hinzufügen'''
        for node1, node2 in self.graph.edges():
            geom = LineString([node1, node2])
            self.graph.edges[node1, node2]['length'] = geom.length

    def plot_G(self):

        # Koordinatensystem festlegen
        pos = {node: (node[0], node[1]) for node in self.graph.nodes}

        # Graph anzeigen
        plt.figure()
        plt.title('Graph')
        nx.draw_networkx(self.graph, pos=pos, with_labels=False, font_size=6, node_size=3, node_color='blue', edge_color='gray')
        plt.show()

    def test_connection(self, source):
        def get_connected_points(G, input_point):
            '''
            Ermittelt die mit dem Eingabepunkt verbundenen Punkte im Graphen G.
            G: Graph
            input_point: Eingabepunkt
            '''
            # Überprüfung der Existenz des Eingabepunkts im Graphen
            if input_point not in G.nodes:
                print("Eingabepunkt nicht im Graphen enthalten.")
                return []

            # Ermitteln der verbundenen Punkte mithilfe von zusammenhängenden Komponenten
            for component in nx.connected_components(G):
                if input_point in component:
                    return list(component - {input_point})  # Entfernen des input_point aus den verbundenen Punkten

            return []

        def plot_graph(G, input_point, connected_points):
            '''
            Plot des Graphen mit eingefärbten verbundenen Punkten.
            G: Graph
            input_point: Eingabepunkt
            connected_points: Liste der verbundenen Punkte
            '''
            pos = {node: (node[0], node[1]) for node in G.nodes}

            # Knoten einfärben
            node_colors = ['blue' if node == input_point else 'red' for node in G.nodes]

            # Verbundene Punkte einfärben
            for node in connected_points:
                node_colors[list(G.nodes).index(node)] = 'green'

            # Graph plotten
            plt.figure(figsize=(20, 20))
            nx.draw(G, pos, node_color=node_colors, font_size=6, node_size=10, with_labels=False)
            plt.show()

        start_point = (source['geometry'][0].x, source['geometry'][0].y)
        connected_points = get_connected_points(self.graph, start_point)
        plot_graph(self.graph, start_point, connected_points)

    def graph_to_gdf(self): # Methode ist ebenfalls in Net. Klassen zusammenfügen? --> Wegen übersichtlichkeit erstmal nicht
        """Konvertiert einen networkx-Graphen in ein GeoDataFrame, wobei auch die Kantenattribute übernommen werden."""
        geometries = []
        attributes = {}

        for u, v, data in self.graph.edges(data=True):
            geometries.append(LineString([u, v]))

            # Sammeln Sie Attribute für jede Kante
            for key, value in data.items():
                if key in attributes:
                    attributes[key].append(value)
                else:
                    attributes[key] = [value]

        # Erstellen Sie ein GeoDataFrame aus den LineString-Objekten und den Attributen
        self.gdf = gpd.GeoDataFrame(attributes, geometry=geometries, crs='EPSG:25832')

    def save_nodes_to_shapefile(self, filename):
        """
        Speichert Knoten eines Graphen als Punkte in einem Shapefile. 
        Jeder Punkt wird mit dem Grad des Knotens und seinen Koordinaten annotiert.
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
    def __init__(self, htemp, ltemp):
        self.net = nx.Graph()
        self.htemp = htemp
        self.ltemp = ltemp

    def update_attribute(self, u, v, attribute, name):
        '''
        Fügt ein Attribut zu einer Kante in einem Netzwerkgraphen hinzu oder aktualisiert es.
        net (networkx.Graph): Der Netzwerkgraph.
        u, v (node): Knoten, die die Kante definieren.
        attribute (any): Wert des Attributs.
        name (str): Name des Attributs.
        '''
        if name in self.net.edges[u, v]:
            self.net.edges[u, v][name] += attribute
        else:
            self.net.edges[u, v][name] = attribute

    def add_edge_attributes(self, pipe_info):
        '''
        Fügt den Kanten des Netzes Attribute hinzu:
            GLF
            power_GLF
            Volumeflow
            DN
            velocity
            loss
        net: networkx-Graph
        path_to_excel: Exceldatei mit Informationen zu den Rohrleitungen
        htemp: Vorlauftemperatur
        ltemp: Rücklauftemperatur
        '''
        for (u, v, data) in self.net.edges(data=True):
            n_building = data['n_building']
            power = data['power']
            length = data['length']

            GLF = calculate_GLF(n_building)
            power_GLF = power * GLF
            volumeflow = calculate_volumeflow(power_GLF, self.htemp, self.ltemp)
            

            diameter, velocity, loss = calculate_diameter_velocity_loss(volumeflow, self.htemp, self.ltemp, length, pipe_info)
            
            # Attribute den Kanten hinzufügen
            data['GLF'] = GLF
            data['power_GLF'] = power_GLF
            data['Volumeflow'] = volumeflow
            data['DN'] = diameter
            data['velocity'] = velocity
            data['loss'] = loss

    def network_analysis(self, G, buildings, sources, pipe_info, power_att, weight='length'):
        '''Berechnet das Netz, indem der kürzeste Pfad zu jedem Gebäude gesucht wird'''

        start_point = (sources['geometry'][0].x, sources['geometry'][0].y)

        for idx, row in buildings.iterrows():
            
            # Attribute des aktuellen Gebäudes deklarieren
            end_point = (row['centroid'].x, row['centroid'].y)
            b1 = G.has_node(start_point)
            b2 = G.has_node(end_point)
            power = row[power_att]
            buildings_count = 1
            try:
                # Kürzesten Pfad berechnen
                path = nx.shortest_path(G, start_point, end_point, weight=weight)
            
            
                # Hinzufügen der Knoten und Kanten des Pfades zum Netzwerkgraphen
                for i in range(len(path) - 1):
                    u, v = path[i], path[i+1]

                    # Kopiere alle Kantenattribute
                    self.net.add_edge(u, v, **G.edges[u, v]) # hier steht self.net, weil das gar keine Funktion von mir ist

                    # Aktualisiere die Attribute
                    self.update_attribute(u, v, power, 'power')    # Leistung
                    self.update_attribute(u, v, buildings_count, 'n_building') # Anzahl versorgter Gebäude an dieser Leitung
            except Exception as e: 
                print(f'Keine Verbindung für:\n{row}')
                print(f'Fehler {e}')
                sys.exit()
            
        # GLF, Durchmesser, Geschwindigkeit und Verlust hinzufügen 
        self.add_edge_attributes(pipe_info)      

    def network_analysis_hz(self, G, buildings, sources, polygons, hz, pipe_info, power_att, weight='length'):
        '''Berechnet das Verbundnetz der Heizzentralen'''

        start_point = (sources['geometry'][0].x, sources['geometry'][0].y)

        for i in range(0, len(polygons)):
            # Verwendet den Index i, um auf die Polygone und Heizzentralen zuzugreifen
            current_polygon = polygons[i]
            current_hz = hz[i]
            current_buildings = buildings[buildings.within(current_polygon.iloc[0].geometry)].copy()

            for idx, row in current_buildings.iterrows():
                end_point = (current_hz['geometry'][0].x, current_hz['geometry'][0].y) # !!! Wenn hier was geändert wird, dann muss beachtet werden, dass die Ergebnisdarstellung in Excel beeinflusst wird (siehe Result.result())
                
                # Attribute deklarieren
                power = row[power_att]
                buildings_count = 1
                try:
                    path = nx.shortest_path(G, start_point, end_point, weight)
                
                    # Hinzufügen der Knoten und Kanten des Pfades zum Netzwerkgraphen
                    for i in range(len(path) - 1):
                        u, v = path[i], path[i+1]

                        # Kopiere alle Kantenattribute
                        self.net.add_edge(u, v, **G.edges[u, v])

                        # Aktualisiere die Attribute
                        self.update_attribute(u, v, power, 'power')    # Leistung
                        self.update_attribute(u, v, buildings_count, 'n_building') # Anzahl versorgter Gebäude an dieser Leitung
                except Exception as e: 
                    print(f'Keine Verbindung für:\n{row}')
                    print(f'Fehler {e}')
                    sys.exit()
            
        # GLF, Durchmesser, Geschwindigkeit und Verlust hinzufügen 
        self.add_edge_attributes(pipe_info)      

    def plot_network(self, streets, buildings, sources, filename, title='Straßennetzwerk und berechnetes Netz'):
        '''
        Zeigt das Straßennetzwerk, die Gebäude und das berechnete Netz net an und speichert das Bild
        streets: Straßennetzwerk
        net: Berechnetes Netz
        buildings: GeoDataFrame der Gebäude
        sources: GeoDataFrame der Energiequellen
        filename: Name unter dem das Bild gespeichert wird
        title: Überschrift des Plots
        '''
        # Positionen der Knoten
        pos = {node: (node[0], node[1]) for node in self.net.nodes}

        # Figure und Axes erstellen
        fig, ax = plt.subplots(figsize=(15, 15))

        # Straßen zeichnen
        streets.plot(ax=ax, edgecolor='gray', zorder=1)

        # Gebäude zeichnen
        buildings.plot(ax=ax, facecolor='#ff8888', edgecolor='black', zorder=2)

        # Energiequelle als Punkt zeichnen
        sources.plot(ax=ax, marker='o', markersize=15, color='green', zorder=3)

        # Netz zeichnen
        nx.draw_networkx_edges(self.net, pos=pos, ax=ax, edge_color='blue', width=1.0)

        # Raster und Achsentitel aktivieren
        #ax.grid(True)
        ax.set_title(title)

        # Plot speichern
        plt.savefig(filename, bbox_inches='tight')

        # Plot anzeigen
        plt.show()

    def ensure_power_attribute(self):
        """
        Stellt sicher, dass jede Kante im Graphen das Attribut 'power' hat.
        Wenn eine Kante das Attribut nicht hat, wird es mit dem Wert 0 initialisiert.
        """
        for u, v in self.net.edges():
            if 'power' not in self.net[u][v]:
                self.net[u][v]['power'] = 0

    def graph_to_gdf(self, crs = 'EPSG:25832'):
        """Konvertiert einen networkx-Graphen in ein GeoDataFrame, wobei auch die Kantenattribute übernommen werden.
        crs: Koordinatensystem"""
        geometries = []
        attributes = {}

        for u, v, data in self.net.edges(data=True):
            geometries.append(LineString([u, v]))

            # Sammeln Sie Attribute für jede Kante
            for key, value in data.items():
                if key in attributes:
                    attributes[key].append(value)
                else:
                    attributes[key] = [value]

        # Erstellen Sie ein GeoDataFrame aus den LineString-Objekten und den Attributen
        self.gdf = gpd.GeoDataFrame(attributes, geometry=geometries, crs=crs)

class Result:
    def __init__(self,path):
        self.result_list = [] # Liste der Ergebnisse [Netz1, Netz2,..., Zusammenfassung, Vergleich]
        self.sum_list = [] # Liste für Dummenliste der Netze (benötigt für Vergleich)
        self.excel_path = path # Pfad zur Ergebnisdatei

    def create_data_dict(self, buildings, net, types, dn_list, heat_att, h_temp, l_temp):
        '''
        Legt ein dictionary für die Ergebnisse in excel an
        buildings: Gebäude data frame
        net: Netz-Graph
        types: Gebäudetypen
        dn_list: Liste mit möglichen Rohrurchmessern
        '''
        def summarize_pipes(df,dn_list):
            '''
            Fasst die Leitungslängen und Verluste in einem Dataframe mit allen möglichen Durchmessern zusammen
            df: Eingngsdataframe
            dn_list: Liste mit allen möglichen Durchmessern
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
        
        # Kumulierte Gebäude. Wärmebedarf und Anzahl pro Lastprofil
        
        #kum_b = buildings.groupby('Lastprofil').agg({wvbr_att: 'sum', 'count': 'sum'}).reset_index()
        kum_b = buildings.groupby('Lastprofil').agg({heat_att: 'sum'}).reset_index()
        kum_b['count'] = buildings.groupby('Lastprofil').size().reset_index(name='count')['count']


        kum_b[heat_att]/=1000 #MW
        
        # Fehlende Lastprofile identifizieren
        missing_types = set(types) - set(kum_b['Lastprofil'])

        if missing_types:
            # Erstelle ein DataFrame für fehlende Typen
            missing_df = pd.DataFrame({'Lastprofil': list(missing_types), 'count': 0, heat_att: 0})

            # Füge fehlende Typen hinzu
            df = pd.concat([kum_b, missing_df], ignore_index=True)
        else:
            df = kum_b
        
        # Sortieren
        df_sorted = df.sort_values(by='Lastprofil', key=lambda x: x.map({val: i for i, val in enumerate(types)}))

        # Netz-Graph zu df
        gdf = net.gdf.copy()
        gdf['power_GLF']/=1000 #MW
        # Kumulierte DN-Werte
        kum_dn = gdf.groupby('DN').agg({'length': 'sum', 'loss': 'sum'}).reset_index()
        kum_dn['loss']/=1000 #MW

        # Länge und Verlust aller Durchmesser in chronologischer Reihenfolge
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
        '''Wandelt das Dictionary in das Ergebnis-DataFrame um.'''
        
        # Konvertiert das Dictionary in einen DataFrame
        df = pd.DataFrame.from_dict(self.data_dict, orient='index').transpose()

        # Summiert die ausgewählten Spalten und schreibt Summen in eine Zeile
        sum_row = df[['Anzahl', 'Wärmebedarf [MWh/a]', 'Max. Leistung (inkl. GLF) [MW]', 'Trassenlänge [m]', 'Verlust [MWh/a]']].sum()
        sum_row['Lastprofil'] = 'Gesamt'
        df_sum = pd.DataFrame([sum_row], columns=['Lastprofil', 'Anzahl', 'Wärmebedarf [MWh/a]', 'Max. Leistung (inkl. GLF) [MW]', 'Trassenlänge [m]', 'Verlust [MWh/a]'], index=['Summe'])

        # Fügt die Summenzeile zu df hinzu
        df = pd.concat([df, df_sum])

        self.result_list.append(df)
        sum_row['Typ']=net_name
        self.sum_list.append(sum_row)
    
    def safe_in_excel(self, col = 0, index_bool=False, sheet_option ='replace', sheet = 'Zusammenfassung'):
        '''
        Speichert das DataFrame df in einer Exceltabelle unter filename
        df: DataFrame
        col: Startspalte
        index_bool: einstellen, ob das df mit oder ohne indices gespeichert werden soll
        filename: Pfad der Exceldatei
        sheet: Sheet der Exceldatei in dem gespeichert werden soll
        '''
        # Öffnet die existierende Excel-Datei und schreibt den letzten(neuesten) DataFrame der Liste in das angegebene Sheet
        with pd.ExcelWriter(self.excel_path, engine='openpyxl', mode='a', if_sheet_exists=sheet_option) as writer:
            self.result_list[-1].to_excel(writer, sheet_name=sheet, index=index_bool, startcol=col)

        # Zellgrößen anpassen
        wb = load_workbook(filename = self.excel_path)        
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
        wb.save(self.excel_path)
    
    def result(self):
        '''Fügt die einzelnen Ergebnisse der Netze zu einem Ergebnis-DataFrame zusammen'''
        result = self.result_list[-1]
        for df in self.result_list[:-1]:
            result['Trassenlänge [m]'] += df['Trassenlänge [m]']
            result['Verlust [MWh/a]'] += df['Verlust [MWh/a]']
        self.result_list.append(result)

    def compare_nets(self):
        '''Vergleicht die Zusammenfassungen der Netze'''
        # Dictionary und indices für die Zusammenfassung1 Erstellen
        z = {
            'Anschlussnehmer':['[n]'],
            'Trassenlänge':['[km]'],
            'Wärmebedarf':['[MWh/a]'],
            'Verlust':['MWh/a'],
            'Gesamtwärmebedarf':['MWh/a'],
            'Max. Leistung (inkl. GLF)':['MW']
        }
        indices = ['Einheit']
        
        for item in self.sum_list:
            z['Anschlussnehmer'].append(item['Anzahl'])
            z['Trassenlänge'].append(item['Trassenlänge [m]']/1000)
            z['Wärmebedarf'].append(item['Wärmebedarf [MWh/a]'])
            z['Verlust'].append(item['Verlust [MWh/a]'])
            z['Gesamtwärmebedarf'].append(item['Wärmebedarf [MWh/a]']+item['Verlust [MWh/a]'])
            z['Max. Leistung (inkl. GLF)'].append(item['Max. Leistung (inkl. GLF) [MW]'])
            indices.append(item['Typ'])
        
        self.result_list.append(pd.DataFrame(z,index=indices))

    def embed_image_in_excel(self, sheet_name, image_filename, row, col):
        # Laden Sie die vorhandene Excel-Datei
        workbook = load_workbook(self.excel_path)

        # Holen Sie sich das Arbeitsblatt
        worksheet = workbook[sheet_name]

        # Fügen Sie das Bild in das Excel-Sheet ein
        img = Image(image_filename)
        worksheet.add_image(img, f'{chr(65 + col)}{row + 1}')

        # Speichern Sie die Excel-Datei
        workbook.save(self.excel_path)

    def open_excel_file(self):
        try:
            subprocess.Popen(['start', 'excel', self.excel_path], shell=True)
        except Exception as e:
            print(f"Fehler beim Öffnen der Excel-Datei: {e}")

    def project_area_map(self, buildings,streets,filename='../Projektgebiet.png'):

        fig, ax = plt.subplots(figsize=(5, 5))

        buildings.plot(ax=ax, color='black', edgecolor='black')
        streets.plot(ax=ax, color='grey', linewidth = 1)

        ax.axis('off')

        plt.savefig(filename, bbox_inches='tight')
        plt.show()
