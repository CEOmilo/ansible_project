import paramiko
import logging
import os

# Setting up logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__) 

# Establishing ssh connection

def establish_ssh_connection(hostname, port, username, private_key_path):
    # Create an SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to the remote host using the provided details
        ssh.connect(hostname, port=port, username=username, key_filename=private_key_path)
        logger.info("SSH connection established to {hostname}")
        return ssh
    except Exception as e:
        logger.info(f"Error connecting to {hostname}: {e}")
        return None

def is_vsftpd_installed(ssh):
    try:
        # Check if very simple ftpd is installed
        _, stdout, _ = ssh.exec_command("which vsftpd")
        return bool(stdout.read().decode('utf-8').strip())
    except Exception as e:
        logger.info(f"Error checking vsftpd installation: {e}")
        return False
    
# Deploying NFS server

def deploy_ftp_server(ssh):
    try:
        if is_vsftpd_installed(ssh):
            logger.info("FTP is already installed on the system.")
        else:
            # Run nfs server deployment commands
            nfs_install_command = "sudo apt-get update && sudo apt-get install -y nfs-utils* && sudo apt-get install -y rpcbind*"
            _, stdout, stderr = ssh.exec_command(nfs_install_command)


# Checking if a web server is already installed
def is_apache_installed(ssh):
    try:
        # Check if apache2 is installed
        _, stdout, _ = ssh.exec_command("which apache2")
        return bool(stdout.read().decode('utf-8').strip())
    except Exception as e:
        logger.info(f"Error checking apache2 installation: {e}")
        return False
    
# Deploying apache web servers to designated vm

def deploy_apache(ssh):
    try:
        # Checking if apache is installed
        if is_apache_installed(ssh):
            logger.info("apache is already installed on the system.")
        else:
            # Run apache deployment commands
            apache_install_command = "sudo apt-get update && sudo apt-get install -y apache2"
            _, stdout, stderr = ssh.exec_command(apache_install_command)

            # Check if the installation was successful
            if stdout.channel.recv_exit_status() == 0:
                logger.info("Successfully installed apache")
            else:
                logger.info(f"Failed to deploy apache. Error: {stderr.read().decode('utf-8')}")
    except Exception as e:
        logger.info(f"Error during apache deployment: {e}")
        return False

# Copying my local website to the vm

def deploy_website(ssh, website_path):
    _, stdout, stderr = ssh.exec_command('sudo chmod -R 777 /var/www/html')
    if stdout.channel.recv_exit_status() == 0:
        logger.info("Successfully changed permissions")
    else:
        logger.info(f"Permissions unchanged. Error: {stderr.read().decode('utf-8')}")
    sftp = ssh.open_sftp()
    for root, dirs, files in os.walk(website_path):
            for file in files:
                local_file_path = os.path.join(root, file)
                remote_file_path = os.path.join(website_path, os.path.relpath(local_file_path, website_path))

                # Ensure remote directories exist
                remote_dir = os.path.dirname(remote_file_path)
                try:
                    sftp.stat(remote_dir)
                except FileNotFoundError:
                    sftp.mkdir(remote_dir)

                # Upload the file
                sftp.put(local_file_path, remote_file_path)
    sftp.close()


# Checking if TMUX is installed
    
def is_tmux_installed(ssh):
    try:
        # Check if tmux is already installed
        _, stdout, _ = ssh.exec_command("which tmux")
        return bool(stdout.read().decode('utf-8').strip())
    except Exception as e:
        logger.info("Error checking tmux installation: {e}")
        return False

# Deploying TMUX to all of our VM's
    
def deploy_tmux(ssh):
    try:
        # Check if tmux is already installed
        if is_tmux_installed(ssh):
            logger.info("tmux is already installed on the system.")
        else:
            # Run tmux deployment commands
            tmux_install_command = "sudo apt-get update && sudo apt-get install -y tmux"
            _, stdout, stderr = ssh.exec_command(tmux_install_command)

            # Check if the installation was successful
            if stdout.channel.recv_exit_status() == 0:
                logger.info("Successfully deployed tmux")
            else:
                logger.info("Failed to deploy tmux. Error: {stderr.read().decode('utf-8')}")
    except Exception as e:
        logger.info(f"Error during tmux deployment: {e}")
        return False

# Creating sample file

def create_example_file(ssh):
    try:
        # Create example.txt in the home directory
        create_file_command = 'touch ~/example.txt'
        _, stdout, stderr = ssh.exec_command(create_file_command)

        # Check if the file creation was successful
        if stdout.channel.recv_exit_status() == 0:
            logger.info("Successfully created example.txt")
        else:
            logger.info("Failed to create example.txt. Error: {stderr.read().decode('utf-8')}")
    except Exception as e:
        logger.info(f"Error creating example.txt: {e}")
        return False

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
        vm_identifier = private_key_path.split('/')[-3] if len(private_key_path.split('/')) >= 4 else None
        return hostname, port, username, private_key_path, vm_identifier
    else:
        return None

# Main function

def main():
    # Specify the path to the Vagrant dynamic inventory file
    vagrant_inventory_path = "/home/stafford/Projects/Vagrant/.vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory"

    # Parse the Vagrant inventory to extract connection details
    inventory = parse_inventory_file(vagrant_inventory_path)
    # Define my web server
    web_server_vm = "vm1"
    # Define my NFS server
    nfs_server_vm = "vm2"
    # Defining local and remote path for website files, which is the same path
    website_path = "/var/www/html"
    # Storing information in a list of dictionaries
    connection_details_list = []

    for group, hosts in inventory.items():
        for host in hosts:
            connection_details = extract_connection_details(host, vagrant_inventory_path)
            if connection_details:
                connection_details_list.append({
                    'hostname': connection_details[0],
                    'port': connection_details[1],
                    'username': connection_details[2],
                    'private_key_path': connection_details[3],
                    'vm_identifier': connection_details[4]
                })
                for details in connection_details_list:
                    hostname = details['hostname']
                    port = details['port']
                    username = details['username']
                    private_key_path = details['private_key_path']
                    vm_identifier = details['vm_identifier']
            
            
                logger.info(f"VM: {vm_identifier}, Host: {hostname}, Port: {port}, Username: {username}, Private Key Path: {private_key_path}")
                
                # Establish SSH connection
                ssh_connection = establish_ssh_connection(hostname, port, username, private_key_path)

                if ssh_connection:
                    # Deploy tmux on the remote host
                    deploy_tmux(ssh_connection)
                    # Creating a test file
                    create_example_file(ssh_connection)
                    if vm_identifier == web_server_vm :
                        # Deploy apache on the remote host
                        deploy_apache(ssh_connection)
                        # Use paramiko to scp the website to the web server
                        deploy_website(ssh_connection, website_path)
                    else:
                        logger.info("Skipping web server")
                    if vm_identifier = nfs_server_vm:
                        deploy_nfs_server()
                    # Close the ssh connection
                    ssh_connection.close()
            else:
                logger.info(f"Skipping invalid host line: {host}")

if __name__ == "__main__":
    main()