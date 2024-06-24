# Author: Sangeetharaj SMB
"""
 Copyright (C) 2024 Maltego Technologies GmbH

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as
 published by the Free Software Foundation, either version 3 of the
 License, or (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.

 You should have received a copy of the GNU Affero General Public License
 along with this program.  If not, see <https://www.gnu.org/licenses/>.
 """

"""Module provides a function to establish MISP Instance connection"""

import os
from typing import Any
from dotenv import load_dotenv  # Import for loading environment variables

from pymisp import PyMISP
from extensions import host_global_setting, api_global_setting


def misp_connection(misp_url=None, misp_key=None):
    """
    Establishes a connection to the MISP instance.

    Checks for environment variables first, then falls back to Maltego transform settings.
    """

    # Check environment variables for MISP credentials (recommended for security)
    load_dotenv()  # Load environment variables
    misp_url_env: str | None = os.getenv("MISP_URL")
    misp_key_env: str | None = os.getenv("MISP_KEY")
    misp_verifycert: bool = (
        False  # Set to True if your MISP instance has a valid SSL certificate
    )
    misp_log: bool = False

    # If environment variables are present, use them
    if misp_url_env and misp_key_env:
        misp_url = misp_url_env
        misp_key = misp_key_env
        print("Using MISP credentials from environment variables.")

    # Connect to MISP using the obtained credentials
    try:
        misp = PyMISP(
            url=misp_url,
            key=misp_key,
            ssl=misp_verifycert,
            debug=misp_log,
            tool="misp_maltego_trx",
        )
        return misp
    except Exception as e:
        raise ValueError(f"Error connecting to MISP: {e}") from e


def get_credentials_from_user(request) -> tuple[Any, Any]:
    """
    Helper function to get credentials from transforms settings from the user
    """
    api_url = request.getTransformSetting(host_global_setting.id)
    api_key = request.getTransformSetting(api_global_setting.id)
    return (api_url, api_key)
