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

# Code blocks used with permission from here: https://github.com/MISP/MISP-maltego/blob/master/src/MISP_maltego/transforms/common/util.py
# Courtesy Christophe Vandeplas
from utils.misp_data import (
    MISPQuery,
    tag_matches_note_prefix,
    attribute_to_entity_details,
    event_to_entity,
    object_to_entity,
    galaxycluster_to_entity,
)
from utils.misp_query import (
    generate_entity_details_relations,
)

from maltego_trx.maltego import MaltegoTransform
from maltego_trx.entities import Hashtag

from typing import Optional


def gen_response_tags(
    input_val: str,
    limit: int,
    response: MaltegoTransform,
    api_url: str,
    api_key: str,
    gen_response=True,
) -> MaltegoTransform:
    """
    Takes an input value, searches for the events, and sends back tags
    """
    misp_query = MISPQuery(api_url=api_url, api_key=api_key)

    if input_val:
        event_json = misp_query.event_to_transform_details(
            input_val=input_val, limit=limit
        )
        if event_json:
            event_tags = []
            if "Tag" in event_json[0]["Event"]:
                for t in event_json[0]["Event"]["Tag"]:
                    event_tags.append(t["name"])
                    if t["name"].startswith("misp-galaxy"):
                        continue
                    if tag_matches_note_prefix(t["name"]):
                        continue
                    if gen_response:
                        response.addEntity(Hashtag, t["name"])
            return event_tags


def gen_response_galaxies(
    input_val: str, limit: int, response: MaltegoTransform, api_url: str, api_key: str
) -> Optional[MaltegoTransform]:
    """
    Takes an input value, searches for the galaxy clusters, and sends back galaxies
    """
    misp_query = MISPQuery(api_url=api_url, api_key=api_key)
    if input_val:
        event_json = misp_query.event_to_transform_details(
            input_val=input_val, limit=limit
        )
    for g in event_json[0]["Event"]["Galaxy"]:
        for c in g["GalaxyCluster"]:
            galaxycluster_to_entity(c, response=response)
    return None


def gen_response_attributes(
    input_val: str, limit: int, response: MaltegoTransform, api_url: str, api_key: str
) -> Optional[MaltegoTransform]:
    """
    Takes an input value, searches for the events, and sends back attributes
    """
    misp_query = MISPQuery(api_url=api_url, api_key=api_key)
    if input_val:
        event_tags = gen_response_tags(
            input_val=input_val,
            limit=limit,
            response=response,
            gen_response=False,
            api_url=api_url,
            api_key=api_key,
        )
        event_json = misp_query.event_to_transform_details(
            input_val=input_val, limit=limit
        )
        if event_json:
            for a in event_json[0]["Event"]["Attribute"]:
                attribute_to_entity_details(
                    a=a, response=response, event_tags=event_tags
                )
    return None


def gen_response_objects(
    input_val: str, limit: int, response: MaltegoTransform, api_url: str, api_key: str
) -> Optional[MaltegoTransform]:
    """
    Takes an input value, searches for the events, and sends back objects
    """
    misp_query = MISPQuery(api_url=api_url, api_key=api_key)
    if input_val:
        event_json = misp_query.event_to_transform_details(
            input_val=input_val, limit=limit
        )
        for o in event_json[0]["Event"]["Object"]:
            object_to_entity(
                input_val=o, response=response, api_url=api_url, api_key=api_key
            )

    return None


def gen_response_relations(
    input_val: str, limit: int, response: MaltegoTransform, api_url: str, api_key: str
) -> Optional[MaltegoTransform]:
    """
    Takes an input value, searches for the events, and sends back attributes
    """
    misp_query = MISPQuery(api_url=api_url, api_key=api_key)
    event_json = misp_query.event_to_transform_details(input_val=input_val, limit=limit)
    for e in event_json[0]["Event"]["RelatedEvent"]:
        results = generate_entity_details_relations(e)
        if results:
            for row in results:
                event_to_entity(result=row, response=response)
    return None
