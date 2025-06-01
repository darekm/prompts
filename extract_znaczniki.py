import xml.etree.ElementTree as ET
import csv
import os

def extract_znaczniki_kont(xsd_path, output_file):
    """
    Extract the list of account markers (znaczniki kont) from the TMapKontaPOZ section in the XSD file.
    
    Args:
        xsd_path (str): Path to the XSD file
        output_file (str): Path to the output CSV file
    """
    # Define XML namespace
    namespace = {'xsd': 'http://www.w3.org/2001/XMLSchema'}
    
    # Parse the XSD file
    tree = ET.parse(xsd_path)
    root = tree.getroot()
    
    # Find the TMapKontaPOZ simpleType element
    poz_type = None
    for simple_type in root.findall('.//xsd:simpleType', namespace):
        name_attr = simple_type.get('name')
        if name_attr == 'TMapKontaPOZ':
            poz_type = simple_type
            break
    
    if poz_type is None:
        print("TMapKontaPOZ section not found in the XSD file.")
        return

    # Extract enumeration values and their documentation
    znaczniki = []
    
    restriction = poz_type.find('./xsd:restriction', namespace)
    if restriction is not None:
        for enum in restriction.findall('./xsd:enumeration', namespace):
            value = enum.get('value')
            doc_elem = enum.find('.//xsd:documentation', namespace)
            documentation = doc_elem.text if doc_elem is not None else ''
            
            znaczniki.append({'kod': value, 'opis': documentation})
    
    # Write to CSV file
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['kod', 'opis']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for znacznik in znaczniki:
            writer.writerow(znacznik)
    
    print(f"Extracted {len(znaczniki)} account markers to {output_file}")
    return znaczniki

def main():
    # Path to the XSD file
    xsd_path = r'c:\git\prompts\notes\jpk_cit.xsd'
    
    # Path to the output CSV file
    output_file = r'c:\git\prompts\znaczniki_kont_poz.csv'
    
    # Extract the account markers
    extract_znaczniki_kont(xsd_path, output_file)

if __name__ == '__main__':
    main()
