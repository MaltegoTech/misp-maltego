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

from maltego_trx.decorator_registry import TransformSetting

api_key_setting = TransformSetting(
    name="api_key", display_name="API Key", setting_type="string", global_setting=True
)

language_setting = TransformSetting(
    name="language",
    display_name="Language",
    setting_type="string",
    default_value="en",
    optional=True,
    popup=True,
)
