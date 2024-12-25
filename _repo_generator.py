#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import hashlib
import zipfile
from xml.dom import minidom
import shutil
from datetime import datetime

class Generator:
    """
    Generates a Kodi addon repository
    """

    def __init__(self):
        """
        Initialize Generator
        """
        self.tools_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__))))
        self.output_path = os.path.join(self.tools_path, "repo")
        self.zips_path = os.path.join(self.output_path, "zips")

        # Create output path if it doesn't exist
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

        # Create zips path if it doesn't exist
        if not os.path.exists(self.zips_path):
            os.makedirs(self.zips_path)

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
                # Remove excessive newlines between elements
                if node.nodeType == node.ELEMENT_NODE:
                    for child in node.childNodes:
                        if child.nodeType == child.TEXT_NODE:
                            child.nodeValue = child.nodeValue.strip()

    def _get_addon_metadata(self, addon_path):
        """
        Extract addon metadata from addon.xml
        """
        path = os.path.join(addon_path, "addon.xml")
        if not os.path.exists(path):
            return None

        try:
            doc = minidom.parse(path)
            addon = doc.getElementsByTagName("addon")[0]
            return {
                "id": addon.getAttribute("id"),
                "version": addon.getAttribute("version")
            }
        except Exception as e:
            print(f"Failed to get metadata for {addon_path}: {str(e)}")
            return None

    def _create_zip(self, addon_path, addon_id, version):
        """
        Create a zip file for the addon
        """
        addon_folder = os.path.join(self.zips_path, addon_id)
        if not os.path.exists(addon_folder):
            os.makedirs(addon_folder)

        final_zip = os.path.join(addon_folder, f"{addon_id}-{version}.zip")

        if not os.path.exists(final_zip):
            zip_file = zipfile.ZipFile(final_zip, 'w', compression=zipfile.ZIP_DEFLATED)
            root_len = len(os.path.dirname(os.path.abspath(addon_path)))

            for root, dirs, files in os.walk(addon_path):
                # Remove any .git folders
                if '.git' in dirs:
                    dirs.remove('.git')

                archive_root = os.path.abspath(root)[root_len:]

                for f in files:
                    fullpath = os.path.join(root, f)
                    archive_name = os.path.join(archive_root, f)

                    if not f.startswith('.'):
                        zip_file.write(fullpath, archive_name, zipfile.ZIP_DEFLATED)

            zip_file.close()

        return final_zip

    def _generate_md5(self, path):
        """
        Generate MD5 hash for a file
        """
        with open(path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def _save_addons_xml(self, addons, path):
        """
        Save addons.xml and addons.xml.md5
        """
        # Clean up the XML
        self._clean_xml(addons.documentElement)

        # Save addons.xml without excessive newlines
        with open(path, 'w', encoding='utf-8') as f:
            addons.writexml(f, encoding='utf-8', indent="  ", newl="\n", addindent="  ")

        # Save addons.xml.md5
        with open(path + '.md5', 'w') as f:
            f.write(self._generate_md5(path))

    def _create_repository_addon(self):
        """
        Create the repository addon zip
        """
        repo_path = os.path.join(self.zips_path, "repository.mikrom")
        if not os.path.exists(repo_path):
            os.makedirs(repo_path)

        # Create the zip file for the repository addon
        zip_path = os.path.join(repo_path, "repository.mikrom-1.0.0.zip")
        if not os.path.exists(zip_path):
            zip_file = zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED)

            # Add addon.xml to the zip
            addon_xml_path = os.path.join(self.tools_path, "addon.xml")
            if os.path.exists(addon_xml_path):
                zip_file.write(addon_xml_path, "addon.xml")

            # Add icon.png and fanart.jpg if they exist
            for asset in ["icon.png", "fanart.jpg"]:
                asset_path = os.path.join(self.tools_path, asset)
                if os.path.exists(asset_path):
                    zip_file.write(asset_path, asset)

            zip_file.close()

    def generate_repo(self):
        """
        Generate the repository
        """
        print("Generating repository...")

        # Create repository addon zip first
        self._create_repository_addon()

        # Create new addons.xml
        addons_xml = minidom.Document()
        addons_root = addons_xml.createElement('addons')
        addons_xml.appendChild(addons_root)

        # Add repository addon to addons.xml first
        repo_addon_path = os.path.join(self.tools_path, "addon.xml")
        if os.path.exists(repo_addon_path):
            repo_doc = minidom.parse(repo_addon_path)
            addons_root.appendChild(repo_doc.getElementsByTagName("addon")[0])

        # Process all other directories in the root
        for addon_folder in os.listdir(self.tools_path):
            # Skip if not a directory or starts with '.' or is 'repo'
            path = os.path.join(self.tools_path, addon_folder)
            if not os.path.isdir(path) or addon_folder.startswith('.') or addon_folder == 'repo':
                continue

            # Get addon metadata
            metadata = self._get_addon_metadata(path)
            if metadata is None:
                print(f"Skipping {addon_folder} - no addon.xml found")
                continue

            print(f"Processing {metadata['id']} version {metadata['version']}")

            # Create zip file
            self._create_zip(path, metadata['id'], metadata['version'])

            # Copy addon.xml to addons.xml
            addon_xml_path = os.path.join(path, "addon.xml")
            doc = minidom.parse(addon_xml_path)
            addons_root.appendChild(doc.getElementsByTagName("addon")[0])

        # Save files
        self._save_addons_xml(addons_xml, os.path.join(self.zips_path, "addons.xml"))
        print("Repository generated successfully!")

if __name__ == "__main__":
    Generator().generate_repo()