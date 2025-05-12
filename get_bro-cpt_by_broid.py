import requests
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib.gridspec as gridspec

# Function to parse column names from the XML schema URL (manual due to slow response)
def parse_column_names_from_schema(schema_url='https://schema.broservices.nl/xsd/cptcommon/1.1/cpttestresult_record.xml'):
    # response = requests.get(schema_url)
    # if response.status_code == 200:
    #     schema_data = response.content
    #     root = ET.fromstring(schema_data)
    #     ns = {'swe': 'http://www.opengis.net/swe/2.0'}
        
    #     column_names = []
    #     for field in root.findall('.//swe:field', ns):
    #         column_names.append(field.attrib['name'])
          
    #     return column_names
    # else:
    #     print(f"Failed to fetch schema. Status code: {response.status_code}")
    #     return []
    column_names = ['penetrationLength', 'depth', 'elapsedTime', 'coneResistance', 'correctedConeResistance', 'netConeResistance', 'magneticFieldStrengthX', 'magneticFieldStrengthY', 'magneticFieldStrengthZ', 'magneticFieldStrengthTotal', 'electricalConductivity', 'inclinationEW', 'inclinationNS', 'inclinationX', 'inclinationY', 'inclinationResultant', 'magneticInclination', 'magneticDeclination', 'localFriction', 'poreRatio', 'temperature', 'porePressureU1', 'porePressureU2', 'porePressureU3', 'frictionRatio']
    return  column_names


import requests
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import os

def get_brocpt_by_broid(bro_ids, safe_fig=True):
    if isinstance(bro_ids, str):
        bro_ids = [bro_ids]
    
    data_dict = {}
    for bro_id in bro_ids:
        url = f"https://publiek.broservices.nl/sr/cpt/v1/objects/{bro_id}"   
        response = requests.get(url)
        
        if response.status_code == 200:
            xml_data = response.content
            root = ET.fromstring(xml_data)

            ns = {
                'dscpt': 'http://www.broservices.nl/xsd/dscpt/1.1',
                'bro': 'http://www.broservices.nl/xsd/brocommon/3.0',
                'cpt': 'http://www.broservices.nl/xsd/cpt/1.1',
                'cptcommon': 'http://www.broservices.nl/xsd/cptcommon/1.1'
            }
            column_names = parse_column_names_from_schema()
            
            offset_elem = root.find('.//cptcommon:offset', ns)
            surface_level_z = float(offset_elem.text) if offset_elem is not None and offset_elem.text else 0

            values_elem = root.find('.//cptcommon:values', ns)
            if values_elem is not None and values_elem.text:
                lines = values_elem.text.strip().split(';')
                data = [line.split(',') for line in lines if line.strip()]
                df = pd.DataFrame(data).apply(pd.to_numeric)
                df.columns = column_names
                df.sort_values('depth')
                df['surface_level_z'] = surface_level_z
                data_dict[bro_id] = df
            else:
                print(f"No <cptcommon:values> element found in the XML for {bro_id}.")
        else:
            print(f"Failed to fetch data for {bro_id}. Status code: {response.status_code}")

    if not data_dict:
        return None

    if safe_fig:
        fig = plt.figure(figsize=(12, 16))
        gs = gridspec.GridSpec(1, 3, width_ratios=[3, 1, 1])
        
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1], sharey=ax1)
        ax3 = fig.add_subplot(gs[2], sharey=ax1)
        
        for bro_id, df in data_dict.items():
            surface_level_z = df['surface_level_z'].iloc[0]
            
            ax1.plot(df['coneResistance'], surface_level_z - df['depth'], label=bro_id)
            ax2.plot(df['frictionRatio'], surface_level_z - df['depth'], label=bro_id)
            ax3.plot(df['porePressureU1'], surface_level_z - df['depth'], label=f'{bro_id} U1')
            ax3.plot(df['porePressureU2'], surface_level_z - df['depth'], label=f'{bro_id} U2')
            ax3.plot(df['porePressureU3'], surface_level_z - df['depth'], label=f'{bro_id} U3')
            ax1.axhline(y=surface_level_z, color='grey', linestyle='--')
            ax2.axhline(y=surface_level_z, color='grey', linestyle='--')
            ax3.axhline(y=surface_level_z, color='grey', linestyle='--')
        
        ax1.set_xlabel('Cone resistance [MPa]')
        ax1.set_ylabel('depth [m] NAP')
        ax1.set_xlim(0, 30)
        ax1.grid()
        
        ax1.legend(loc=4)
        
        ax2.set_xlabel('Friction ratio [-]')
        ax2.set_xlim(0, 10)
        ax2.invert_xaxis()
        ax2.grid()
        ax2.axhline(y=surface_level_z, color='grey', linestyle='--')
        
        ax3.set_xlabel('Pore Pressure [MPa]')
        ax3.set_xlim(0, 1)
        ax3.grid()
        ax3.axhline(y=surface_level_z, color='grey', linestyle='--')

        path = os.path.join(os.path.expanduser("~"), 'Downloads')
        fig.savefig(os.path.join(path, 'combined_plot.png'), dpi=300, bbox_inches='tight')

    return data_dict

# Example usage
cpt_dict = get_brocpt_by_broid(['CPT000000225352', 'CPT000000225353'])
for bro_id, df in cpt_dict.items():
    print(f"Data for {bro_id}:")
    print(df.head(100000))
