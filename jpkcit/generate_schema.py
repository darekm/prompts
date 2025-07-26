from calendar import c
import csv
import os

from sklearn import base

next_idx = 30  # Starting index for new branches


def read_csv_entries(input_file):
    """
    Read CSV file and extract entries as a dictionary.

    Args:
        input_file (str): Path to the input CSV file

    Returns:
        dict: Dictionary of entries with code as key and details as value
    """
    entries = {}
    global next_idx

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
                        'code': code,
                        'components': components,
                        'is_generated': False,
                        'is_branch': False,  # Initially set to False
                        'order': next_idx * 10,  # Original order based on CSV line
                        'index': next_idx,
                        'sum': [],  # Initialize sum as an empty list
                    }
                    next_idx += 1

        return entries
    except UnicodeDecodeError:
        print('Encoding error detected. Trying alternative encoding...')
    except Exception as e:
        print(f'Error reading CSV file: {e}')
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
    global next_idx

    # Create a dictionary to store all paths that should exist
    all_paths = {}
    branches_to_add = {}

    # Collect all component paths from entries
    for code, entry in entries.items():
        components = entry['components']

        # Add all prefixes of the path as required branches
        for i in range(1, len(components)):
            path = tuple(components[:i])
            # Store the path with its best order (keep the lowest order value if path already exists)
            path_order = entry['order'] - (len(components) - i)  # Adjust order based on depth
            if path in all_paths:
                all_paths[path]['order'] = min(all_paths[path]['order'], path_order)
                all_paths[path]['sum'].append(entry['index'])
                # all_paths[path]['code'] = entry['code'][:-1] + '='

            else:
                all_paths[path] = {'order': path_order, 'sum': [entry['index']], 'code': entry['code'][:-1] + '='}

    # Check which paths need to be added
    for path, branch in all_paths.items():
        # Check if a direct entry for this path exists
        path_exists = False
        for code, entry in entries.items():
            if tuple(entry['components']) == path:
                entry['is_branch'] = True  # Mark as branch if it exists
                branch['index'] = entry['index']  # Use existing index
                entry['sum'] = branch['sum']  # Update sum with existing indices
                path_exists = True
                break

        # If no direct entry exists, create one
        if not path_exists:
            # Generate a branch code
            branch_code = ''
            for comp in path:
                branch_code += comp[0] if branch_code == '' else comp[0].lower()
            branch_code = branch_code[: min(len(branch_code), 6)]  # limit length
            branch_code += '='

            # Ensure the branch code is unique
            branch_code = branch['code'] if 'code' in branch else branch_code
            base_branch_code = branch_code

            suffix = 1
            while branch_code in entries or branch_code in branches_to_add:
                branch_code = f'{base_branch_code}{suffix}'
                suffix += 1

            # Add the new branch
            branches_to_add[branch_code] = {
                'components': list(path),
                'order': branch['order'],
                'index': next_idx,
                'sum': branch['sum'],  # Use the sum from the existing path
                'is_branch': True,  # Mark this as a branch
                'is_generated': True,  # Mark this as a generated branch
            }
            next_idx += 1

    # Add the new branches to the entries
    entries.update(branches_to_add)
    return entries


def output_sums_as_schema(sums, output_file):
    """
    Output the sum paths to the schema file.
    """
    try:
        with open(output_file, 'w', encoding='cp1250') as schema_file:
            for path, branch in sums.items():
                if branch['is_branch']:
                    idx = branch['index']  # Adjust index for branches
                    schema_file.write(f'  tp[{idx}] := ')
                    for idx in branch['sum']:
                        schema_file.write(f' tp[{idx}] +')
                    schema_file.write('0;\n')
        print(f"Sum paths successfully generated in '{output_file}'")

    except Exception as e:
        print(f'Error writing the schema file: {e}')


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
        group = 0

        with open(output_file, 'w', encoding='cp1250') as schema_file:
            for code, entry in sorted_entries:
                components = entry['components']
                depth = len(components) - 2  # Adjust depth (root is 0)
                if depth < 0:
                    continue  # Skip root level

                # Get the description (last component)
                description = components[-1] if components else ''

                # Format based on whether it's a branch or leaf node
                if depth == 0:
                    depth_indicator = ' '
                else:
                    depth_indicator = '>' * (depth)
                idx = entry['index']
                if entry['is_branch']:
                    idx += 8000
                schema_file.write(f'{code} * {description[0:90]}^{depth_indicator}{idx}|')
                if counter % 2 == 0:
                    schema_file.write("',\n  '")
                    group += 1
                else:
                    schema_file.write('')
                counter += 1
                if group == 60:
                    schema_file.write('\'\n\n  \'')
                    group = 0

            for i in range(group, 60):
                schema_file.write("'',\n")
        print(f"Schema successfully generated in '{output_file}'")

    except Exception as e:
        print(f'Error writing the schema file: {e}')


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
        print('No valid entries found in the input file.')
        return

    # Generate missing branch entries
    entries = generate_missing_branches(entries)

    # Output the entries directly as a schema
    output_entries_as_schema(entries, output_file)
    output_sums_as_schema(entries, r'c:\git\prompts\jpkcit\sum_schema_sum.txt')


if __name__ == '__main__':
    input_file = r'c:\git\prompts\jpkcit\znaczniki_kont_poz.csv'
    output_file = r'c:\git\prompts\jpkcit\account_schema_tree.txt'

    generate_hierarchical_schema(input_file, output_file)
