Installation
============
.. attention::
    If QGIS and Python is already installed on the system, please go directly to :ref:`Plugin-Installation` section. 

To use this software Python and QGIS has to be installed on your system. The application is currently tested for Python versions > 3.9 and QGIS version > 3.3.

QGIS Installation
-----------------

Go to `qgis.org <https://qgis.org/>`_ and download the current version for your system.

Python Installation
-------------------

The Plugin provides a function to automatically install the required python packages. Therefore python has to be installed on your device. Go to `python.org <https://www.python.org/downloads/>`_ and download the current version for your system (Windows, macOS, Linux).
Follow the instructions for installation for installation. Make sure to check the box for adding Python to PATH. If you want to install the required packages manually you can skip the python download.

.. attention::
    Make sure to check the box for adding Python to PATH.

    .. figure:: images/python_to_path.png
        :alt: Python_to_path.png
        :width: 100 %
        :align: center

.. _Plugin-Installation:

Plugin Installation
-------------------

After installing Python and QGIS the plugin, as an extension of QGIS, has to be installed finally.

#. Official extension from QGIS:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure:: images//readme/qs0.png
    :alt: qs0.png
    :width: 100 %
    :align: center

a) Once QGIS is installed, open QGIS Desktop.


.. figure:: images//readme/qs1.png
    :alt: qs1.png
    :width: 100 %
    :align: center

b) Click on "Plugins" > "Manage and Install Plugins..."


.. figure:: images//readme/qs2.png
    :alt: qs2.png
    :width: 100 %
    :align: center

c) Select "All", search for "FHeat" and install the Plugin.

.. figure:: images//readme/qs3.png
    :alt: qs3.png
    :width: 100 %
    :align: center

d) If the plugin toolbar is not visible, right-click on an empty space in the toolbar and check the "Plugin Toolbar" box.

.. figure:: images//readme/qs4.png
    :alt: qs4.png
    :width: 100 %
    :align: center

e) The plugin toolbar with the F|Heat icon will then become visible.

.. figure:: images//readme/qs5.png
    :alt: qs5.png
    :width: 100 %
    :align: center

f) It is advisable to save the project before starting F|Heat, as the plugin utilizes the project directory to save files. The project can be saved by clicking the save icon or by selecting "Project" > "Save As...".

.. figure:: images//readme/qs6.png
    :alt: qs6.png
    :width: 100 %
    :align: center

g) F|Heat starts by clicking the icon in the toolbar.



#. Install via zip-folder (development version):
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    * Extract the plugin from the current Github repository.
    * Install via the option `Install from zip-folder` instead of searching for FHeat in step c).
    * Do not select the whole repository, only zip the `F-Heat_QGIS` folder and install it

Install python packages
-----------------------

Once F|Heat is started the user is greeted with the Introduction tab. Here you can find the same Information on how to install the required python packages:

To ensure the required packages are installed, please click on 'Install Packages' at the bottom of the tab. This will automatically install the necessary Python libraries: 
geopandas, OWSLib, pandas, fiona, numpy, networkx, matplotlib, openpyxl, demandlib, workalendar

Alternatively, you can follow the steps from this guide and install the libraries manually:
`Installing Python packages in QGIS 3 (for Windows) <https://landscapearchaeology.org/2018/installing-python-packages-in-qgis-3-for-windows/>`_

Once the button is clicked a terminal window will open and installation will begin. If you get an empty prompt and everything is installed without error messages, you can close the window.
If an error occurs you can try to install the packages manually or check the Troubleshooting section.

.. warning::
    Do not close the terminal window during installation. Otherwise the process has to be repeated.

Congratulations, everything is set up. If you did not get any error messages you are ready to plan district heating networks for your desired planning region.


Manual Instructions
-------------------

We provide also a german instruction paper where all steps and the underlying structure of the methodology is explained.

.. note::
    German version of the installation process will be added soon.
