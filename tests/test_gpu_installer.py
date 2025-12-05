import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to sys.path to ensure we can import the module if running directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import gpu_installer

class TestGpuInstaller(unittest.TestCase):

    def setUp(self):
        # Clear the lru_cache before each test to ensure mocks work correctly
        gpu_installer.detect_aur_helper.cache_clear()

    @patch('src.gpu_installer.shutil.which')
    def test_detect_aur_helper_paru(self, mock_which):
        # Mock shutil.which to return True for paru
        def side_effect(arg):
            if arg == 'paru':
                return '/usr/bin/paru'
            return None
        mock_which.side_effect = side_effect
    
        helper = gpu_installer.detect_aur_helper()
        self.assertEqual(helper, 'paru')

    @patch('src.gpu_installer.shutil.which')
    def test_detect_aur_helper_yay(self, mock_which):
        # Mock shutil.which to return False for paru, True for yay
        def side_effect(arg):
            if arg == 'paru':
                return None
            if arg == 'yay':
                return '/usr/bin/yay'
            return None
        mock_which.side_effect = side_effect
    
        helper = gpu_installer.detect_aur_helper()
        self.assertEqual(helper, 'yay')

    @patch('src.gpu_installer.shutil.which')
    def test_detect_aur_helper_none(self, mock_which):
        # Mock shutil.which to return None for all
        mock_which.return_value = None

        helper = gpu_installer.detect_aur_helper()
        self.assertIsNone(helper)

    @patch('src.gpu_installer.get_distro_id')
    @patch('src.gpu_installer.detect_aur_helper')
    def test_get_installation_plan_nvidia_beta(self, mock_detect_helper, mock_get_distro):
        # Setup mocks
        mock_get_distro.return_value = 'arch'
        mock_detect_helper.return_value = 'paru'

        # Test with type_beta
        plan = gpu_installer.get_installation_plan(
            vendor_id='nvidia',
            workloads={'gaming'},
            driver_type='type_beta'
        )

        # Verify beta packages are in aur_packages
        self.assertIn('nvidia-beta-dkms', plan['aur_packages'])
        self.assertIn('nvidia-utils-beta', plan['aur_packages'])
        self.assertIn('lib32-nvidia-utils-beta', plan['aur_packages']) # added because of 'gaming'
        
        # Verify no standard packages that shouldn't be there
        self.assertNotIn('nvidia-dkms', plan['packages'])

    @patch('src.gpu_installer.get_distro_id')
    def test_get_installation_plan_nvidia_opensource(self, mock_get_distro):
        # Setup mocks (Arch Linux scenario)
        mock_get_distro.return_value = 'arch'

        # Test with type_opensource (type_open)
        plan = gpu_installer.get_installation_plan(
            vendor_id='nvidia',
            workloads={'gaming'},
            driver_type='type_open'
        )

        # Verify open source packages
        self.assertIn('nvidia-open-dkms', plan['packages'])
        self.assertIn('lib32-nvidia-utils', plan['packages'])
        
        # Verify beta packages are NOT present
        self.assertNotIn('nvidia-beta-dkms', plan['aur_packages'])

    @patch('src.gpu_installer.detect_aur_helper')
    @patch('src.gpu_installer.getpass.getuser')
    def test_generate_installation_command_beta(self, mock_getuser, mock_detect_helper):
        mock_getuser.return_value = 'testuser'
        mock_detect_helper.return_value = 'paru'

        # Construct a fake plan with beta packages
        plan = {
            "groups": ["video"],
            "aur_packages": ["nvidia-beta-dkms", "nvidia-utils-beta"],
            "packages": [],
            "post_install_cmds": ["sudo mkinitcpio -P"],
            "services": []
        }

        cmd = gpu_installer.generate_installation_command(plan)
        
        # Verify it uses the detected AUR helper
        self.assertIn('paru -S --noconfirm', cmd)
        self.assertIn('nvidia-beta-dkms', cmd)
        self.assertIn('sudo usermod -aG video testuser', cmd)

        # Verify conflict removal command is present
        self.assertIn('pkgs_to_remove=$(pacman -Qq', cmd)
        self.assertIn('nvidia-dkms', cmd)
        self.assertIn('nvidia-open-dkms', cmd)
        self.assertIn('if [ -n "$pkgs_to_remove" ]; then', cmd)
        self.assertIn('sudo pacman -Rdd --noconfirm $pkgs_to_remove', cmd)

        # Verify mkinitcpio replacement logic
        self.assertIn('if command -v mkinitcpio >/dev/null; then sudo mkinitcpio -P', cmd)

    @patch('src.gpu_installer.detect_aur_helper')
    @patch('src.gpu_installer.getpass.getuser')
    def test_generate_installation_command_opensource(self, mock_getuser, mock_detect_helper):
        mock_getuser.return_value = 'testuser'
        mock_detect_helper.return_value = 'paru' # Even if installed, shouldn't use if no aur_packages

        # Construct a fake plan with standard packages
        plan = {
            "groups": ["video"],
            "aur_packages": [],
            "packages": ["nvidia-open-dkms", "nvidia-utils"],
            "post_install_cmds": [],
            "services": []
        }

        cmd = gpu_installer.generate_installation_command(plan)
        
        # Verify it uses pacman
        self.assertIn('sudo pacman -S --noconfirm', cmd)
        self.assertIn('nvidia-open-dkms', cmd)
        
        # Verify it does NOT use AUR helper for standard packages
        self.assertNotIn('paru -S', cmd)

    @patch('src.gpu_installer.detect_aur_helper')
    @patch('src.gpu_installer.getpass.getuser')
    def test_generate_installation_command_remove_beta_when_standard(self, mock_getuser, mock_detect_helper):
        mock_getuser.return_value = 'testuser'
        mock_detect_helper.return_value = 'paru'

        # Construct a fake plan with standard packages
        plan = {
            "groups": ["video"],
            "aur_packages": [],
            "packages": ["nvidia-dkms", "nvidia-utils"],
            "post_install_cmds": ["sudo mkinitcpio -P"],
            "services": []
        }

        cmd = gpu_installer.generate_installation_command(plan)
        
        # Verify conflict removal command for Beta is present
        self.assertIn('pkgs_to_remove=$(pacman -Qq', cmd)
        self.assertIn('nvidia-beta-dkms', cmd)
        self.assertIn('nvidia-utils-beta', cmd)
        self.assertIn('if [ -n "$pkgs_to_remove" ]; then', cmd)
        self.assertIn('sudo pacman -Rdd --noconfirm $pkgs_to_remove', cmd)

        # Verify mkinitcpio replacement logic
        self.assertIn('if command -v mkinitcpio >/dev/null; then sudo mkinitcpio -P', cmd)

if __name__ == '__main__':
    unittest.main()