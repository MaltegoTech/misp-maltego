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

from typing import Union

from maltego_trx.maltego import MaltegoTransform
from utils.misp_connection import misp_connection

# Connect to MISP using the misp_connection
# misp = misp_connection()


class MISPQuery:
    def __init__(self, api_url: str, api_key: str):
        # Connect to MISP using the misp_connection
        self.misp = misp_connection(api_url, api_key)

    def misp_query_idinfo(
        self, event_type: str, event_val: Union[str, int], limit: int
    ) -> dict:
        """Takes an input value (could be int or str), a flag, and a limit and searches
        events with either id or info in MISP instance with the configured settings, and returns a JSON object"""

        if "id" in event_type:
            events = self.misp.search(
                controller="events",
                eventid=event_val,
                limit=limit,
                with_attachments=False,
            )
        elif "info" in event_type:
            events = self.misp.search(
                controller="events",
                eventinfo=event_val,
                limit=limit,
                with_attachments=False,
            )

        return generate_entity_details_idinfo(events)

    def misp_query_attr(
        self, event_type: str, event_val: str, limit: int
    ) -> MaltegoTransform:
        """Takes an input value (could be int or str), a flag, and a limit
        and searches for either galaxies or tags in MISP instance with the configured settings, and returns a JSON object"""

        if "galaxy" in event_type:
            events = self.misp.search(
                controller="events", tags=event_val, limit=limit, with_attachments=False
            )
        elif "hash_or_temp" in event_type:
            events = self.misp.search_index(tags=event_val)

        for event in events:
            return generate_entity_details_attr(event)

    def from_hashtag(self, value: str) -> str:
        """
        Takes an input searches for tags and returns the value
        """
        result = self.misp.direct_call("tags/search", {"name": value})
        for t in result:
            # skip misp-galaxies as we have processed them earlier on
            if t["Tag"]["name"].startswith("misp-galaxy"):
                continue
            # In this case we do not filter away those we add as notes, as people might want to pivot on it explicitly.
            return t["Tag"]["name"]

    def to_attribute(self, value: str, limit: int) -> dict:
        """
        Takes an input and returns a JSON object
        """
        return self.misp.search(
            controller="attributes", value=value, limit=limit, with_attachments=False
        )

    def get_object_template(self, val: str) -> dict:
        """
        Takes an input and returns a JSON object
        """
        return self.misp.get_object_template(val)

    def obj_to_attribute(self, event_id: int) -> dict:
        """
        Takes an input and returns a JSON object
        """
        return self.misp.get_event(event_id)

    def event_to_transform_details(self, input_val: int, limit: int) -> dict:
        """
        Takes an input and returns a JSON object
        """
        return self.misp.search(
            controller="events", eventid=input_val, with_attachments=False, limit=limit
        )

    def misp_value(self, event_type: str, event_val: str, limit: int) -> dict:
        """
        Takes an input and returns a JSON object
        """
        if "value" in event_type:
            return self.misp.search(
                controller="events",
                value=event_val,
                limit=limit,
                with_attachments=False,
            )


def generate_entity_details_idinfo(events: dict) -> list:
    """
    Takes a dictionary and returns a list for building an entity
    """
    result_list = []
    if events:
        for event_dict in events:
            event = event_dict.get("Event", {})  # Safely get the 'Event' dictionary
            if event:
                event_id = event.get("id")
                uuid = event.get("uuid")
                event_info = event.get("info")
                event_tag = event.get("Tag")

                result = {
                    "event_id": event_id,
                    "uuid": uuid,
                    "event_info": event_info,
                    "event_tag": event_tag,
                }
                result_list.append(result)

    return result_list


def generate_entity_details_attr(events: dict) -> list:
    """
    Takes a dictionary and returns a list for building an entity
    """
    result_list = []
    if events:
        event_id = events["Event"]["id"]
        uuid = events["Event"]["uuid"]
        event_info = events["Event"]["info"]
        event_tag = events["Event"]["Tag"]

        result = {
            "event_id": event_id,
            "uuid": uuid,
            "event_info": event_info,
            "event_tag": event_tag,
        }
        result_list.append(result)
    return result_list


def generate_entity_details_relations(events: dict) -> list:
    """
    Takes a dictionary and returns a list for building an entity
    """
    result_list = []
    if events:
        event_id = events["Event"]["id"]
        uuid = events["Event"]["uuid"]
        event_info = events["Event"]["info"]

        result = {"event_id": event_id, "uuid": uuid, "event_info": event_info}
        result_list.append(result)

    return result_list
