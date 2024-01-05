import paramiko

# establishing ssh connection

def establish_ssh_connection(hostname, port, username, private_key_path):
    # Create an SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to the remote host using the provided details
        ssh.connect(hostname, port=port, username=username, key_filename=private_key_path)
        print(f"SSH connection established to {hostname}")
        return ssh
    except Exception as e:
        print(f"Error connecting to {hostname}: {e}")
        return None

# Checking if TMUX is installed
    
def is_tmux_installed(ssh):
    try:
        # Check if tmux is already installed
        _, stdout, _ = ssh.exec_command("which tmux")
        return bool(stdout.read().decode('utf-8').strip())
    except Exception as e:
        print(f"Error checking tmux installation: {e}")
        return False

# Deploying TMUX to all of our VM's
    
def deploy_tmux(ssh):
    try:
        # Check if tmux is already installed
        if is_tmux_installed(ssh):
            print("tmux is already installed on the system.")
        else:
            # Run tmux deployment commands
            tmux_install_command = "sudo apt-get update && sudo apt-get install -y tmux"
            _, stdout, stderr = ssh.exec_command(tmux_install_command)

            # Check if the installation was successful
            if stdout.channel.recv_exit_status() == 0:
                print("Successfully deployed tmux")
            else:
                print(f"Failed to deploy tmux. Error: {stderr.read().decode('utf-8')}")
    except Exception as e:
        print(f"Error during tmux deployment: {e}")
    finally:
        # Close the SSH connection
        ssh.close()

# This is where we read our parsed inventory file and return it

def parse_inventory_file(inventory_path):
    with open(inventory_path, 'r') as file:
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

def extract_connection_details(host_line, vagrant_inventory_path):
    parts = host_line.split()

    if len(parts) >= 5:
        hostname = parts[1].split("=")[1]
        port = int(parts[2].split("=")[1])
        username = parts[3].split("=")[1].strip("'")
        private_key_path = parts[4].split("=")[1].strip("'")
        return hostname, port, username, private_key_path
    else:
        return None

# Main function

def main():
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
                # Deploy tmux on the remote host
                # Establish SSH connection
                ssh_connection = establish_ssh_connection(hostname, port, username, private_key_path)

                if ssh_connection:
                    # Deploy tmux on the remote host
                    deploy_tmux(ssh_connection)
            else:
                print(f"Skipping invalid host line: {host}")

if __name__ == "__main__":
    main()
