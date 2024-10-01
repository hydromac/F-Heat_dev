# F|Heat - Heat Planning Plugin for QGIS

## Description
The Heat Planning Plugin for [QGIS](https://qgis.org/) enables functions like status analysis and heat network analysis for municipal heat planning. This plugin facilitates municipal heat planning by giving users access to various Python libraries within QGIS without the need for programming skills. Parts of the plugin are currently tailored to NRW, Germany.

## Table of Contents
1. [Features and Usage](#features-and-usage)
2. [Quick-Start](#quick-start)
3. [Installation](#installation)
4. [Requirements](#requirements)
5. [Documentation](#documentation)
6. [Contact Information](#contact-information)
7. [Contributing](#contributing)
8. [License](#license)
9. [Acknowledgements](#acknowledgments)

## Features and Usage

This tool simplifies the urban heat planning process by automating tasks such as:
* downloading data, 
* customising necessary files,
* displaying suitable heat network areas and 
* a potential network layout.

The resulting network areas and routes (streets) can be customised and adjusted during the whole process. The process is about designating the planning region and is based on the [german heat planning law](https://www.gesetze-im-internet.de/wpg/BJNR18A0B0023.html).

## Quick-Start

If you do not have QGIS installed, you can download it from the official website: [qgis.org](https://qgis.org/download/)

Once QGIS is installed, open QGIS Desktop.
<img src="docs/images/readme/qs0.png" alt="quick start0" width="800">

Click on Plugins > Manage and Install Plugins...
<img src="docs/images/readme/qs1.png" alt="quick start1" width="800">

Select "All", search for "FHeat" and install the Plugin.
<img src="docs/images/readme/qs2.png" alt="quick start2" width="800">

If the plugin toolbar is not visible, right-click on an empty space in the toolbar and check the "Plugin Toolbar" box.
<img src="docs/images/readme/qs3.png" alt="quick start3" width="800">

The plugin toolbar with the F|Heat icon will then become visible.
<img src="docs/images/readme/qs4.png" alt="quick start4" width="800">

It is advisable to save the project before starting F|Heat, as the plugin utilizes the project directory to save files.
<img src="docs/images/readme/qs5.png" alt="quick start5" width="800">

F|Heat starts by clicking the icon in the toolbar. From there, the plugin guides you through the process. Check the documentation for a detailed example.
<img src="docs/images/readme/qs6.png" alt="quick start6" width="800">

## Installation
To install F|Heat and use the functionalities without QGIS, ensure you have Python installed on your system. Follow the steps below:

1. **Clone the repository**:
    ```sh
    git clone https://github.com/L4rsG/F-Heat.git
    ```

2. **Navigate to the project directory**:
    ```sh
    cd F-Heat
    ```

3. **Install the required packages**:
    ```sh
    pip install -r requirements.txt
    ```

## Requirements
For using the application as a plugin you need QGIS on your machine. The required Python packages are installed by using the plugin on your local machine.
Alternatively you can install the packages yourself by following this guide on [Installing Python packages in QGIS 3.](https://landscapearchaeology.org/2018/installing-python-packages-in-qgis-3-for-windows/)

## Documentation

All necessary steps are documented within the plugin. A detailed documentation about on installation, usage and methodology is available via the following link:

[F|Heat readthedocs](https://fheat.readthedocs.io/en/latest/)

## Contributing

We welcome contributions from the community. Issues and Pull Requests for further development are greatly appreciated. To contribute follow this guideline:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them with descriptive messages.
4. Push your changes to your forked repository.
5. Open a pull request to the main repository.

Please ensure that your contributions align with the coding standards and consider to add tests for new functionalities. If you've never contributed to an open source project before we are more than happy to walk you through how to create a pull request.

## Contact Information
**F|Heat** is developed and maintained by FH Münster - University of Applied Sciences.

<img src="docs/images/readme/fh_logo.png" alt="FH Logo" width="350">

For further information, questions or feedback, please contact one of the project maintainers:

### Organizational Matters and Usage
- Hinnerk Willenbrink - willenbrink@fh-muenster.de

### Technical Documentation and Development
- Lars Goray - lars.goray@fh-muenster.de
- Philipp Sommer - philipp.sommer@fh-muenster.de

## License

**F|Heat** is licensed under the GPL 3.0 License. We refer to the `LICENSE` file for more information.

## Acknowledgments

Credits to those who helped or inspired the project.

## Additional Attribution
This project uses code from the project [demandlib](https://github.com/oemof/demandlib) published under MIT license.
