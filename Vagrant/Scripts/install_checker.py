import paramiko
import logging

class VMManager:
        def __init__(self, logger=None, ssh=None):
            self.ssh = ssh
            self.logger = logger
            self.package_name = None
        
        def set_package_name(self, package_name):
            self.package_name = package_name

        def is_installed(self):
            try:
                if self.ssh is None:
                    raise ValueError("SSH object is not initialized.")
                # Check if the package is installed
                _, stdout, _ = self.ssh.exec_command(f"which {self.package_name}")
                return bool(stdout.read().decode('utf-8').strip())
            except Exception as e:
                self.logger.info(f"Error checking {self.package_name} installation: {e}")
            return False
                    