import os
import shutil
import glob
import tempfile
import subprocess
from pathlib import Path

class GoatFetchManager:
    ASSETS_DIR = Path(__file__).parent / "assets" / "goatfetch"
    CONFIG_DIR = Path(os.path.expanduser("~/.config/fastfetch"))
    CONFIG_FILE = CONFIG_DIR / "config.jsonc"
    LOGO_FILE = CONFIG_DIR / "logo.txt"
    BACKUP_FILE = CONFIG_DIR / "config.jsonc.bak"
    STOCK_BACKUP = CONFIG_DIR / "config.jsonc.stock"
    
    def __init__(self):
        pass

    def ensure_config_dir(self):
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def list_variants(self):
        """Returns a list of tuples (filename, display_name)"""
        variants = []
        pattern = str(self.ASSETS_DIR / "variant_*.jsonc")
        files = sorted(glob.glob(pattern))
        
        for f in files:
            filename = os.path.basename(f)
            # simple parsing: variant_1_classic.jsonc -> Classic
            parts = filename.replace(".jsonc", "").split("_")
            if len(parts) >= 3:
                name = " ".join(word.capitalize() for word in parts[2:])
                variants.append((filename, name))
            else:
                variants.append((filename, filename))
        
        return variants

    def read_logo(self):
        """Reads the logo.txt content"""
        logo_path = self.ASSETS_DIR / "logo.txt"
        if logo_path.exists():
            return logo_path.read_text(encoding="utf-8")
        return ""

    def install(self, variant_filename, use_custom_logo, weather_location, log_callback=None):
        """
        Installs the selected variant.
        variant_filename: filename of the jsonc file in assets
        use_custom_logo: boolean
        weather_location: string (empty for auto)
        log_callback: optional function to log messages
        """
        def log(msg):
            if log_callback:
                log_callback(msg)

        self.ensure_config_dir()
        
        source_variant = self.ASSETS_DIR / variant_filename
        if not source_variant.exists():
            raise FileNotFoundError(f"Variant file {source_variant} not found")

        # 1. Handle Stock Backup
        if self.CONFIG_FILE.exists() and not self.STOCK_BACKUP.exists():
            log("Creating stock backup...")
            shutil.copy2(self.CONFIG_FILE, self.STOCK_BACKUP)

        # 2. Handle Current Backup
        if self.CONFIG_FILE.exists():
            log("Backing up current configuration...")
            shutil.copy2(self.CONFIG_FILE, self.BACKUP_FILE)

        # 3. Read Variant Content
        log(f"Reading variant: {variant_filename}")
        config_content = source_variant.read_text(encoding="utf-8")

        # 4. Handle Logo Logic
        if use_custom_logo:
            log("Configuring custom logo...")
            # Copy logo file
            source_logo = self.ASSETS_DIR / "logo.txt"
            if source_logo.exists():
                shutil.copy2(source_logo, self.LOGO_FILE)
            
            # Replace placeholders
            config_content = config_content.replace("LOGO_TYPE_PLACEHOLDER", "file")
            config_content = config_content.replace("LOGO_SOURCE_PLACEHOLDER", str(self.LOGO_FILE))
        else:
            log("Configuring default logo...")
            # Default OS logo
            config_content = config_content.replace("LOGO_TYPE_PLACEHOLDER", "auto")
            # Replace "LOGO_SOURCE_PLACEHOLDER" (quoted) with null (unquoted)
            config_content = config_content.replace('"LOGO_SOURCE_PLACEHOLDER"', "null")

        # 5. Handle Weather
        if weather_location and weather_location.strip():
            log(f"Setting weather location: {weather_location}")
            config_content = config_content.replace("UserLocationPlaceholder", weather_location.strip())
        else:
            log("Setting weather location: Auto")
            # Auto-detect: replace "UserLocationPlaceholder" (quoted) with null
            config_content = config_content.replace('"UserLocationPlaceholder"', "null")

        # 6. Write Config
        log("Writing new configuration...")
        self.CONFIG_FILE.write_text(config_content, encoding="utf-8")
        log("Installation complete.")

    def revert(self, log_callback=None):
        """Restores from backup if available"""
        if self.BACKUP_FILE.exists():
            if log_callback:
                log_callback("Restoring from backup...")
            shutil.copy2(self.BACKUP_FILE, self.CONFIG_FILE)
            if log_callback:
                log_callback("Restore complete.")
            return True
        return False
    
    def generate_preview_config(self, variant_filename, use_custom_logo, weather_location):
        """
        Generates a temporary configuration file for preview.
        Returns the path to the temporary file.
        """
        source_variant = self.ASSETS_DIR / variant_filename
        if not source_variant.exists():
            raise FileNotFoundError(f"Variant file {source_variant} not found")

        config_content = source_variant.read_text(encoding="utf-8")
        
        # Logo logic for preview
        if use_custom_logo:
            source_logo = self.ASSETS_DIR / "logo.txt"
            if source_logo.exists():
                # For preview, we point directly to the asset logo file if possible,
                # or we might need to copy it if fastfetch needs it in a specific place.
                # Since fastfetch takes an absolute path, pointing to ASSETS_DIR/logo.txt should work.
                config_content = config_content.replace("LOGO_TYPE_PLACEHOLDER", "file")
                config_content = config_content.replace("LOGO_SOURCE_PLACEHOLDER", str(source_logo))
        else:
            config_content = config_content.replace("LOGO_TYPE_PLACEHOLDER", "auto")
            config_content = config_content.replace('"LOGO_SOURCE_PLACEHOLDER"', "null")

        # Weather logic
        if weather_location and weather_location.strip():
            config_content = config_content.replace("UserLocationPlaceholder", weather_location.strip())
        else:
            config_content = config_content.replace('"UserLocationPlaceholder"', "null")

        # Create temp file
        fd, path = tempfile.mkstemp(suffix=".jsonc", text=True)
        with os.fdopen(fd, 'w') as f:
            f.write(config_content)
        
        return path

    def run_fastfetch_preview(self, config_path):
        """
        Runs fastfetch with the given config path and returns the output.
        """
        try:
            # We rely on 'fastfetch' being in the PATH
            result = subprocess.run(
                ["fastfetch", "--config", config_path],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return f"Error running fastfetch:\n{result.stderr}"
            return result.stdout
        except Exception as e:
            return f"Exception running fastfetch: {e}"
        finally:
            # Clean up temp file
            if os.path.exists(config_path):
                os.unlink(config_path)
        
    def reset_to_stock(self, log_callback=None):
        """Restores the original stock config if it exists, or clears config"""
        if self.STOCK_BACKUP.exists():
            if log_callback:
                log_callback("Restoring stock configuration...")
            shutil.copy2(self.STOCK_BACKUP, self.CONFIG_FILE)
            return True
        elif self.CONFIG_FILE.exists():
             # If no stock backup but config exists, maybe delete it?
             # The original script does `rm -rf "${HOME}/.config/fastfetch/"*`
             # Safer to just remove the file we manage.
             if log_callback:
                log_callback("No stock backup found. Removing current config...")
             self.CONFIG_FILE.unlink()
             return True
        return False