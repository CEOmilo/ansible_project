def parse_inventory_file(inventory_path):
    with open(inventory_path, 'r') as file:
        lines = file.readlines()
    
    inventory = {}
    current_group = "default"

    for line in lines:
        line = line.strip()

        if line:  # Check if the line is not empty
            # Treat each section of consecutive hosts as a group
            inventory.setdefault(current_group, []).append(line)

    return inventory

def extract_connection_details(host_line, vagrant_inventory_path):
    parts = host_line.split()
    print(f"Reading inventory file: {vagrant_inventory_path}")
    inventory = parse_inventory_file(vagrant_inventory_path)
    print(f"Parsed inventory: {inventory}")

    if len(parts) >= 5:
        hostname = parts[1].split("=")[1]
        port = int(parts[2].split("=")[1])
        username = parts[3].split("=")[1].strip("'")
        private_key_path = parts[4].split("=")[1].strip("'")
        return hostname, port, username, private_key_path
    else:
        return None

if __name__ == "__main__":
    # Specify the path to the Vagrant dynamic inventory file
    vagrant_inventory_path = "/home/stafford/Projects/Vagrant/.vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory"
    
    # Parse the Vagrant inventory to extract connection details
    inventory = parse_inventory_file(vagrant_inventory_path)
    

    for group, hosts in inventory.items():
        for host in hosts:
            connection_details = extract_connection_details(host, vagrant_inventory_path)
            if connection_details:
                hostname, port, username, private_key_path = connection_details
                print(f"Host: {hostname}, Port: {port}, Username: {username}, Private Key Path: {private_key_path}")
            else:
                print(f"Skipping invalid host line: {host}")
