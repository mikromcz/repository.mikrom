import os
import hashlib
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime

class Generator:
    """
    Generates a Kodi addon repository
    """
    
    def __init__(self):
        self.zips_path = "repo/zips"
        self.addons_xml_path = os.path.join(self.zips_path, "addons.xml")
        self.addons_xml_md5_path = os.path.join(self.zips_path, "addons.xml.md5")

    def _create_zip(self, addon_id, version):
        """Creates a zip file of the addon."""
        addon_folder = addon_id
        zip_folder = os.path.join(self.zips_path, addon_id)
        zip_path = os.path.join(zip_folder, f"{addon_id}-{version}.zip")
        
        if not os.path.exists(zip_folder):
            os.makedirs(zip_folder)
            
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(addon_folder):
                for file in files:
                    if not file.startswith('.'):
                        file_path = os.path.join(root, file)
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
  
