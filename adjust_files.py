import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString,MultiLineString
import re
from collections import Counter
import numpy as np

class Streets_adj():
    '''
     A class used to represent and manipulate street geometries.

    This class provides methods to round the coordinates of street geometries and to add a boolean column
    indicating possible routes.

    Attributes
    ----------
    gdf : GeoDataFrame
        A GeoDataFrame containing the street geometries.

    Methods
    -------
    round_streets():
        Rounds the coordinates of street geometries to 3 decimal places.
        
    add_bool_column():
        Adds a boolean column indicating possible routes.
    '''

    def __init__(self, path, projected_crs):
        '''
        Initializes the Streets_adj class with a GeoDataFrame of street geometries.

        Parameters
        ----------
        path : str
            The file path to the shapefile containing the street geometries.
        projected_crs : str
            The coordinate reference system to be used for the GeoDataFrame.
        '''
        self.gdf = gpd.read_file(path, crs=projected_crs)
        
    def round_streets(self):
        '''
        Rounds the coordinates of street geometries to 3 decimal places.

        This method processes the geometries in the GeoDataFrame, converting any MultiLineString geometries
        to LineString geometries, and then rounds their coordinates to 3 decimal places.

        Notes
        -----
        - If any MultiLineString geometries are found, they are converted to LineString geometries by taking
          the first component of the MultiLineString.
        - A warning is printed if any MultiLineString geometries are found and processed.
        '''
        # Helper functions
        def convert_multilinestring_to_linestring(geometry, x):
            '''
            Converts a MultiLineString geometry to a LineString geometry.

            Parameters
            ----------
            geometry : shapely.geometry.MultiLineString or shapely.geometry.LineString
                The geometry to be converted.
            x : int
                A counter for tracking the number of MultiLineString geometries found.

            Returns
            -------
            shapely.geometry.LineString
                The converted LineString geometry.
            int
                The updated counter.
            '''
            if isinstance(geometry, MultiLineString):
                x += 1
                return LineString(list(geometry.geoms)[0].coords), x
            else:
                return geometry, x

        def round_coordinates(line):
            '''
            Rounds the coordinates of a LineString geometry to 3 decimal places.

            Parameters
            ----------
            line : shapely.geometry.LineString
                The LineString geometry to be rounded.

            Returns
            -------
            shapely.geometry.LineString
                The rounded LineString geometry.
            '''
            rounded_coords = [(round(x, 3), round(y, 3)) for x, y in line.coords]
            return LineString(rounded_coords)

        streets = self.gdf
        x = 0
        streets['geometry'], x = zip(*streets['geometry'].apply(lambda geom: convert_multilinestring_to_linestring(geom, x)))
        streets['geometry'] = streets['geometry'].apply(round_coordinates)
        
        if max(x) > 0:
            print('At least one street geometry is a MultiLineString! Continuing with the first LineString as the street. Check the street geometry if necessary.')
        self.gdf = streets 
    
    def add_bool_column(self):
        '''
        Adds a boolean column to the GeoDataFrame indicating possible routes.

        This method adds a new column 'possible_route' to the GeoDataFrame, initialized with the value 1 for all rows.
        '''
        self.gdf['possible_route'] = 1

class Buildings_adj():
    '''
    A class used to represent and manipulate building geometries and attributes.

    This class provides methods to add load profiles, drop unwanted buildings, add power attributes,
    classify buildings into age groups, and merge building data.

    Attributes
    ----------
    gdf : GeoDataFrame
        A GeoDataFrame containing the building geometries and attributes.
    heat_att : str
        The attribute name for heat data.

    Methods
    -------
    add_Vlh_Loadprofile(excel_data):
        Adds full load hours and load profiles to the buildings.
        
    drop_unwanted():
        Drops buildings that do not have a load profile.
        
    add_power():
        Adds a power attribute to the buildings based on heat attribute and full load hours.
        
    extract_year(date_str):
        Extracts the year from a date string.
        
    add_BAK(bins, labels):
        Adds building age classification based on the provided bins and labels.
        
    add_age_LANUV():
        Adds building age information based on the building type attribute.
        
    merge_buildings():
        Merges building geometries and attributes, performing custom aggregations.
    '''
    def __init__(self, path, heat_att, projected_crs):
        '''
         Initializes the Buildings_adj class with a GeoDataFrame of building geometries and attributes.

        Parameters
        ----------
        path : str
            The file path to the shapefile containing the building geometries.
        heat_att : str
            The attribute name for heat data.
        projected_crs : str
            The coordinate reference system to be used for the GeoDataFrame.
        '''
        self.gdf = gpd.read_file(path, crs=projected_crs)
        self.heat_att = heat_att

    def add_Vlh_Loadprofile(self, excel_data):
        '''
        Adds full load hours and load profiles to the buildings.

        This method merges the building data with external Excel data containing full load hours (Vlh)
        and load profiles based on the 'citygml_fu' attribute of the buildings.

        Parameters
        ----------
        excel_data : DataFrame
            A DataFrame containing the load profile data with 'Funktion', 'Lastprofil', and 'Vlh' columns.
        '''
        buildings = self.gdf
        excel_data['Funktion'] = excel_data['Funktion'].astype(str)
        buildings['GFK_last_four'] = buildings['citygml_fu'].str[-4:]
        buildings = buildings.merge(excel_data[['Funktion', 'Lastprofil', 'Vlh']], left_on='GFK_last_four', right_on='Funktion', how='left')

        # Delete the temporary column and the 'Funktion' column
        buildings.drop(columns=['GFK_last_four'], inplace=True)

        try:
            buildings.drop(columns=['Funktion'], inplace=True)
        except:
            buildings.drop(columns=['Funktion_y'], inplace=True)
        self.gdf = buildings

    def drop_unwanted(self):
        '''
        Drops buildings that do not have a load profile.

        This method removes all buildings that do not have a load profile, as these are buildings that
        are not needed or have other issues.
        '''
        b = self.gdf
        b = b[b['Lastprofil'].notna()]
        b = b.copy() # Suppress a false warning
        self.gdf = b

    def add_power(self):
        '''
        Adds a power attribute to the buildings.

        This method calculates the power attribute for each building based on the heat attribute and full load hours.
        If full load hours (Vlh) are zero, it uses a default value of 1600.
        '''
        buildings = self.gdf
        buildings['power'] = buildings[self.heat_att] / buildings['Vlh'].where(buildings['Vlh'] != 0, 1600) # Default to 1600 if Vlh is 0
        self.gdf = buildings
    
    @staticmethod
    def extract_year(date_str):
        '''
        Extracts the year from a date string.

        This method extracts the year as an integer from the beginning of a date string. If the date string
        is NaN, it returns NaN.

        Parameters
        ----------
        date_str : str
            The date string from which to extract the year.

        Returns
        -------
        int or float
            The extracted year or NaN if the date string is NaN.

        Examples
        --------
        >>> Buildings_adj.extract_year("2023-07-17")
        2023
        >>> Buildings_adj.extract_year(None)
        nan
        '''
        if pd.notna(date_str):
            return int(date_str[:4])
        return np.nan

    def add_BAK(self,bins,labels):
        '''
        Adds building age classification based on the provided bins and labels.

        This method classifies buildings into age groups based on the 'validFrom' attribute using the
        provided bins and labels.

        Parameters
        ----------
        bins : list of int
            The bin edges for classifying buildings by age.
        labels : list of str
            The labels for the age bins.

        Examples
        --------
        >>> bins = [1800, 1900, 1950, 2000, 2024]
        >>> labels = ["1800-1899", "1900-1949", "1950-1999", "2000-2024"]
        '''
        # Convert the validFrom attribute to year
        self.gdf['jahr'] = self.gdf['validFrom'].apply(self.extract_year)

        # Classify buildings into age groups
        self.gdf['BAK'] = pd.cut(self.gdf['jahr'], bins=bins, labels=labels, right=True)
        self.gdf['BAK'] = self.gdf['BAK'].astype(str)
        self.gdf.drop(columns=['jahr'], inplace = True)

    def add_age_LANUV(self):
        ''' 
        Adds building age information based on the building type attribute.

        This method extracts the building age from the 'GEBAEUDETY' attribute and adds it as a new column.
        '''
        def extract_age(building_type):
            '''
            Extracts the age from the building type attribute.

            This helper function extracts the age from the 'GEBAEUDETY' attribute using a regular expression.

            Parameters
            ----------
            building_type : str
                The building type attribute value.

            Returns
            -------
            int or None
                The extracted age or None if no age is found.
            '''
            match = re.search(r'_(\d+)$', building_type)
            if match:
                return int(match.group(1))
            else:
                return None
        # Add the 'Alter_LANUV' column
        self.gdf['Alter_LANUV'] = self.gdf['GEBAEUDETY'].apply(extract_age)
    
    def merge_buildings(self):
        '''
        Merges building geometries and attributes, performing custom aggregations.

        This method dissolves the building geometries based on 'Flurstueck', 'citygml_fu', and 'Fortschrei'
        attributes and performs custom aggregations on the attributes.
        '''
        # Aggregation functions
        def custom_agg_mix_str(s):
            '''
            Aggregates string attributes by returning the unique value or 'mix' if there are multiple unique values.

            Parameters
            ----------
            s : Series
                The series to aggregate.

            Returns
            -------
            str
                The aggregated value.
            '''
            unique_vals = s.unique()
            if len(unique_vals) == 1:
                return unique_vals[0]
            else:
                return 'mix'
            
        def custom_agg_mix_numeric(s):
            '''
            Aggregates numeric attributes by returning the unique value or None if there are multiple unique values.

            Parameters
            ----------
            s : Series
                The series to aggregate.

            Returns
            -------
            int, float, or None
                The aggregated value.
            '''
            unique_vals = s.unique()
            if len(unique_vals) == 1:
                return unique_vals[0]
            else:
                return None 
            
        def custom_agg_most_common(s):
            '''
            Aggregates by returning the most common value.

            Parameters
            ----------
            s : Series
                The series to aggregate.

            Returns
            -------
            int, float, or str
                The most common value.
            '''
            most_common = s.mode()
            if len(most_common) > 0:
                return most_common.iloc[0]
            else:
                return s.iloc[0]  # Fallback if no mode is found (should not occur in practice)

        def mode_or_string(x):
            ''' 
            Aggregates by returning the most common value or a comma-separated string if there are ties.

            Parameters
            ----------
            x : Series
                The series to aggregate.

            Returns
            -------
            str
                The aggregated value.
            '''
            counts = Counter(x)
            max_count = max(counts.values())
            max_list = [val for val, count in counts.items() if count == max_count]
            if len(max_list) == 1:
                return str(max_list[0])
            else:
                sorted_list = sorted(max_list)
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
    '''
    A class used to represent and manipulate parcel geometries.

    This class provides a method to initialize a GeoDataFrame of parcel geometries from a shapefile.

    Attributes
    ----------
    gdf : GeoDataFrame
        A GeoDataFrame containing the parcel geometries.

    Methods
    -------
    __init__(path, projected_crs):
        Initializes the Parcels_adj class with a GeoDataFrame of parcel geometries.
    '''
    def __init__(self, path, projected_crs):
        '''
        Initializes the Parcels_adj class with a GeoDataFrame of parcel geometries.

        Parameters
        ----------
        path : str
            The file path to the shapefile containing the parcel geometries.
        projected_crs : str
            The coordinate reference system to be used for the GeoDataFrame.
        '''
        self.gdf = gpd.read_file(path, crs=projected_crs)

def spatial_join(shape1, shape2, attributes):
    '''
    Performs a spatial join to add attributes from shape2 to the best fitting feature in shape1.

    This function finds the best fitting feature in `shape2` that intersects with each feature in `shape1` 
    based on the intersection area. It then adds the specified attributes from `shape2` to `shape1`.

    Parameters
    ----------
    shape1 : GeoDataFrame
        The GeoDataFrame to which attributes will be added.
    shape2 : GeoDataFrame
        The GeoDataFrame from which attributes will be sourced.
    attributes : list of str
        List of attribute names to be transferred from `shape2` to `shape1`.

    Returns
    -------
    GeoDataFrame
        The updated `shape1` GeoDataFrame with the specified attributes added from `shape2`.

    Notes
    -----
    If columns named 'index_left' or 'index_right' exist in either `shape1` or `shape2`, 
    they will be removed to avoid conflicts during the spatial join.

    If an attribute specified in the `attributes` list does not exist in `shape2`, the function 
    will attempt to use a column named `{attribute}_left` instead and will print a message 
    indicating the update.

    Examples
    --------
    >>> shape1 = gpd.read_file("path/to/shape1.shp")
    >>> shape2 = gpd.read_file("path/to/shape2.shp")
    >>> attributes = ["attr1", "attr2"]
    >>> updated_shape1 = spatial_join(shape1, shape2, attributes)
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