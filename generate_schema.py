from calendar import c
import csv
import os

def read_csv_entries(input_file):
    """
    Read CSV file and extract entries as a dictionary.
    
    Args:
        input_file (str): Path to the input CSV file
        
    Returns:
        dict: Dictionary of entries with code as key and details as value
    """
    entries = {}
    idx = 100
    
    try:
        with open(input_file, 'r', encoding='utf-8-sig') as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader)  # Skip header row
            
            for line in csv_reader:
                if len(line) >= 2:
                    code = line[0].strip()
                    description = line[1].strip()
                    components = [comp.strip() for comp in description.split('|')]
                    
                    entries[code] = {
                        'components': components,
                        'is_generated': False,
                        'order': idx*10,  # Original order based on CSV line
                        'index': idx
                    }
                    idx += 1
        
        return entries
    except UnicodeDecodeError:
        print("Encoding error detected. Trying alternative encoding...")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return {}

def generate_missing_branches(entries):
    """
    Generate missing branch entries in the hierarchy.
    
    This function ensures that for any given path in the hierarchy,
    all intermediate paths also exist as entries.
    
    Args:
        entries (dict): Dictionary of entries with code as key and details as value
        
    Returns:
        dict: Updated dictionary with added branch entries
    """
    # Find the highest index
    next_idx = 8100
    
    # Create a dictionary to store all paths that should exist
    all_paths = {}
    branches_to_add = {}
    
    # Collect all component paths from entries
    for code, entry in entries.items():
        components = entry['components']
        
        # Add all prefixes of the path as required branches
        for i in range(1, len(components) + 1):
            path = tuple(components[:i])
            # Store the path with its best order (keep the lowest order value if path already exists)
            path_order = entry['order'] - (len(components) - i)  # Adjust order based on depth
            if path in all_paths:
                all_paths[path] = min(all_paths[path], path_order)
            else:
                all_paths[path] = path_order
    
    # Check which paths need to be added
    for path, order in all_paths.items():
        # Check if a direct entry for this path exists
        path_exists = False
        for code, entry in entries.items():
            if tuple(entry['components']) == path:
                path_exists = True
                break
                
        # If no direct entry exists, create one
        if not path_exists:
            # Generate a branch code
            branch_code = ""
            for comp in path:
                branch_code += comp[0] if branch_code == "" else comp[0].lower()
            branch_code = branch_code[:min(len(branch_code), 5)]  # limit length
            
            # Ensure the branch code is unique
            base_branch_code = branch_code
            suffix = 1
            while branch_code in entries or branch_code in branches_to_add:
                branch_code = f"{base_branch_code}{suffix}"
                suffix += 1
            
            # Add the new branch
            branches_to_add[branch_code] = {
                'components': list(path),
                'order': order,
                'index': next_idx,
                'is_generated': True  # Mark this as a generated branch
            }
            next_idx += 1
    
    # Add the new branches to the entries
    entries.update(branches_to_add)
    return entries

def output_entries_as_schema(entries, output_file):
    """
    Output all entries directly to the schema file in hierarchical order.
    
    Args:
        entries (dict): Dictionary of entries with code as key and details as value
        output_file (str): Path to the output schema file
    """
    try:
        # Sort entries by component length (depth) and then by order
        sorted_entries = []
        for code, entry in entries.items():
            sorted_entries.append((code, entry))
        
        # Sort by depth first, then by order within each depth
        sorted_entries.sort(key=lambda x: (x[1]['order']))

        counter = 100
        group=0

        with open(output_file, 'w', encoding='cp1250') as schema_file:
            for code, entry in sorted_entries:
                components = entry['components']
                depth = len(components) - 2  # Adjust depth (root is 0)
                if depth < 0:
                    continue  # Skip root level
                
                # Get the description (last component)
                description = components[-1] if components else ""
                
                # Format based on whether it's a branch or leaf node
                if depth == 0:
                    depth_indicator = ' '
                else:
                    depth_indicator = '>' * (depth)
                schema_file.write(f"{code} * {description[0:55]}^{depth_indicator}{entry['index']}|")
                if counter % 3 == 0:
                    schema_file.write("',\n  '")
                    group += 1
                else:
                    schema_file.write("")
                counter += 1
                if group == 60:
                    schema_file.write("\n\n")
                    group = 0

            for i in range(group,60):
                schema_file.write("'',\n")
        print(f"Schema successfully generated in '{output_file}'")

    except Exception as e:
        print(f"Error writing the schema file: {e}")

def generate_hierarchical_schema(input_file, output_file):
    """
    Generate a hierarchical schema file from a CSV file with accounting codes.
    
    Args:
        input_file (str): Path to the input CSV file
        output_file (str): Path to the output schema file
    """
    # Ensure input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return
    
    # Read entries from CSV file
    entries = read_csv_entries(input_file)
    if not entries:
        print("No valid entries found in the input file.")
        return
    
    # Generate missing branch entries
    entries = generate_missing_branches(entries)
    
    # Output the entries directly as a schema
    output_entries_as_schema(entries, output_file)
    
   

if __name__ == "__main__":
    input_file = r"c:\git\prompts\znaczniki_kont_poz.csv"
    output_file = r"c:\git\prompts\account_schema_tree.txt"
    
    generate_hierarchical_schema(input_file, output_file)
