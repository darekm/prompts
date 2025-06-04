import xml.etree.ElementTree as ET
import csv
import os
import re
import argparse

def extract_znaczniki_kont(xsd_path, output_file, section_name='TMapKontaPOZ', search_term=None):
    """
    Extract the list of account markers (znaczniki kont) from the specified section in the XSD file.
    
    Args:
        xsd_path (str): Path to the XSD file
        output_file (str): Path to the output CSV file
        section_name (str): Name of the section to extract from (default: TMapKontaPOZ)
        search_term (str, optional): Term to search for in the documentation
    """
    # Define XML namespace
    namespace = {'xsd': 'http://www.w3.org/2001/XMLSchema'}
    
    # Parse the XSD file
    tree = ET.parse(xsd_path)
    root = tree.getroot()
    
    # Find the specified simpleType element
    target_type = None
    for simple_type in root.findall('.//xsd:simpleType', namespace):
        name_attr = simple_type.get('name')
        if name_attr == section_name:
            target_type = simple_type
            break
    
    if target_type is None:
        print(f"{section_name} section not found in the XSD file.")
        return []

    # Extract section description
    annotation = target_type.find('./xsd:annotation', namespace)
    section_description = ""
    if annotation is not None:
        doc_elem = annotation.find('./xsd:documentation', namespace)
        if doc_elem is not None:
            section_description = doc_elem.text
    
    print(f"Section: {section_name}")
    print(f"Description: {section_description}")
    
    # Extract enumeration values and their documentation
    znaczniki = []
    
    restriction = target_type.find('./xsd:restriction', namespace)
    if restriction is not None:
        for enum in restriction.findall('./xsd:enumeration', namespace):
            value = enum.get('value')
            doc_elem = enum.find('.//xsd:documentation', namespace)
            documentation = doc_elem.text if doc_elem is not None else ''
            
            # Apply search filter if provided
            if search_term is None or (
                search_term.lower() in value.lower() or 
                search_term.lower() in documentation.lower()
            ):
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

def list_available_sections(xsd_path):
    """List all TMapKonta* sections available in the XSD file."""
    namespace = {'xsd': 'http://www.w3.org/2001/XMLSchema'}
    
    # Parse the XSD file
    tree = ET.parse(xsd_path)
    root = tree.getroot()
    
    # Find all simpleType elements that match the pattern
    sections = []
    for simple_type in root.findall('.//xsd:simpleType', namespace):
        name_attr = simple_type.get('name')
        if name_attr and name_attr.startswith('TMapKonta'):
            annotation = simple_type.find('./xsd:annotation', namespace)
            description = ""
            if annotation is not None:
                doc_elem = annotation.find('./xsd:documentation', namespace)
                if doc_elem is not None:
                    description = doc_elem.text
            
            sections.append({'name': name_attr, 'description': description})
    
    print("\nAvailable sections:")
    for section in sections:
        print(f"- {section['name']}: {section['description']}")
    
    return sections

def main():
    parser = argparse.ArgumentParser(description='Extract account markers from JPK_CIT.xsd')
    parser.add_argument('--xsd', default=r'c:\git\prompts\notes\jpk_cit.xsd', 
                        help='Path to the XSD file')
    parser.add_argument('--output', default=r'c:\git\prompts\znaczniki_kont.csv',
                        help='Path to the output CSV file')
    parser.add_argument('--section', default='TMapKontaPOZ',
                        help='Section name to extract (e.g., TMapKontaPOZ)')
    parser.add_argument('--search', help='Search term to filter results')
    parser.add_argument('--list-sections', action='store_true', 
                        help='List all available TMapKonta sections')
    
    args = parser.parse_args()
    
    if args.list_sections:
        list_available_sections(args.xsd)
        return
    
    # Extract the account markers
    extract_znaczniki_kont(args.xsd, args.output, args.section, args.search)

if __name__ == '__main__':
    main()
