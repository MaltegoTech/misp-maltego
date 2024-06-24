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

from maltego_trx.decorator_registry import TransformRegistry, TransformSetting

host_global_setting = TransformSetting(
    "misp_instance_url",
    "Misp Instance URL",
    setting_type="string",
    default_value="",
    global_setting=True,
)
api_global_setting = TransformSetting(
    "misp_api_key",
    "Misp API key",
    setting_type="string",
    default_value="",
    global_setting=True,
)

registry = TransformRegistry(
    owner="Maltego Technologies GmbH",
    author="Sangeeth <sb@maltego.com>",
    host_url="http://192.168.1.147:8080",
    seed_ids=["misptrx"],
)

registry.global_settings = [host_global_setting, api_global_setting]

# The rest of these attributes are optional

# metadata
registry.version = "0.1"

# global settings
# from maltego_trx.template_dir.settings import api_key_setting
# registry.global_settings = [api_key_setting]

# transform suffix to indicate datasource
# registry.display_name_suffix = " [ACME]"

# reference OAuth settings
# registry.oauth_settings_id = ['github-oauth']
