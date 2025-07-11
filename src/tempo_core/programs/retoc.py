import os
import shutil
import subprocess

import requests

from tempo_core import logger, settings


def get_is_using_retoc_path_override() -> bool:
    return settings.settings_information.settings["retoc_info"][
        "override_default_retoc_path"
    ]


def get_retoc_path_override() -> str:
    return settings.settings_information.settings["retoc_info"]["retoc_path_override"]


def get_retoc_package_path():
    if get_is_using_retoc_path_override():
        return get_retoc_path_override()
    return os.path.join(os.path.expanduser("~"), ".cargo", "bin", "retoc.exe")


def download_and_install_latest_version(repository="trumank/retoc", install_path=None):
    if install_path is None:
        install_path = os.path.join(os.path.expanduser("~"), ".cargo", "bin")

    api_url = f"https://api.github.com/repos/{repository}/releases/latest"

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        release_data = response.json()

        asset = next(
            (
                asset
                for asset in release_data["assets"]
                if asset["name"] == "retoc-installer.ps1"
            ),
            None,
        )

        if asset is None:
            installer_not_found_error = (
                'Asset "retoc-installer.ps1" not found in the latest release.'
            )
            raise RuntimeError(installer_not_found_error)

        asset_url = asset["browser_download_url"]
        script_path = os.path.join(os.environ["TEMP"], "retoc-installer.ps1")
        script_response = requests.get(asset_url)
        script_response.raise_for_status()

        with open(script_path, "wb") as file:
            file.write(script_response.content)

        powershell_exe = shutil.which("powershell")
        if not powershell_exe:
            powershell_not_found_error = "Was unable to find powershell"
            raise FileNotFoundError(powershell_not_found_error)
        subprocess.run(
            [
                powershell_exe,
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                script_path,
            ],
            check=True,
        )

        logger.log_message("Retoc installed successfully.")

    except requests.RequestException as e:
        logger.log_message(f"Error fetching release information: {e}")
    except subprocess.CalledProcessError as e:
        logger.log_message(f"Error executing the installer script: {e}")


def ensure_retoc_installed():
    retoc_path = get_retoc_package_path()

    if os.path.exists(retoc_path):
        logger.log_message(
            f"Retoc is already installed at {retoc_path}. Skipping installation."
        )
        return

    logger.log_message("Retoc executable not found. Proceeding with installation...")

    download_and_install_latest_version()


def get_retoc_version_str_from_engine_version(engine_version: str) -> str:
    # takes in a string like 5.3 or 4.27 and returns a string like UE5_3 or UE4_27
    parts = engine_version.strip().split(".")
    return f'UE{parts[0]}_{parts[1]}' if len(parts) > 1 else f'UE{parts[0]}'



def get_retoc_pak_version_str() -> str:
    # the below code is because we either derive the version from the engine version
    # if not using engine, it can't be derived from the engine, so we need to manually specify
    if settings.get_is_overriding_automatic_version_finding():
        retoc_version_str = settings.settings_information.settings["retoc_info"][
            "retoc_version"
        ]
    else:
        retoc_version_str = get_retoc_version_str_from_engine_version(settings.custom_get_unreal_engine_version(settings.get_unreal_engine_dir()))
    return retoc_version_str
