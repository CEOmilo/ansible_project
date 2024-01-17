import paramiko
import logging
import os
from install_checker import VMManager

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
        logger.info(f"SSH connection established to {hostname}")
        return ssh
    except Exception as e:
        logger.info(f"Error connecting to {hostname}: {e}")
        return None

# Deploying NFS server
def deploy_nfs_server(ssh):
    try:
        logger.info("Deploying ftp server...")
        # Run nfs server deployment commands
        ftp_install_command = "sudo apt-get update && sudo apt-get install -y nfs-kernel-server"
        _, stdout, stderr = ssh.exec_command(ftp_install_command)

        # Check if the installation was successful
        if stdout.channel.recv_exit_status() == 0:
            logger.info("Successfully installed ftp server")
        else:
            logger.info(f"Failed to deploy the ftp server. Error: {stderr.read().decode('utf-8')}")
        
        logger.info("Making shared directory...")
        make_directory_command = "sudo mkdir /share"
        _, stdout, stderr = ssh.exec_command(make_directory_command)
        
        # Change permissions for /etc/exports to allow for writing priveleges and change ownership to vagrant user
        permission_command = "sudo chmod 666 /etc/exports && sudo chown vagrant:vagrant /share"
        _,stdout,stderr = ssh.exec_command(permission_command)
        if stdout.channel.recv_exit_status() == 0:
            logger.info("Successfully changed permissions")
        else:
            logger.info(f"Permissions unchanged. Error: {stderr.read().decode('utf-8')}")
                
        # Specify the local and remote file paths
        local_file_path = '/etc/exports'
        remote_file_path = '/etc/exports'
        
        # Copy the config file and move it to the vm
        logger.info("Copying config file...")
        
        # Open the local file and read its contents
        with open(local_file_path, 'rb') as local_file:
            file_contents = local_file.read()

        # Open the remote file and write the contents
        with ssh.open_sftp() as sftp:
            with sftp.file(remote_file_path, 'wb') as remote_file:
                remote_file.write(file_contents)
        
        # Restarting nfs service
        logger.info("Restarting the nfs service...")
        # Run systemctl deployment commands
        nfs_start_command = "sudo service nfs-kernel-server start && sudo service nfs-kernel-server restart"
        _, stdout, stderr = ssh.exec_command(nfs_start_command)
        exit_status = stdout.channel.recv_exit_status()
        
        return exit_status
    except Exception as e:
        logger.info(f"Error during nfs server deployment: {e}")
        return False
# Setting up client vms for nfs

def client_vms(ssh):
    try:
        # Installing nfs for clients
        logger.info("Installing nfs for clients...")
        nfs_client_command = "sudo apt install nfs-common -y"
        ssh.exec_command(nfs_client_command)
        # Making client directories
        logger.info("Making client directories")
        make_directory_command = "sudo mkdir /client"
        ssh.exec_command(make_directory_command)
        # Changing permissions and ownership
        permission_command = "sudo chmod 666 /client && sudo chown vagrant:vagrant /client"
        _,stdout,stderr = ssh.exec_command(permission_command)
        if stdout.channel.recv_exit_status() == 0:
            logger.info("Successfully changed permissions")
        else:
            logger.info(f"Permissions unchanged. Error: {stderr.read().decode('utf-8')}")
        # Mounting filesystem
        logger.info("Mounting filesystem...")
        mount_command = "sudo mount 192.168.56.3:/share /client && sudo mount -a"
        _,stdout,stderr = ssh.exec_command(mount_command)
        if stdout.channel.recv_exit_status() == 0:
            logger.info("Successfully mounted filesystem")
        else:
            logger.info(f"Not mounted. Error: {stderr.read().decode('utf-8')}")
        return None
    except Exception as e:
        logger.info(f"Error during nfs client deployment: {e}")
        return False
# Deploying apache web server to designated vm

def deploy_apache(ssh):
    try:
        logger.info("Deploying web server...")
        # Run apache deployment commands
        apache_install_command = "sudo apt-get update && sudo apt-get install -y apache2"
        _, stdout, stderr = ssh.exec_command(apache_install_command)

        # Check if the installation was successful
        if stdout.channel.recv_exit_status() == 0:
            logger.info("Successfully installed apache")
        else:
            logger.info(f"Failed to deploy apache. Error: {stderr.read().decode('utf-8')}")
        
        logger.info("Installing php...")
        php_install_command = "sudo apt-get update && sudo apt-get install -y php"
        _, stdout, stderr = ssh.exec_command(apache_install_command)

        # Check if the installation was successful
        if stdout.channel.recv_exit_status() == 0:
            logger.info("Successfully installed php")
        else:
            logger.info(f"Failed to deploy apache. Error: {stderr.read().decode('utf-8')}")

        
        return None
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
        for dir in dirs:
            remote_dir = os.path.join(website_path, os.path.relpath(os.path.join(root, dir), website_path))
        
            # Ensure remote directory exists
            try:
                sftp.stat(remote_dir)
            except FileNotFoundError:
                # Remote directory doesn't exist, create it
                sftp.mkdir(remote_dir)

        for file in files:
            local_file_path = os.path.join(root, file)
            remote_file_path = os.path.join(website_path, os.path.relpath(local_file_path, website_path))

            # Upload the file
            sftp.put(local_file_path, remote_file_path)

    sftp.close()

# Creating sample file

def create_testing_files(ssh):
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
    server_vm = "vm1"
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
                # Creating an instance of my VMManager class
                checker = VMManager(ssh=ssh_connection, logger=logger)

                if ssh_connection:
                    # Creating a test file
                    create_example_file(ssh_connection)
                    if vm_identifier == server_vm :
                        checker.set_package_name("apache2")
                        if checker.is_installed():
                            # Deploy apache on the remote host
                            logger.info("apache is already installed on the system.")
                        else:
                            #Deploy apache on the remote host
                            deploy_apache(ssh_connection)
                            # Use paramiko to scp the website to the web server
                            deploy_website(ssh_connection, website_path)
                    if vm_identifier == server_vm:
                        checker.set_package_name("nfs-kernel-server")
                        if checker.is_installed():
                            # Deploy nfs server on the remote host
                            logger.info("nfs is already installed on the system.")
                        else:
                            #Deploy nfs on the remote host
                            deploy_nfs_server(ssh_connection)
                    if vm_identifier != server_vm:
                        client_vms(ssh_connection)
                    else:
                        logger.info("This is the nfs server")
                # Close the ssh connection
                ssh_connection.close()
            else:
                logger.info(f"Skipping invalid host line: {host}")

if __name__ == "__main__":
    main()