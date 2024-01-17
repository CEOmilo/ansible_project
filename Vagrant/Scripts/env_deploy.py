import logging
from inventory_parser import InventoryParser
from install_checker import VMManager
from deployment import EnvironmentDeployment
from ssh_connection import SSH

# Setting up logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__) 

# Main function

def main():
    
    # Instantiation of Parser with a file path
    ansible_parser = InventoryParser("/home/stafford/Projects/Vagrant/.vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory")

    # Calling parse_inventory_file on the instance
    inventory_data = ansible_parser.parse_inventory_file()
    
    # Define my server
    server_vm = "vm1"
    
    # Defining local and remote path for website files, which is the same path
    website_path = "/var/www/html"
    
    # Storing information in a list of dictionaries
    connection_details = []

    # Parse the Vagrant inventory to extract connection details
    for group, hosts in inventory_data.items():
        for host in hosts:
            connection_details = ansible_parser.extract_connection_details(host)
            if connection_details:                
                details = {
                    'hostname': connection_details[0],
                    'port': connection_details[1],
                    'username': connection_details[2],
                    'private_key_path': connection_details[3],
                    'vm_identifier': connection_details[4]
                }

                # Access details

                hostname = details['hostname']
                port = details['port']
                username = details['username']
                private_key_path = details['private_key_path']
                vm_identifier = details['vm_identifier']
            
                # Instantiation of my SSH class

                paramiko_ssh = SSH(hostname=hostname, port=port, username=username, private_key_path=private_key_path, logger=logger)
                logger.info(f"VM: {vm_identifier}, Host: {hostname}, Port: {port}, Username: {username}, Private Key Path: {private_key_path}")    
                
                # Establish SSH connection
              
                ssh_connection = paramiko_ssh.establish_ssh_connection()

                # Instantiation of my Environment Deployment class
                environment = EnvironmentDeployment(logger=logger)

                # Instantiation of my VMManager class
                checker = VMManager(ssh=ssh_connection, logger=logger)

                # Instantiation of my FileMaker class
                # files = FileMaker(ssh=ssh_connection, logger=logger)

                if ssh_connection:
                    if vm_identifier == server_vm :
                        checker.set_package_name("apache2")
                        if checker.is_installed():
                            # Deploy apache on the remote host
                            logger.info("apache is already installed on the system.")
                        else:
                            #Deploy apache on the remote host
                            environment.deploy_apache(ssh_connection)
                            # Use paramiko to scp the website to the web server
                            environment.deploy_website(ssh_connection, website_path)
                    if vm_identifier == server_vm:
                        checker.set_package_name("nfs-kernel-server")
                        if checker.is_installed():
                            logger.info("nfs is already installed on the system.")
                        else:
                            #Deploy nfs on the remote host
                            environment.deploy_nfs_server(ssh_connection)
                    if vm_identifier != server_vm:
                        checker.set_package_name("nfs-common")
                        if checker.is_installed():
                            logger.info("nfs is already set-up on client")
                        else:
                            # Deploy nfs for clients
                            environment.client_vms(ssh_connection)
                    else:
                        logger.info("This is the nfs server")
                # Close the ssh connection
                ssh_connection.close()
            else:
                logger.info(f"Skipping invalid host line: {host}")

if __name__ == "__main__":
    main()