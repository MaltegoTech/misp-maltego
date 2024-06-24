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

from extensions import registry

from maltego_trx.maltego import MaltegoMsg, MaltegoTransform

from utils.misp_data import object_to_attributes_helper
from maltego_trx.transform import DiscoverableTransform
from utils.misp_connection import get_credentials_from_user


@registry.register_transform(
    display_name="To Attributes",
    input_entity="maltego.misp.MISPObject",
    description="From MISP Object To Attributes",
    output_entities=["maltego.Unknown"],
)
class ObjectToAttributes(DiscoverableTransform):
    """This transform searches MISP Instance
    for a given object and returns Attributes"""

    @classmethod
    def create_entities(cls, request: MaltegoMsg, response: MaltegoTransform):
        # Get the value from the request
        event_id = request.getProperty("event_id")
        uuid = request.getProperty("uuid")

        # call the helper function to get the API_URL and API_KEY values
        api_url, api_key = get_credentials_from_user(request=request)

        object_to_attributes_helper(
            event_id, uuid, response, api_url=api_url, api_key=api_key
        )
