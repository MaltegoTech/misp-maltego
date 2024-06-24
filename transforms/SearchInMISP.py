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

from utils.misp_data import misp_events_idinfo, misp_events_galaxy
from maltego_trx.transform import DiscoverableTransform
from utils.misp_connection import get_credentials_from_user


@registry.register_transform(
    display_name="Search In MISP",
    input_entity="maltego.Unknown",
    description="Use % at the front/end for wildcard search",
    output_entities=["maltego.Unknown"],
)
class SearchInMISP(DiscoverableTransform):
    """This is a transform that searches MISP Instance for a given value
    It works for event ids, event infos, misp galaxy objects"""

    @classmethod
    def create_entities(cls, request: MaltegoMsg, response: MaltegoTransform):
        # Get the value from the request
        input_val = (
            request.Value
            or request.getProperty("properties.mispevent")
            or request.Properties.get("properties.mispevent")
        )
        limit = request.Slider
        kw_temp = request.Properties
        keyword = kw_temp.get("properties.temp")

        # call the helper function to get the API_URL and API_KEY values
        api_url, api_key = get_credentials_from_user(request=request)

        # Gets the entity type in following format [{"Name": entity_type_name, "OldName": entity_type_old_name if entity_type_old_name else None}]
        entity_type = request.Genealogy

        # Invokes the appropriate function based on the entity type
        if "MISPEvent" in entity_type[0].get("Name", None):
            misp_events_idinfo(
                input_val=input_val,
                limit=limit,
                response=response,
                api_url=api_url,
                api_key=api_key,
            )
        elif "MISPGalaxy" in entity_type[0].get(
            "Name", None
        ) or "hashtag" in entity_type[0].get("Name", None):
            if keyword is not None:
                if "MISPGalaxy" in entity_type[0].get("Name", None):
                    misp_events_galaxy(
                        entity_type="MISPGalaxy",
                        input_val=input_val,
                        limit=limit,
                        response=response,
                        api_url=api_url,
                        api_key=api_key,
                    )
                if "hashtag" in entity_type[0].get("Name", None) or keyword:
                    misp_events_galaxy(
                        entity_type="hashtag",
                        input_val=input_val,
                        limit=limit,
                        response=response,
                        api_url=api_url,
                        api_key=api_key,
                    )
            else:
                misp_events_galaxy(
                    entity_type="hashtag",
                    input_val=keyword,
                    limit=limit,
                    response=response,
                    api_url=api_url,
                    api_key=api_key,
                )
