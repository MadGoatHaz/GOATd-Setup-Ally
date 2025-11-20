import os
import pytest
from unittest.mock import MagicMock, patch
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from goatfetch_logic import GoatFetchManager

@pytest.fixture
def mock_fs():
    with patch('goatfetch_logic.Path') as mock_path, \
         patch('goatfetch_logic.shutil') as mock_shutil, \
         patch('goatfetch_logic.glob.glob') as mock_glob:
        yield mock_path, mock_shutil, mock_glob

def test_list_variants(mock_fs):
    _, _, mock_glob = mock_fs
    
    # Mock glob return values
    mock_glob.return_value = [
        "/path/to/assets/variant_1_classic.jsonc",
        "/path/to/assets/variant_2_minimal.jsonc"
    ]
    
    manager = GoatFetchManager()
    variants = manager.list_variants()
    
    assert len(variants) == 2
    assert variants[0] == ("variant_1_classic.jsonc", "Classic")
    assert variants[1] == ("variant_2_minimal.jsonc", "Minimal")

def test_install_logic_flow(mock_fs):
    mock_path, mock_shutil, _ = mock_fs
    
    # Mock Path instances
    mock_config_dir = MagicMock()
    mock_config_file = MagicMock()
    mock_assets_dir = MagicMock()
    mock_source_variant = MagicMock()
    
    mock_path.return_value = mock_config_dir # For recursive calls if needed, but better to mock attributes
    
    # Setup manager with mocked paths
    manager = GoatFetchManager()
    manager.ASSETS_DIR = mock_assets_dir
    manager.CONFIG_DIR = mock_config_dir
    manager.CONFIG_FILE = mock_config_file
    manager.STOCK_BACKUP = MagicMock()
    manager.BACKUP_FILE = MagicMock()
    manager.LOGO_FILE = MagicMock()
    
    # Setup exists() returns
    mock_source_variant.exists.return_value = True
    mock_assets_dir.__truediv__.return_value = mock_source_variant
    
    mock_config_file.exists.return_value = True
    manager.STOCK_BACKUP.exists.return_value = False # Simulate no stock backup yet
    
    # Mock read_text return
    mock_source_variant.read_text.return_value = '{"logo": "LOGO_TYPE_PLACEHOLDER", "source": "LOGO_SOURCE_PLACEHOLDER", "weather": "UserLocationPlaceholder"}'
    
    # Test Install
    manager.install("variant_1_test.jsonc", use_custom_logo=False, weather_location="London")
    
    # Verifications
    manager.ensure_config_dir = MagicMock() # Actually this was called inside install, hard to mock after init unless we patch the class
    # But we can check if mkdir was called on CONFIG_DIR
    mock_config_dir.mkdir.assert_called_with(parents=True, exist_ok=True)
    
    # Check backups
    mock_shutil.copy2.assert_any_call(mock_config_file, manager.STOCK_BACKUP)
    mock_shutil.copy2.assert_any_call(mock_config_file, manager.BACKUP_FILE)
    
    # Check content replacement and write
    # Verify write_text was called
    assert mock_config_file.write_text.called
    
    # Get the content written
    args, _ = mock_config_file.write_text.call_args
    content_written = args[0]
    
    assert '"logo": "auto"' in content_written
    assert '"source": null' in content_written
    assert "London" in content_written
    assert "UserLocationPlaceholder" not in content_written

def test_reset_to_stock(mock_fs):
    _, mock_shutil, _ = mock_fs
    
    manager = GoatFetchManager()
    manager.STOCK_BACKUP = MagicMock()
    manager.CONFIG_FILE = MagicMock()
    
    # Case 1: Stock backup exists
    manager.STOCK_BACKUP.exists.return_value = True
    
    result = manager.reset_to_stock()
    
    assert result is True
    mock_shutil.copy2.assert_called_with(manager.STOCK_BACKUP, manager.CONFIG_FILE)