import urllib.request
import ast
from zipfile import ZipFile
from io import BytesIO
import geopandas as gpd
import pandas as pd
import urllib.request
import os
import shutil
import sys
from owslib.wfs import WebFeatureService

    
def file_list_from_URL(url):
    '''lists files from URL'''
    filestring = ''
    for line in urllib.request.urlopen(url):
        d = line.decode('latin1')
        d = d.strip()
        filestring += d
    dict=ast.literal_eval(filestring)
    files = dict['datasets'][1]['files']
    return files

def search_filename(files, city_id):
        '''
        Searches files for city and returns file name.
        Input should either be city name or Gemeindeschlüssel
        '''
        file_name = 'Keine Datei gefunden'
        for item in files:
            if str(city_id) in item['name']:
                file_name = item['name']
                break
        return file_name

def read_file_from_zip(url,zipfile,file_pattern,encoding='utf-8'):
            '''
            reads a file as geo data frame from a downloadable zip file
            url: url of the site where the zip file can be downloaded
            zipfile: name of the zipfile
            file_path: path and name of desired file in zip file
            '''
            with urllib.request.urlopen(url + zipfile) as response:
                with ZipFile(BytesIO(response.read())) as my_zip_file:
                    # Create a temporary directory
                    temp_dir = '/tmp/extracted_zip'
                    os.makedirs(temp_dir, exist_ok=True)

                    # Extract the entire Zip archive to the temporary directory
                    my_zip_file.extractall(temp_dir)
                    
                    # search matching file
                    file_list = my_zip_file.namelist()

                    matching_files = [file for file in file_list if 
                                        file_pattern in file and file.endswith('.shp')]

                    file = matching_files[0]

                    # Read the shapefile directly from the extracted directory
                    data = gpd.read_file(os.path.join(temp_dir, file), encoding=encoding)

                    # Clean up: Remove the temporary directory
                    shutil.rmtree(temp_dir)
            return data

def filter_df(name, dataframe, parameter):
    '''searches data frame for city name'''
    if parameter.lower() == 'city':
        col = 'name'
    else:
        col = 'gemeinde'
    try:
        df = dataframe.loc[dataframe[col] == name].reset_index(drop=True)
        return df
    except :
        print(f'{name} not found')
        return None

def get_shape_from_wfs(wfs_url, schluessel, bbox, layer_name):
    '''
    loads shape files within bounding box from wfs service and filters for 'schluessel'
    wfs_url: url of the wfs service
    schluessel: key for filtering (Gemeinde or Gemarkung)
    bbox: bounding box
    layer_name: layer with desired shapes 
    '''
    # Verbinden mit dem WFS-Dienst
    wfs = WebFeatureService(wfs_url, version='2.0.0')

    # Holen Sie sich die Eigenschaften (Attribute) des Layers als GeoDataFrame
    response = wfs.getfeature(typename=layer_name, outputFormat='text/xml', bbox=bbox)

    # Position des BytesIO-Objekts zurücksetzen, damit GeoPandas es lesen kann
    response.seek(0)

    # Lesen Sie das BytesIO-Objekt mit GeoPandas
    gdf = gpd.read_file(response)

    # Flurstk
    # Warnung falls zu viele Features im Bereich liegen
    exception = None
    if len(gdf)>=100000:
        print('In dem ausgewählten Bereich befinden sich über 100000 Flurstücke! Da der WFS-Dienst nur 100000 Features pro Anfrage übermittelt, können einige Flurstücke fehlen.')
        exception = 1
    # Features der Gemarkung wählen
    selected_rows = gdf[gdf['nationalCadastralReference'].str.startswith(schluessel)].reset_index(drop=True)
    return selected_rows, exception