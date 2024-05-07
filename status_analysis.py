import numpy as np
import geopandas as gpd

class WLD:
    def __init__(self,buildings,streets):
        self.buildings = buildings
        self.streets = streets

    def get_centroid(self):
        '''Fügt den Zentroid zu den Polygonen hinzu'''
        self.buildings['centroid'] = self.buildings['geometry'].centroid

    def closest_street_buildings(self):
        '''Ermittelt für jedes Gebäude die nächste straße (Anschlusspunkt) auf dem Linien-Netzwerk und die street-ID'''
        
        # def get_closest_point(line, point):
        #     '''Ermittelt den nächstgelegenen Punkt auf der Linie zu einem Punkt'''
        #     closest_point = line.interpolate(line.project(point))
        #     return closest_point
        
        # Iteration über jeden Polygon-Zentroiden
        for index, row in self.buildings.iterrows():
            centroid = row['centroid']

            # Finden der Linie, die dem Zentroiden am nächsten liegt
            closest_line = self.streets.geometry.distance(centroid).idxmin()

            # Ermitteln des nächsten Punktes auf dieser Linie
            # closest_point = get_closest_point(self.streets.at[closest_line, 'geometry'], centroid)
            #self.buildings.at[index, 'Anschlusspunkt'] = closest_point
            
            self.buildings.at[index, 'street_id'] = int(closest_line)

    def add_lenght(self):
        '''Fügt dem steets-gdf die Spalte 'Länge' hinzu'''
        self.streets['Länge'] = self.streets['geometry'].length

    def add_heat_att(self,heat_att):
        '''Fügt den Straßen den Wärmeverbrauch und die IDs der angeschlossenen Gebäude hinzu'''
        self.streets['connected'] = [[] for _ in range(len(self.streets))]
        self.streets[f'{heat_att}'] = 0

        for idx, row in self.buildings.iterrows():
            wvbr = row[heat_att]
            id = row['street_id']
            
            self.streets.loc[id, f'{heat_att}'] += wvbr
            self.streets.at[id, 'connected'].append(row['new_ID']) # ID wählen
            
        # Convert the list of polygons to a comma-separated string
        self.streets['connected'] = self.streets['connected'].apply(lambda x: ','.join(map(str, x)))
        

    def add_WLD(self, heat_att):
        '''Fügt die Wärmeliniendichte hinzu'''
        # Add 'HLD' field with Float data type
        self.streets['HLD'] = np.where(
            self.streets['Länge'] != 0, self.streets[f'{heat_att}'] / self.streets['Länge'], np.nan)
        
class Polygons:
    def __init__(self, parcels, hld, buildings):
        self.parcels = parcels
        self.hld = hld
        self.buildings = buildings
    
    def select_parcels_by_building_connection(self, HLD_value):
        # Filter HLD for values > HLD_value
        filtered_hld = self.hld[self.hld['HLD']>= HLD_value] 

        # Alle verbundenen Gebäude-IDs aus der 'connected'-Spalte extrahieren
        connected_building_ids = [int(id) for sublist in filtered_hld['connected'].dropna().str.split(',').tolist() if isinstance(sublist, list) for id in sublist]

        # Wählen Sie Gebäude aus, die in der Liste der verbundenen Gebäude-IDs enthalten sind
        connected_buildings = self.buildings[self.buildings['new_ID'].isin(connected_building_ids)]

        # Calculate area of building footprint
        connected_buildings['building_area'] = connected_buildings.geometry.area
        # index_left und index_right_entfernen
        if 'index_left' in self.parcels.columns:
            self.parcels = self.parcels.drop(columns=['index_left'])
        if 'index_right' in self.parcels.columns:
            self.parcels = self.parcels.drop(columns=['index_right'])

        if 'index_left' in connected_buildings.columns:
            connected_buildings = connected_buildings.drop(columns=['index_left'])
        if 'index_right' in connected_buildings.columns:
            connected_buildings = connected_buildings.drop(columns=['index_right'])

        # add identifier to remove duplicates
        self.parcels['identifier'] = range(len(self.parcels))

        # Räumlichen Verknüpfung durchführen: Überprüfen, welche Flurstücke Gebäude berühren
        join_result = gpd.sjoin(self.parcels, connected_buildings, how="inner", predicate="intersects")
        
        # Dissolve join_result based on the identifier column to remove duplicate geometries
        #join_result = join_result.dissolve(by='identifier')

        # Calculate area of overlap between parcels and buildings
        join_result['overlap_area'] = join_result.apply(lambda row: self.parcels.geometry.iloc[row.name].intersection(connected_buildings.geometry.iloc[row['index_right']]).area, axis=1)
        
        # Calculate coverage ratio
        join_result['coverage_ratio'] = join_result['overlap_area'] / join_result['building_area']
        
        # sort by coverage_ratio
        sorted_joined = join_result.sort_values(by='coverage_ratio', ascending=False)

        # keep only the row of a parcel with the max. 
        max_coverage = sorted_joined.groupby(sorted_joined.index).first()
        
        # Select parcels where the coverage ratio exceeds the threshold
        selected_parcels = max_coverage[max_coverage['coverage_ratio'] >= 0.1]

        # Spalte 'identifier' entfernen
        #selected_parcels = selected_parcels.drop(columns=['identifier'])

        # Spalte 'centroid' entfernen, damit es zum test als shape gespeichert werden kann
        selected_parcels = selected_parcels.drop(columns=['centroid'])
        
        self.selected_parcels = selected_parcels

    def buffer_dissolve_and_explode(self, buffer_distance):
        """
        Funktion, die einen Buffer um die Polygone in einer Shape-Datei anlegt, 
        sie dann verschmilzt und MultiPolygone in ihre Bestandteile aufteilt. 
        (d.h. man erhält nicht ein Feature als Multipolygon sondern mehrere Features jeweils als Polygon)
        
        Parameters:
        - input_path: Pfad zur Eingabe Shape-Datei.
        - buffer_distance: Distanz des Buffers in m.
        """

        # Buffer anlegen
        self.selected_parcels['geometry'] = self.selected_parcels.buffer(buffer_distance)
        
        # Zusammenführen (Dissolving) aller Polygone
        dissolved = self.selected_parcels.dissolve()

        # MultiPolygons in ihre Bestandteile aufteilen (Explodieren)
        exploded = dissolved.explode(index_parts=True).reset_index(drop=True)

        # Attribute entfernen und nur die Geometrie beibehalten
        self.polygons = exploded[['geometry']]

    def add_attributes(self,heat_attribute, power_attribute):

        # only buildings with heat demand
        buildings = self.buildings[self.buildings[heat_attribute]>0] 

        # add area
        self.polygons['Area'] = self.polygons['geometry'].area

        # add columns for attributes
        self.polygons['Connections'] = 0
        self.polygons['Heat_Demand'] = 0.0
        self.polygons['Power'] = 0.0

        for idx, polygon in self.polygons.iterrows():
            # buildings within polygon
            contained_buildings = buildings[buildings.geometry.within(polygon.geometry)]

            # connections in polygon
            self.polygons.loc[idx, 'Connections'] = len(contained_buildings)

            # cumulated heat demand
            self.polygons.loc[idx, 'Heat_Demand'] = contained_buildings[heat_attribute].sum()
            
            # accumulated power
            self.polygons.loc[idx,'Power'] = contained_buildings[power_attribute].sum()
        
        # heat deman per area 
        self.polygons['Demand/Area[MWh/ha]'] = 10 * self.polygons['Heat_Demand'] / self.polygons['Area'] # 1000 kW 10000 m^2 in 1 MW 1 ha
        
        # mean power
        self.polygons['Mean_Power'] = self.polygons['Power'] / self.polygons['Connections']