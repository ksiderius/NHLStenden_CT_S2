# -*- coding: utf-8 -*-
"""
Created on Mon May 12 11:29:45 2025

@author: k.siderius
"""

import requests
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import os

# BRO ID
bro_id = "CPT000000225472"

# Fetch the XML
url = f"https://publiek.broservices.nl/sr/cpt/v1/objects/{bro_id}"
response = requests.get(url)

if response.status_code == 200:
    xml_data = response.content
    root = ET.fromstring(xml_data)

    # Define namespaces
    ns = {
        'dscpt': 'http://www.broservices.nl/xsd/dscpt/1.1',
        'bro': 'http://www.broservices.nl/xsd/brocommon/3.0',
        'cpt': 'http://www.broservices.nl/xsd/cpt/1.1',
        'cptcommon': 'http://www.broservices.nl/xsd/cptcommon/1.1'
    }

    # Extract the surface level Z-coordinate
    offset_elem = root.find('.//cptcommon:offset', ns)
    if offset_elem is not None and offset_elem.text:
        surface_level_z = float(offset_elem.text)
        # print(f"Surface level Z-coordinate (offset): {surface_level_z} meters")
    else:
        print("No <cptcommon:offset> element found in the XML.")

    # Extract CPT values
    values_elem = root.find('.//cptcommon:values', ns)
    if values_elem is not None and values_elem.text:
        lines = values_elem.text.strip().split(';')
        data = [line.split(',') for line in lines if line.strip()]
        df = pd.DataFrame(data)
        df = df.apply(pd.to_numeric)
        print(df.head(100))
    else:
        print("No <cptcommon:values> element found in the XML.")
else:
    print(f"Failed to fetch data. Status code: {response.status_code}")

# Plotting
fig, ax1 = plt.subplots(figsize=(6, 10))
ax1.plot(df[3], surface_level_z-df[0], color='#005AA7')
ax1.set_xlabel('cone resistance [MPa]')
ax1.set_ylabel('depth [m] NAP')
ax1.set_title(bro_id)

ax1.set_xlim(0, 30)
ax1.grid()

ax1.axhline(y=surface_level_z, color='grey', linestyle='--')

# Secondary x-axis
ax2 = ax1.twiny()
ax2.plot(df[24], surface_level_z - df[0], color='#E52329')
ax2.set_xlabel('Friction ratio [-]', color='#E52329')
ax2.set_xlim(0, 30)
ax2.invert_xaxis()

# Save image
home_directory = os.path.expanduser("~")
# Save the figure
path = home_directory + r'\Downloads'
fname = bro_id+'.png'
fig.savefig(os.path.join(path, fname), dpi=300, bbox_inches='tight')
