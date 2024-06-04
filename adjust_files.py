import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString,MultiLineString
import re
from collections import Counter
import numpy as np

class Streets_adj():
    def __init__(self, path, projected_crs):
        self.gdf = gpd.read_file(path, crs=projected_crs)
        
    def round_streets(self):
        '''Koordinaten runden'''
        # Hilfsfunktionen
        def convert_multilinestring_to_linestring(geometry, x):
            """
            Überprüft, ob es sich bei der Geometrie um einen MultiLineString handelt
            und wandelt diesen in einen LineString um.
            """
            if isinstance(geometry, MultiLineString):
                x += 1
                return LineString(list(geometry.geoms)[0].coords), x
            else:
                return geometry, x

        def round_coordinates(line):
            '''
            Rundet die Koordinaten der Punkte im LineString auf 3 Nachkommastellen.
            line: LineString-Objekt
            Rückgabe: gerundetes LineString-Objekt
            '''
            rounded_coords = [(round(x, 3), round(y, 3)) for x, y in line.coords]
            return LineString(rounded_coords)

        streets = self.gdf
        x = 0
        streets['geometry'], x = zip(*streets['geometry'].apply(lambda geom: convert_multilinestring_to_linestring(geom, x)))
        streets['geometry'] = streets['geometry'].apply(round_coordinates)
        
        if max(x) > 0:
            print('Bei mindestens einer Geometrie der Straßen handelt es sich um einen Multilinestring! \nEs wird mit dem ersten Linestring als Straße weitergerechnet. \nggf. Straßengeometrie prüfen.')
        self.gdf = streets 
    
    def add_bool_column(self):
        self.gdf['possible_route'] = 1

class Buildings_adj():
    def __init__(self, path, heat_att, projected_crs):
        self.gdf = gpd.read_file(path, crs=projected_crs)
        self.heat_att = heat_att

    def add_Vlh_Loadprofile(self, excel_data):
        '''Volllastunden und Lastprofil hinzufügen'''
        buildings = self.gdf
        excel_data['Funktion'] = excel_data['Funktion'].astype(str)
        buildings['GFK_last_four'] = buildings['citygml_fu'].str[-4:]
        buildings = buildings.merge(excel_data[['Funktion', 'Lastprofil', 'Vlh']], left_on='GFK_last_four', right_on='Funktion', how='left')

        # Löschen der temporären Spalte und der 'Funktion'-Spalte
        buildings.drop(columns=['GFK_last_four'], inplace=True)

        try:
            buildings.drop(columns=['Funktion'], inplace=True)
        except:
            buildings.drop(columns=['Funktion_y'], inplace=True)
        self.gdf = buildings

    def drop_unwanted(self):
        b = self.gdf
        b = b[b['Lastprofil'].notna()] # alle Gebäude entfernen, die kein Lastprofil zugeschrieben bekommen, da das oft Gebäude sind die wir nicht wollen oder sonstige Fehler haben
        b = b.copy() # unterdrückt eine falsche Warnung
        #b.loc[:,'count'] = 1 # ist für die Zusammenfassung wichtig
        self.gdf = b

    def add_power(self):
        buildings = self.gdf
        '''Leistung hinzufügen'''
        buildings['power'] = buildings[self.heat_att] / buildings['Vlh'].where(buildings['Vlh'] != 0, 1600) # Falls 0 VLH eingetragen sind wird mit 1600 gerechnet
        self.gdf = buildings
    
    @staticmethod
    def extract_year(date_str):
        if pd.notna(date_str):
            return int(date_str[:4])
        return np.nan

    def add_BAK(self,bins,labels):
        #self.gdf['jahr'] = self.gdf['validFrom'].str[:4].astype(int)
        
        # Nur die Zeilen auswählen, in denen validFrom nicht NaN ist, und die Umwandlung durchführen
        self.gdf['jahr'] = self.gdf['validFrom'].apply(self.extract_year)

        self.gdf['BAK'] = pd.cut(self.gdf['jahr'], bins=bins, labels=labels, right=True)
        self.gdf['BAK'] = self.gdf['BAK'].astype(str)
        self.gdf.drop(columns=['jahr'], inplace = True)

    def add_age_LANUV(self):
        def extract_age(building_type):
            '''help function to extract the age from buildings'''
            match = re.search(r'_(\d+)$', building_type)
            if match:
                return int(match.group(1))
            else:
                return None
            
        # Spalte 'Altersklasse' hinzufügen
        self.gdf['Alter_LANUV'] = self.gdf['GEBAEUDETY'].apply(extract_age)
    
    def merge_buildings(self):
        # Aggregationsfunktionen
        def custom_agg_mix_str(s):
            unique_vals = s.unique()
            if len(unique_vals) == 1:
                return unique_vals[0]
            else:
                return 'mix'
            
        def custom_agg_mix_numeric(s):
            unique_vals = s.unique()
            if len(unique_vals) == 1:
                return unique_vals[0]
            else:
                return None 
            
        def custom_agg_most_common(s):
            most_common = s.mode()
            if len(most_common) > 0:
                return most_common.iloc[0]
            else:
                return s.iloc[0]  # Für den Fall, dass es keine wiederholten Werte gibt (sollte in der Praxis nicht vorkommen, ist aber eine Absicherung)

        def mode_or_string(x):
            '''help function to aggregate the most common value or values'''
            counts = Counter(x)
            max_count = max(counts.values())
            max_list = [val for val, count in counts.items() if count == max_count]
            if len(max_list) == 1:
                return str(max_list[0])
            else:
                sorted_list = sorted(max_list)  # Sortiere die Liste
                return ', '.join(map(str, sorted_list))
            
        grouped_gdf = self.gdf.dissolve(by=['Flurstueck', 'citygml_fu', 'Fortschrei'], as_index=False, aggfunc={
            'Fest_ID': 'first', 
            'Nutzung': 'first',  
            'RW': 'sum', 
            'WW': 'sum',
            'RW_WW': 'sum',
            'Block_ID': custom_agg_mix_numeric,
            'Flur_ID': custom_agg_mix_numeric,
            'Gemarkung_': 'first',
            'AGS': 'first',
            'Kreis': 'first',
            'validFrom' : 'first',
            'BAK': mode_or_string,
            'Alter_LANUV': mode_or_string,
            'Lastprofil': 'first',
            'Vlh': 'first',
            'power': 'sum',
            'new_ID': 'first'})
        self.gdf = grouped_gdf

class Parcels_adj():
    def __init__(self, path, projected_crs):
        self.gdf = gpd.read_file(path, crs=projected_crs)

def spatial_join(shape1, shape2, attributes):
        '''
        searches best fitting feature and adds attribute from shape2 to shape1
        attributes: List of attributes
        '''
        # Überprüfen, ob Spalten index_left und index_right vorhanden sind und sie gegebenenfalls entfernen
        if 'index_left' in shape1.columns:
            shape1 = shape1.drop(columns=['index_left'])
            print('index_left was removed from shape1 to execute the spatial join')
        if 'index_right' in shape1.columns:
            shape1 = shape1.drop(columns=['index_right'])
            print('index_right was removed from shape1 to execute the spatial join')
        if 'index_left' in shape2.columns:
            shape2 = shape2.drop(columns=['index_left'])
            print('index_left was removed from shape2 to execute the spatial join')
        if 'index_right' in shape2.columns:
            shape2 = shape2.drop(columns=['index_right'])
            print('index_right was removed from shape2 to execute the spatial join')

        # Räumlichen Join durchführen
        joined = gpd.sjoin(shape1, shape2, how='inner', predicate='intersects')

        # Schnittfläche für jedes überlappende Paar berechnen
        joined['intersection_area'] = joined.apply(lambda row: shape1.geometry.iloc[row.name].intersection(shape2.geometry.iloc[row['index_right']]).area, axis=1)

        # Ergebnisse basierend auf der Schnittfläche sortieren
        sorted_joined = joined.sort_values(by='intersection_area', ascending=False)

        # Den Eintrag mit der größten Schnittfläche für jedes Gebäude-Feature behalten
        max_intersection = sorted_joined.groupby(sorted_joined.index).first()

        # Attribute übertragen
        for attr in attributes:
            try:
                shape1[attr] = max_intersection[attr]
            except:
                shape1[attr] = max_intersection[(attr+'_left')]
                print(f'{attr} got updated during spatial join')

        return shape1