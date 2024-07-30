import urllib.request
import ast
from zipfile import ZipFile
from io import BytesIO
import geopandas as gpd
import pandas as pd
import urllib.request
import os
import shutil
from owslib.wfs import WebFeatureService

    
def file_list_from_URL(url):
    '''lists downloadable files from given URL

    This function downloads the content from the specified URL, decodes the content,
    evaluates it as a dictionary, and extracts a list of files from the dictionary.

    Parameters
    ----------
    url : str
        The URL from which to download and extract the file list.

    Returns
    -------
    list
        A list of files found in the dictionary under the key 'datasets' -> 1 -> 'files'.
    '''
    filestring = ''
    for line in urllib.request.urlopen(url):
        d = line.decode('latin1')
        d = d.strip()
        filestring += d
    dict=ast.literal_eval(filestring)
    files = dict['datasets'][1]['files']
    return files

def search_filename(files, city_id):
    '''Searches for a city in a list of files and returns the file name.

    This function iterates through a list of file dictionaries, searching for the specified
    city identifier in the file names. The city identifier can be either a city name or a
    Gemeindeschlüssel. If a matching file is found, its name is returned; otherwise, a default
    message indicating that no file was found is returned.

    Parameters
    ----------
    files : list of dict
        A list of dictionaries, each representing a file with at least a 'name' key.
    city_id : str or int
        The city identifier to search for in the file names. This can be a city name or a
        Gemeindeschlüssel.

    Returns
    -------
    str
        The name of the file that contains the city identifier, or 'Keine Datei gefunden'
        if no matching file is found.
    '''
    file_name = 'No sata found'
    for item in files:
        if str(city_id) in item['name']:
            file_name = item['name']
            break
    return file_name

def read_file_from_zip(url, zipfile, file_pattern, encoding='utf-8'):
    '''
    Reads a file as a GeoDataFrame from a downloadable zip file.

    This function downloads a zip file from a specified URL, extracts the contents,
    searches for a file matching a given pattern, and reads the file as a GeoDataFrame.
    The function assumes the file is a shapefile and handles extraction and cleanup
    of temporary files.

    Parameters
    ----------
    url : str
        The URL of the site where the zip file can be downloaded.
    zipfile : str
        The name of the zip file to be downloaded.
    file_pattern : str
        The pattern to search for in the file names within the zip file.
    encoding : str, optional
        The encoding to use when reading the shapefile, by default 'utf-8'.

    Returns
    -------
    GeoDataFrame
        A GeoDataFrame containing the data from the extracted shapefile.

    Examples
    --------
    >>> url = "http://example.com/files/"
    >>> zipfile = "data.zip"
    >>> file_pattern = "desired_file"
    >>> data = read_file_from_zip(url, zipfile, file_pattern)
    >>> data.head()
       column1  column2  geometry
    0        1        2  POINT (1.00000 2.00000)
    1        3        4  POINT (3.00000 4.00000)

    Notes
    -----
    The function assumes that the zip file contains shapefiles and that the desired file
    matches the provided pattern and ends with '.shp'. Temporary files are extracted to
    '/tmp/extracted_zip' and cleaned up after reading the shapefile.
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
    '''
    Searches a DataFrame for a city name .

    This function filters a given DataFrame based on a specified parameter ('city' or 'gemeinde')
    and searches for an exact match of the provided name. If a match is found, a new DataFrame
    containing the matching rows is returned; otherwise, a message is printed and None is returned.

    Parameters
    ----------
    name : str
        The name (city or municipality name) to search for in the DataFrame.
    dataframe : pandas.DataFrame
        The DataFrame to search within.
    parameter : str
        Specifies whether to search by 'city' (for city name) or 'gemeinde' (for municipality name).

    Returns
    -------
    pandas.DataFrame or None
        A DataFrame containing rows matching the specified name and parameter, or None if no match is found.
    '''
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

def get_shape_from_wfs(wfs_url, key, bbox, layer_name):
    '''
    Loads shapefiles within a bounding box from a WFS service and filters for 'key'.

    This function connects to a Web Feature Service (WFS), retrieves shapefiles within a specified
    bounding box, and filters the shapefiles based on the given key (Gemeinde or Gemarkung). If the
    number of features exceeds 100,000, a warning is printed.

    Parameters
    ----------
    wfs_url : str
        The URL of the WFS service.
    key : str
        The key for filtering (e.g., Gemeinde or Gemarkung).
    bbox : tuple
        The bounding box for filtering in the format (minx, miny, maxx, maxy).
    layer_name : str
        The name of the layer containing the desired shapes.

    Returns
    -------
    GeoDataFrame
        A GeoDataFrame containing the filtered shapes.
    int or None
        An exception flag. If the number of features exceeds 100,000, returns 1; otherwise, None.

    Examples
    --------
    >>> wfs_url = "http://example.com/wfs"
    >>> key = "123"
    >>> bbox = (10.0, 50.0, 10.5, 50.5)
    >>> layer_name = "example_layer"
    >>> shapes, exception = get_shape_from_wfs(wfs_url, key, bbox, layer_name)
    >>> shapes.head()
       nationalCadastralReference  geometry
    0                        1234  POINT (10.00000 50.00000)
    1                        1235  POINT (10.10000 50.10000)

    Notes
    -----
    The function assumes that the WFS service supports version 2.0.0 and returns data in 'text/xml' format.
    If the bounding box contains more than 100,000 features, a warning is printed, and the returned
    GeoDataFrame may be incomplete.
    '''
    # Connect to the WFS service
    wfs = WebFeatureService(wfs_url, version='2.0.0')

    # Retrieve the layer attributes as a GeoDataFrame
    response = wfs.getfeature(typename=layer_name, outputFormat='text/xml', bbox=bbox)

    # Reset the position of the BytesIO object for GeoPandas to read it
    response.seek(0)

    # Read the BytesIO object with GeoPandas
    gdf = gpd.read_file(response)

    # Warn if too many features are within the bounding box
    exception = None
    if len(gdf)>=100000:
        print('The selected area contains over 100,000 parcels! As the WFS service transmits only 100,000 features per request, some parcels may be missing.')
        exception = 1

    # Select features based on the key
    selected_rows = gdf[gdf['nationalCadastralReference'].str.startswith(key)].reset_index(drop=True)
    return selected_rows, exception