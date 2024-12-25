import os
import hashlib
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import shutil

class Generator:
    """
    Generates a Kodi addon repository with symlink support
    """

    def __init__(self):
        self.zips_path = "repo/zips"
        self.addons_xml_path = os.path.join(self.zips_path, "addons.xml")
        self.addons_xml_md5_path = os.path.join(self.zips_path, "addons.xml.md5")
        self.symlinks_file = "symlinks.txt"

    def _create_symlinks(self):
        """Creates symlinks defined in symlinks.txt"""
        if os.path.exists(self.symlinks_file):
            with open(self.symlinks_file, 'r') as f:
                for line in f:
                    source, target = line.strip().split('|')
                    source = source.strip()
                    target = target.strip()

                    # Remove existing symlink or directory
                    if os.path.exists(target):
                        if os.path.islink(target):
                            os.unlink(target)
                        elif os.path.isdir(target):
                            shutil.rmtree(target)

                    # Create parent directory if it doesn't exist
                    os.makedirs(os.path.dirname(target), exist_ok=True)

                    # Create symlink
                    if sys.platform == 'win32':
                        # On Windows, we need to handle directory junctions
                        if os.path.isdir(source):
                            os.system(f'mklink /J "{target}" "{source}"')
                        else:
                            os.system(f'mklink "{target}" "{source}"')
                    else:
                        # On Unix systems, we can use os.symlink
                        os.symlink(source, target)

    def _create_zip(self, addon_id, version):
        """Creates a zip file of the addon."""
        addon_folder = addon_id
        zip_folder = os.path.join(self.zips_path, addon_id)
        zip_path = os.path.join(zip_folder, f"{addon_id}-{version}.zip")

        if not os.path.exists(zip_folder):
            os.makedirs(zip_folder)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(addon_folder):
                # Skip .git directories
                if '.git' in dirs:
                    dirs.remove('.git')

                for file in files:
                    if not file.startswith('.'):
                        file_path = os.path.join(root, file)
                        # If it's a symlink, get the real path
                        if os.path.islink(file_path):
                            real_path = os.path.realpath(file_path)
                            if os.path.exists(real_path):
                                file_path = real_path
                        arc_path = os.path.join(addon_id, file_path[len(addon_folder)+1:])
                        zip_file.write(file_path, arc_path)

    def _generate_addons_xml(self):
        """Generates addons.xml file from addon.xml files"""
        addons_root = ET.Element("addons")

        # Process repository addon first
        repo_addon_xml = ET.parse("addon.xml")
        addons_root.append(repo_addon_xml.getroot())

        # Process other addons
        for addon_folder in os.listdir('.'):
            if os.path.isdir(addon_folder) and addon_folder != "repo" and not addon_folder.startswith('.'):
                addon_xml_path = os.path.join(addon_folder, "addon.xml")
                if os.path.exists(addon_xml_path):
                    addon_xml = ET.parse(addon_xml_path)
                    addons_root.append(addon_xml.getroot())

        # Create zips directory if it doesn't exist
        if not os.path.exists(self.zips_path):
            os.makedirs(self.zips_path)

        # Write addons.xml
        tree = ET.ElementTree(addons_root)
        tree.write(self.addons_xml_path, encoding="UTF-8", xml_declaration=True)

        # Generate MD5
        with open(self.addons_xml_path, 'rb') as f:
            m = hashlib.md5()
            m.update(f.read())

        # Write MD5
        with open(self.addons_xml_md5_path, 'w') as f:
            f.write(m.hexdigest())

    def generate_repo(self):
        """Main method to generate repository"""
        # Create symlinks first
        self._create_symlinks()

        # Generate addons.xml and md5
        self._generate_addons_xml()

        # Create zip files
        tree = ET.parse(self.addons_xml_path)
        root = tree.getroot()

        for addon in root.findall('addon'):
            addon_id = addon.get('id')
            version = addon.get('version')
            if os.path.exists(addon_id):
                self._create_zip(addon_id, version)

if __name__ == "__main__":
    gen = Generator()
    gen.generate_repo()
