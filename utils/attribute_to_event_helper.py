# Author: Sangeetharaj SMB
"""
 Copyright (C) 2018-2024 Christophe Vandeplas
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

# Code blocks used with permission from here: https://github.com/MISP/MISP-maltego/blob/master/src/MISP_maltego/transforms/common/util.py
# Courtesy Christophe Vandeplas
from typing import Optional, List, Dict

from maltego_trx.maltego import MaltegoTransform

from utils.misp_query import MISPQuery
from utils.misp_data import (
    event_to_entity,
    misp_events_idinfo,
    get_attribute_in_event,
    get_attribute_in_object,
    object_to_entity_result,
    parse_output,
)


def determine_run_type(
    input_val: str,
    property_val: dict,
    entity_type: List[Dict],
    response: MaltegoTransform,
    limit: int,
    api_url: str,
    api_key: str,
) -> None:
    """
    Helper function takes inputs from the main transform entry file,
    based on the entity type flag passes the correct parameters to attribute_to_event function
    """
    entity_type = entity_type[0].get("Name", "")

    if "MISPEvent" in entity_type:
        response.addUIMessage(message="Invalid Entity Type", messageType="Inform")
    elif "MISPGalaxy" in entity_type:
        galaxy_name = property_val.get("mispgalaxy") or input_val
        attribute_to_event(
            input_val=input_val,
            property_val=galaxy_name,
            input_type="mispgalaxy",
            response=response,
            limit=limit,
            api_url=api_url,
            api_key=api_key,
        )
    elif "MISPObject" in entity_type:
        object_name = property_val.get("mispobject") or input_val
        event_id = property_val.get("event_id")
        input_type = "mispobject" if event_id else "mispobject"
        property_val = event_id if event_id else object_name
        attribute_to_event(
            input_val=input_val,
            property_val=property_val,
            input_type=input_type,
            response=response,
            limit=limit,
            api_url=api_url,
            api_key=api_key,
        )
    elif "hashtag" in entity_type:
        hashtag_or_temp = property_val.get("temp") or input_val
        attribute_to_event(
            input_val=input_val,
            property_val=hashtag_or_temp,
            input_type="hash_or_temp",
            response=response,
            limit=limit,
            api_url=api_url,
            api_key=api_key,
        )
    else:
        attribute_to_event(
            input_val=input_val,
            property_val=input_val,
            input_type="standard",
            response=response,
            limit=limit,
            api_url=api_url,
            api_key=api_key,
        )


def attribute_to_event(
    input_val: str,
    property_val: str,
    input_type: str,
    response: MaltegoTransform,
    limit: int,
    api_url: str,
    api_key: str,
) -> Optional[MaltegoTransform]:
    """
    Takes the inputs from the main helper function, invokes the data helpers.
    """
    # from Galaxy
    if "mispgalaxy" in input_type:
        if not property_val:
            return None
        return parse_output(
            input_val=property_val,
            etype="galaxy",
            response=response,
            limit=limit,
            api_url=api_url,
            api_key=api_key,
        )

    # from Object
    elif "mispobject" in input_type:
        try:
            if int(property_val):
                return misp_events_idinfo(
                    input_val=property_val,
                    limit=limit,
                    response=response,
                    api_url=api_url,
                    api_key=api_key,
                )
        except ValueError:
            return misp_events_idinfo(
                input_val=property_val,
                limit=limit,
                response=response,
                api_url=api_url,
                api_key=api_key,
            )

    # from Hashtag
    elif "hash_or_temp" in input_type:
        if not property_val:
            return parse_output(
                input_val=property_val,
                etype="hash_or_temp",
                response=response,
                limit=limit,
                api_url=api_url,
                api_key=api_key,
            )

    # standard Entities (normal attributes)
    else:
        misp_query = MISPQuery(api_url=api_url, api_key=api_key)
        events_json = misp_query.misp_value(
            event_type="value", event_val=input_val, limit=limit
        )

        # return the MISPEvent or MISPObject of the attribute
        for e in events_json:
            # find the value as attribute
            attr = get_attribute_in_event(e, input_val)
            if attr:
                event_to_entity(result=e, response=response)
            # find the value as object
            if "Object" in e["Event"]:
                for o in e["Event"]["Object"]:
                    if get_attribute_in_object(o=o, attribute_value=input_val).get(
                        "value"
                    ):
                        object_to_entity_result(o=o, api_url=api_url, api_key=api_key)
