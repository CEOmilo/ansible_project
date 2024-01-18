import paramiko
import logging

# Setting up logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SSH:

    def __init__(self, hostname, port, username, private_key_path, logger=None):
        self.logger = logger
        self.package_name = None
        self.hostname = hostname
        self.port = port
        self.username = username
        self.private_key_path = private_key_path
        self.ssh = None

    def establish_ssh_connection(self):
        
        # Create an SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # Connect to the remote host using the provided details
            ssh.connect(self.hostname, port=self.port, username=self.username, key_filename=self.private_key_path)
            self.ssh = ssh
            if self.logger:
                self.logger.info(f"SSH connection established to {self.hostname}")
            
            # Return ssh object
            return ssh
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error connecting to {self.hostname}: {e}")
            return None

    def close_ssh_connection(self):
        # Close the SSH connection
        if self.ssh:
            self.ssh.close()
            if self.logger:
                self.logger.info(f"SSH connection closed for {self.hostname}")
