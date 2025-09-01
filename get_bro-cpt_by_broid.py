import requests as requests
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import os as os
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D

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

def get_brocpt_by_broid(bro_ids, safe_fig=True):
    if isinstance(bro_ids, str):
        bro_ids = [bro_ids]
    
    data_dict = {}
    for bro_id in bro_ids:
        url = f"https://publiek.broservices.nl/sr/cpt/v1/objects/{bro_id}"   
        response = requests.get(url, verify=False) #if a ssl error occurs try requests.get(url, verify=False)
        
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
                df = df.sort_values('penetrationLength')
                data_dict[bro_id] = {'df': df, 'surface_level_z': surface_level_z}
            else:
                print(f"No <cptcommon:values> element found in the XML for {bro_id}.")
        else:
            print(f"Failed to fetch data for {bro_id}. Status code: {response.status_code}")

    if not data_dict:
        return None

    if safe_fig:
        fig = plt.figure(figsize=(12, 16))
        gs = gridspec.GridSpec(1, 3, width_ratios=[3, 1, 3]) 
        
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1], sharey=ax1)
        ax3 = fig.add_subplot(gs[2], sharey=ax1)
        
        axes = fig.get_axes()

        for bro_id, data in data_dict.items():
            df = data['df']
            df['ref_depth'] = data['surface_level_z'] - df['depth']
            max_exp_depth = data['surface_level_z'] - df['depth'].iat[-1]
            
            ax1.plot(
                df['coneResistance'], 
                df['ref_depth'], 
                label=bro_id
                )
            
            ax2.plot(
                df['frictionRatio'], 
                df['ref_depth'], 
                label=bro_id)
            
            last_color = ax2.get_lines()[-1].get_c()
            
            ax3.plot(
                df['porePressureU1'], 
                df['ref_depth'], 
                label=f'{bro_id} U1', 
                color=last_color, 
                linestyle=(0, (1, 1))
                )
            
            ax3.plot(
                df['porePressureU2'], 
                df['ref_depth'], 
                label=f'{bro_id} U2', 
                color=last_color, 
                linestyle='solid'
                )
            
            ax3.plot(
                df['porePressureU3'], 
                df['ref_depth'], 
                label=f'{bro_id} U3', 
                color=last_color, 
                linestyle='dashdot'
                )
            
            for ax in axes:
                ax.axhline(
                    y=data['surface_level_z'], 
                    color=last_color, 
                    linestyle='--'
                    )
                ax.axhline(
                    y= max_exp_depth, 
                    color=last_color, 
                    linestyle='--'
                    )
        
        for ax in axes:
            ax.grid(
                visible=True, 
                which='major', 
                color='grey', 
                linestyle='-'
                )
            ax.minorticks_on()
            ax.grid(
                visible=True, 
                which='minor', 
                color='grey', 
                linestyle='--'
                )
               
        ax1.set_xlabel('Cone resistance [MPa]')
        ax1.set_ylabel('depth [m] REF')
        ax1.set_xlim(0, 30)

        ax2.set_xlabel('Friction ratio [-]')
        ax2.set_xlim(0, 10)
        ax2.invert_xaxis()

        ax3_legend = [
            Line2D([0], [0], color='black', linestyle=(0, (1, 1)), label='u1'),
            Line2D([0], [0], color='black', linestyle='solid', label='u2'),
            Line2D([0], [0], color='black', linestyle='dashdot', label='u3')
            ]
        
        ax3.set_xlabel('Pore pressure [MPa]')
        ax3.set_xlim(-0.1, 1)
        ax3.axvline(x=0, color='black', linewidth=1)

        if len(data_dict.items()) <5: #if more than 5 CPT's are selected do not plot legend
            ax1.legend(loc=4)
            
        ax3.legend(handles=ax3_legend, loc='lower right')

        path = os.path.join(os.path.expanduser("~"), 'Downloads')
        fig.savefig(
            os.path.join(
                path, 
                'combined_plot.png'
                ), 
            dpi=300, 
            bbox_inches='tight'
            )

    return data_dict


if __name__ == "__main__":
    # Example usage
    cpt_dict = get_brocpt_by_broid(['CPT000000007230'])
    for bro_id, data in cpt_dict.items():
        print(f"Data for {bro_id}:")
        print(data['df'].head())
        print(f"Surface level: {data['surface_level_z']}")
