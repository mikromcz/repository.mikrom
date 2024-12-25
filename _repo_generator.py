import os
import hashlib
from xml.dom import minidom
import zipfile

class Generator:
    """
    Generates Kodi repository files
    """

    def __init__(self):
        self.tools_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__))))
        self.repo_path = os.path.join(self.tools_path, "repo")

        # Create repo path if it doesn't exist
        if not os.path.exists(self.repo_path):
            os.makedirs(self.repo_path)

    def _clean_xml(self, element):
        """
        Remove empty text nodes and excessive whitespace
        """
        for node in element.childNodes[:]:
            if node.nodeType == node.TEXT_NODE:
                if node.nodeValue.strip() == "":
                    element.removeChild(node)
            else:
                self._clean_xml(node)
                if node.nodeType == node.ELEMENT_NODE:
                    for child in node.childNodes:
                        if child.nodeType == child.TEXT_NODE:
                            child.nodeValue = child.nodeValue.strip()

    def _create_repository_zip(self):
        """
        Create the repository addon zip
        """
        repo_path = os.path.join(self.repo_path, "repository.mikrom")
        if not os.path.exists(repo_path):
            os.makedirs(repo_path)

        # Create the zip file for the repository addon
        zip_path = os.path.join(repo_path, "repository.mikrom-1.0.0.zip")
        if not os.path.exists(zip_path):
            zip_file = zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED)

            # Add addon.xml to the zip inside repository.mikrom folder
            addon_xml_path = os.path.join(self.tools_path, "addon.xml")
            if os.path.exists(addon_xml_path):
                zip_file.write(addon_xml_path, "repository.mikrom/addon.xml")

            # Add icon.png and fanart.jpg if they exist
            for asset in ["icon.png", "fanart.jpg"]:
                asset_path = os.path.join(self.tools_path, asset)
                if os.path.exists(asset_path):
                    zip_file.write(asset_path, f"repository.mikrom/{asset}")

            zip_file.close()

    def _generate_md5(self, path):
        """
        Generate MD5 hash for a file
        """
        with open(path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def _get_version_from_zip(self, zip_path):
        """
        Extract addon version from addon.xml in the zip file
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Find addon.xml file
                addon_xml = None
                for filename in zip_ref.namelist():
                    if filename.endswith('addon.xml'):
                        addon_xml = filename
                        break

                if addon_xml:
                    with zip_ref.open(addon_xml) as f:
                        doc = minidom.parse(f)
                        addon = doc.getElementsByTagName("addon")[0]
                        return addon.getAttribute("version")
        except Exception as e:
            print(f"Error reading zip {zip_path}: {str(e)}")
        return None

    def generate_repo(self):
        """
        Generate the repository
        """
        print("Generating repository files...")

        # Create repository addon zip first
        self._create_repository_zip()

        # Create new addons.xml
        addons_xml = minidom.Document()
        addons_root = addons_xml.createElement('addons')
        addons_xml.appendChild(addons_root)

        # Add repository addon to addons.xml first
        repo_addon_path = os.path.join(self.tools_path, "addon.xml")
        if os.path.exists(repo_addon_path):
            repo_doc = minidom.parse(repo_addon_path)
            addons_root.appendChild(repo_doc.getElementsByTagName("addon")[0])

        # Process addon folders in repo directory
        for addon_folder in os.listdir(self.repo_path):
            folder_path = os.path.join(self.repo_path, addon_folder)
            if not os.path.isdir(folder_path) or addon_folder.startswith('.'):
                continue

            # Find the latest version zip file
            zip_files = [f for f in os.listdir(folder_path) if f.endswith('.zip')]
            if not zip_files:
                continue

            latest_zip = None
            latest_version = None

            for zip_file in zip_files:
                zip_path = os.path.join(folder_path, zip_file)
                version = self._get_version_from_zip(zip_path)
                if version:
                    if latest_version is None or version > latest_version:
                        latest_version = version
                        latest_zip = zip_path

            if latest_zip:
                # Extract addon.xml from the zip and add to addons.xml
                with zipfile.ZipFile(latest_zip, 'r') as zip_ref:
                    addon_xml = None
                    for filename in zip_ref.namelist():
                        if filename.endswith('addon.xml'):
                            addon_xml = filename
                            break

                    if addon_xml:
                        with zip_ref.open(addon_xml) as f:
                            doc = minidom.parse(f)
                            addon = doc.getElementsByTagName("addon")[0]
                            print(f"Processing {addon.getAttribute('id')} version {addon.getAttribute('version')}")
                            addons_root.appendChild(addon)

        # Clean up and save addons.xml
        self._clean_xml(addons_xml.documentElement)
        addons_xml_path = os.path.join(self.repo_path, "addons.xml")
        with open(addons_xml_path, 'w', encoding='utf-8') as f:
            addons_xml.writexml(f, encoding='utf-8', indent="  ", newl="\n", addindent="  ")

        # Generate MD5
        with open(addons_xml_path + '.md5', 'w') as f:
            f.write(self._generate_md5(addons_xml_path))

        print("Repository files generated successfully!")

if __name__ == "__main__":
    Generator().generate_repo()
