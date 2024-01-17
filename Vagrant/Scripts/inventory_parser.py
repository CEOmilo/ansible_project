class InventoryParser:
    # Initialize
    def __init__(self, vagrant_inventory_path):
        self.vagrant_inventory_path = vagrant_inventory_path
        

    # This is where we read our parsed inventory file and return it

    def parse_inventory_file(self):
         # Specify the path to the Vagrant dynamic inventory file
        with open(self.vagrant_inventory_path, 'r') as file:
            lines = file.readlines()

        inventory = {}
        current_group = "default"  # Start with a default group

        for line in lines:
            line = line.strip()

            if line:  # Check if the line is not empty
                # Treat each section of consecutive hosts as a group
                inventory.setdefault(current_group, []).append(line)

        return inventory

    # This is our parser that parses the auto-generated Vagrant inventory

    def extract_connection_details(self, host_line):
        parts = host_line.split()

        if len(parts) >= 5:
            hostname = parts[1].split("=")[1]
            port = int(parts[2].split("=")[1])
            username = parts[3].split("=")[1].strip("'")
            private_key_path = parts[4].split("=")[1].strip("'")
            vm_identifier = private_key_path.split('/')[-3] if len(private_key_path.split('/')) >= 4 else None
            return hostname, port, username, private_key_path, vm_identifier
        else:
            return None