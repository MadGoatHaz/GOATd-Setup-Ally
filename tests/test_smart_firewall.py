import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src execution path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from config import apply_firewall, get_installed_packages_sync
from apps import APPS_CATEGORIES

class TestSmartFirewall(unittest.TestCase):

    @patch('config.get_installed_packages_sync')
    @patch('subprocess.run')
    def test_apply_firewall_steam_installed(self, mock_subprocess, mock_get_packages):
        # Mock installed packages to include steam
        mock_get_packages.return_value = {'steam'}
        
        # Mock subprocess.run to return success
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "success"

        result = apply_firewall()

        # Check if firewall commands for Steam ports were generated
        expected_ports = ["27031/udp", "27036/udp", "27015/tcp", "27036/tcp"]
        
        calls = mock_subprocess.call_args_list
        command_strings = [call[0][0] for call in calls]
        
        # Check for each port command
        for port in expected_ports:
            found = False
            for cmd_str in command_strings:
                if f"--add-port={port}" in cmd_str:
                    found = True
                    break
            self.assertTrue(found, f"Command for port {port} not found")

        # Check for reload command
        self.assertTrue(any("firewall-cmd --reload" in cmd for cmd in command_strings))

    @patch('config.get_installed_packages_sync')
    @patch('subprocess.run')
    def test_apply_firewall_kdeconnect_installed(self, mock_subprocess, mock_get_packages):
        # Mock installed packages to include kdeconnect
        mock_get_packages.return_value = {'kdeconnect'}
        
        # Mock subprocess.run to return success
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "success"

        result = apply_firewall()

        # Check if firewall commands for KDE Connect ports were generated
        expected_ports = ["1714-1764/tcp", "1714-1764/udp"]
        
        calls = mock_subprocess.call_args_list
        command_strings = [call[0][0] for call in calls]
        
        # Check for each port command
        for port in expected_ports:
            found = False
            for cmd_str in command_strings:
                if f"--add-port={port}" in cmd_str:
                    found = True
                    break
            self.assertTrue(found, f"Command for port {port} not found")

    @patch('config.get_installed_packages_sync')
    @patch('subprocess.run')
    def test_apply_firewall_none_installed(self, mock_subprocess, mock_get_packages):
        # Mock installed packages to be empty
        mock_get_packages.return_value = set()

        result = apply_firewall()

        self.assertIn("No installed applications found that require specific firewall ports.", result)
        mock_subprocess.assert_not_called()

if __name__ == '__main__':
    unittest.main()