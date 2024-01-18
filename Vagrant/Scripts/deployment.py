import logging
import os
from inventory_parser import InventoryParser

# Setting up logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__) 

class EnvironmentDeployment:
    
    def __init__(self, vm_identifier):
        self.logger = logger
        self.package_name = None
        self.vm_identifier = vm_identifier

    # Deploying NFS server
    
    def deploy_nfs_server(self, ssh):
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
            permission_command = "sudo chmod 777 /etc/exports && sudo chown vagrant:vagrant /share"
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

    def client_vms(self, ssh):
        try:
            # Installing nfs for clients
            logger.info("Installing nfs for clients...")
            nfs_client_command = "sudo apt install nfs-common -y"
            _, stdout, stderr = ssh.exec_command(nfs_client_command)
            exit_status = stdout.channel.recv_exit_status()

            if exit_status == 0:
                self.logger.info("Successfully installed nfs-common")
            else:
                self.logger.error(f"Failed to install nfs-common. Error: {stderr.read().decode('utf-8')}")
                return False

            # Making client directories
            logger.info("Making client directories")
            make_directory_command = "sudo mkdir -p /client"
            ssh.exec_command(make_directory_command)

            # Changing permissions and ownership
            permission_command = "sudo chmod 755 /client && sudo chown vagrant:vagrant /client" # Directories have to be executable
            _,stdout,stderr = ssh.exec_command(permission_command)
            if stdout.channel.recv_exit_status() == 0:
               logger.info("Successfully changed permissions")
            else:
              logger.info(f"Permissions unchanged. Error: {stderr.read().decode('utf-8')}")
            # Mounting filesystem
            logger.info("Mounting filesystem...")
            mount_command = "sudo mount 192.168.56.5:/share /client"
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

    def deploy_apache(self, ssh):
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
            _, stdout, stderr = ssh.exec_command(php_install_command)

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

    def deploy_website(self, ssh, website_path):
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
    
    def example_files(self, ssh, vm_identifier):
        file_name = (f"I_am_from_{vm_identifier}.txt")
        content = input(f"Enter the content for {file_name}: ")
        
        try:
            # Specify the local and remote file paths
            local_file_path = f"/home/stafford/Projects/Vagrant/{file_name}"
            remote_file_path = f'/home/vagrant/{file_name}' # Never use the tilde, unless you want an hour of your time wasted

            # Create file
            with open(local_file_path, 'w') as local_file:
                local_file.write(content)

            # Copy the config file and move it to the vm
            self.logger.info(f"Transferring {local_file_path}...")
            with ssh.open_sftp() as sftp:
                sftp.put(local_file_path, remote_file_path)            
            self.logger.info(f"{file_name} created and transferred to the VM successfully")

            # Remove the local file
            os.remove(local_file_path)

            if vm_identifier != "vm3":
                # Use sudo to move from home directory to nfs-shared directory
                self.logger.info("Moving to shared client directory")
                _,stdout, stderr = ssh.exec_command(f"sudo mv ~/{file_name} /client")
                if stdout.channel.recv_exit_status() == 0:
                    self.logger.info("Successfully moved to shared directory")
                else:
                    self.logger.info(f"Failed to move. Error: {stderr.read().decode('utf-8')}")
            else:
                 # Use sudo to move from home directory to nfs-shared directory
                self.logger.info("Moving to shared server directory")
                _,stdout, stderr = ssh.exec_command(f"sudo mv ~/{file_name} /share")
                if stdout.channel.recv_exit_status() == 0:
                    self.logger.info("Successfully moved to shared directory")
                else:
                    self.logger.info(f"Failed to move. Error: {stderr.read().decode('utf-8')}")

        except Exception as e:
            self.logger.error(f"Error creating and transferring {file_name} to the VM: {e}")