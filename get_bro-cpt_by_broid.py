import requests
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import os

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


# Function to get CPT data by BRO ID
def get_brocpt_by_broid(bro_id, safe_fig=True):
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

        offset_elem = root.find('.//cptcommon:offset', ns)
        surface_level_z = float(offset_elem.text) if offset_elem is not None and offset_elem.text else 0

        values_elem = root.find('.//cptcommon:values', ns)
        if values_elem is not None and values_elem.text:
            lines = values_elem.text.strip().split(';')
            data = [line.split(',') for line in lines if line.strip()]
            df = pd.DataFrame(data).apply(pd.to_numeric)

            column_names = parse_column_names_from_schema()
            df.columns = column_names
        else:
            print("No <cptcommon:values> element found in the XML.")
            return None
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return None

    if safe_fig:
        fig, ax1 = plt.subplots(figsize=(6, 10))
        ax1.plot(df['coneResistance'], surface_level_z - df['depth'], color='#005AA7')
        ax1.set_xlabel('cone resistance [MPa]')
        ax1.set_ylabel('depth [m] NAP')
        ax1.set_title(bro_id)
        ax1.set_xlim(0, 30)
        ax1.grid()
        ax1.axhline(y=surface_level_z, color='grey', linestyle='--')

        ax2 = ax1.twiny()
        ax2.plot(df['frictionRatio'], surface_level_z - df['depth'], color='#E52329')
        ax2.set_xlabel('Friction ratio [-]', color='#E52329')
        ax2.set_xlim(0, 30)
        ax2.invert_xaxis()

        path = os.path.join(os.path.expanduser("~"), 'Downloads')
        fig.savefig(os.path.join(path, bro_id + '.png'), dpi=300, bbox_inches='tight')

    return df

# Example usage

cpt = get_brocpt_by_broid('CPT000000225441')
print(cpt.head())
