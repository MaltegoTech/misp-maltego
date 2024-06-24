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
from typing import Union, Optional

from maltego_trx.maltego import MaltegoTransform
from maltego_trx.entities import Hashtag, URL, Person, Phrase

from utils.misp_query import MISPQuery
from utils.galaxy_helper import (
    search_galaxy_cluster,
    galaxycluster_to_cluster,
    galaxycluster_to_entity,
)
from utils.mappings import mapping_misp_to_maltego, mapping_object_icon

# TODO Maybe provide the user with a popup box to enter their own tag prefixes?
tag_note_prefixes = ["tlp:", "PAP:", "de-vs:", "euci:", "fr-classif:", "nato:", "gdpr:"]


def misp_events_idinfo(
    input_val: str, response: MaltegoTransform, limit: int, api_url: str, api_key: str
) -> MaltegoTransform:
    """
    Main helper function for the MISP id and events to entity transforms
    """
    try:
        if input_val == "0":
            return response
        # when the event ID is the input
        if int(input_val):
            parse_output(
                input_val=input_val,
                limit=limit,
                etype="eid",
                response=response,
                api_url=api_url,
                api_key=api_key,
            )
            return response
    except ValueError:
        pass
    # when the input is a string check for event info
    if isinstance(input_val, str):
        parse_output(
            input_val=input_val,
            limit=limit,
            etype="einfo",
            response=response,
            api_url=api_url,
            api_key=api_key,
        )
        return response


def parse_output(
    input_val: Union[str, int],
    etype: str,
    response: MaltegoTransform,
    limit: int,
    api_url: str,
    api_key: str,
) -> MaltegoTransform:
    """
    Helper function to invoke the correct MISP query function
    """
    misp_query = MISPQuery(api_url, api_key)
    if "eid" in etype:
        result = misp_query.misp_query_idinfo(
            event_type="id", event_val=int(input_val), limit=limit
        )
    elif "einfo" in etype:
        result = misp_query.misp_query_idinfo(
            event_type="info", event_val=str(input_val), limit=limit
        )
    elif "galaxy" in etype:
        result = misp_query.misp_query_attr(
            event_type="galaxy", event_val=input_val, limit=limit
        )
    elif "hash_or_temp" in etype:
        result = misp_query.misp_query_attr(
            event_type="hash_or_temp", event_val=input_val, limit=limit
        )

    if result:
        for row in result:
            event_to_entity(result=row, response=response)


def event_to_entity(result: dict, response: MaltegoTransform) -> MaltegoTransform:
    """
    Helper function that takes a dictionary and builds a Maltego Entity
    """
    if result:
        notes = []
        if "event_tag" in result.keys():
            for row in result["event_tag"]:
                notes.append(tag_to_notes(row))
        notes = list(filter(lambda x: x is not None and x != "", notes))
        entity = response.addEntity("maltego.misp.MISPEvent", result["event_id"])
        entity.addProperty(fieldName="uuid", displayName="uuid", value=result["uuid"])
        entity.addProperty(
            fieldName="event_info", displayName="event_info", value=result["event_info"]
        )
        entity.setNote(notes)
        entity.setBookmark(1)


def convert_tags_to_note(tags: list) -> str:
    """
    Helper function that takes in a string, matches with the predefined set of tags
    and returns a list
    """
    if not tags:
        return None
    notes = []
    for tag in tags:
        for tag_note_prefix in tag_note_prefixes:
            if tag.startswith(tag_note_prefix):
                notes.append(tag)

    return "\n".join(notes)


def tag_to_notes(tags: dict) -> str:
    """
    Helper function that takes a dictionary checks for tags both in main and nested
    returns all tags
    """
    # alltags = [tag.get('name') or tag.get('Tag', {}).get('name') for tag in tags]
    name_from_direct = tags.get("name")
    name_from_nested = tags.get("Tag", {}).get("name")

    if name_from_direct or name_from_nested:
        return convert_tags_to_note([name_from_direct or name_from_nested])
    return convert_tags_to_note([])


def tag_matches_note_prefix(tag: str) -> bool:
    """
    Helper function to check for tags
    """
    for tag_note_prefix in tag_note_prefixes:
        if tag.startswith(tag_note_prefix):
            return True
    return False


def misp_events_galaxy(
    entity_type: str,
    input_val: str,
    response: MaltegoTransform,
    limit: int,
    api_url: str,
    api_key: str,
) -> MaltegoTransform:
    """
    Main helper function to search for galaxies based on events
    """
    misp_query = MISPQuery(api_url=api_url, api_key=api_key)
    potential_clusters = search_galaxy_cluster(input_val)
    if "MISPGalaxy" in entity_type:
        if potential_clusters:
            for potential_cluster in potential_clusters:
                galaxycluster_to_entity(potential_cluster, response=response)
    else:
        result = misp_query.from_hashtag(input_val)
        if result:
            entity = response.addEntity(Hashtag, result)
            entity.setBookmark(1)

    attr_json = misp_query.to_attribute(input_val, limit=limit)
    for a in attr_json["Attribute"]:
        attribute_to_entity_details(a, response=response, only_self=True)


def attribute_to_entity_details(
    a: dict, response: MaltegoTransform, event_tags: list = [], only_self=False
) -> MaltegoTransform:
    # TODO Remove the empty list default declaration
    """
    if event_tags:
        return event_tags
    else:
        return []
    """
    """
    Takes a dictionary, and a list, returns Maltego Entities from MISP Attributes
    """
    # prepare some attributes to a better form
    a["data"] = None  # empty the file content as we really don't need this here
    for k, v in a.items():
        if a["type"] == "malware-sample":
            a["type"] = "filename|md5"
        if (
            a["type"] == "regkey|value"
        ):  # LATER regkey|value => needs to be a special non-combined object
            a["type"] = "regkey"

        combined_tags = event_tags
        if "Galaxy" in a and not only_self:
            for g in a["Galaxy"]:
                for c in g["GalaxyCluster"]:
                    cluster = galaxycluster_to_cluster(c)
                    galaxycluster_to_entity(cluster, response)

        # complement the event tags with the attribute tags.
        if "Tag" in a and not only_self:
            for t in a["Tag"]:
                combined_tags.append(t["name"])
                # ignore all misp-galaxies
                if t["name"].startswith("misp-galaxy"):
                    continue
                # ignore all those we add as notes
                if tag_matches_note_prefix(t["name"]):
                    continue
                else:
                    response.addEntity(Hashtag, t["name"]).setBookmark(1)

        notes = convert_tags_to_note(combined_tags)

        # TODO Reduce redundancies further by way of another function(s) that could generate the dictionaries
        # Or maybe adding the a['type'] to the mapping and call the same function depending on the type,
        # along with using if or conditions for key value pairs
        """
        Example in mind
        if a["type"] in entity_type_map/mapping
        entity_type = entity_type_map[a["type"]]
        display_value = a.get("comment") or "Label"
        value = format_entity_value(a["type"], a["value"])
        response.addEntity(entity_type, value)
        """
        # special cases
        if a["type"] in ("url", "uri"):
            value_dict = {
                "entity_type": URL,
                "entity_value": a["value"],
                "display_value": a["value"],
                "display_title": a["value"],
                "entity_note": notes,
                "bookmark": 1,
            }
            attribute_to_entity(value_dict, response)

        # attribute is from an object, and a relation gives better understanding of the type of attribute
        if a.get("object_relation") and mapping_misp_to_maltego.get(
            a["object_relation"]
        ):
            entity_obj = mapping_misp_to_maltego[a["object_relation"]][0]
            value_dict = {
                "entity_type": entity_obj,
                "entity_value": a["value"],
                "display_value": a.get("comment"),
                "display_title": "Label",
                "entity_note": notes,
                "bookmark": 1,
            }
            attribute_to_entity(value_dict, response)

        # combined attributes
        elif "|" in a["type"]:
            t_1, t_2 = a["type"].split("|")
            v_1, v_2 = a["value"].split("|")

            for t, v, display in [(t_1, v_1, "hash"), (t_2, v_2, "filename")]:
                if t in mapping_misp_to_maltego:
                    entity_obj = mapping_misp_to_maltego[t][0]
                    value_dict = {
                        "entity_type": entity_obj,
                        "entity_value": [v, t],
                        "display_value": display,
                        "display_title": v,
                        "entity_note": notes,
                        "bookmark": 1,
                    }
                    attribute_to_entity(value_dict, response)

        # normal attributes
        elif a["type"] in mapping_misp_to_maltego:
            entity_obj = mapping_misp_to_maltego[a["type"]][0]
            value_dict = {
                "entity_type": entity_obj,
                "entity_value": a["value"],
                "entity_value_type": a["type"],
                "display_value": a.get("comment"),
                "display_title": "Comment",
                "entity_note": notes,
                "bookmark": 1,
            }
            attribute_to_entity(value_dict, response)

        else:
            value_dict = {
                "entity_type": Phrase,
                "entity_value": a["value"],
                "entity_value_type": a["type"],
                "display_value": a.get("comment"),
                "display_title": "Comment",
                "entity_note": notes,
                "bookmark": 1,
            }
            attribute_to_entity(value_dict, response)

    # return None


def attribute_to_entity(
    entity_result: dict, response: MaltegoTransform
) -> Optional[MaltegoTransform]:
    """
    Takes a dictionary and returns entities
    """
    if entity_result:
        entity = response.addEntity(
            entity_result["entity_type"], entity_result["entity_value"]
        )
        entity.addDisplayInformation(
            entity_result["display_value"], entity_result["display_title"]
        )
        entity.setNote(note=entity_result["entity_note"])
        entity.setBookmark(entity_result["bookmark"])
        entity.addProperty(
            fieldName="type",
            displayName="Entity Value Type",
            value=entity_result["entity_value_type"],
        )


def get_attribute_in_event(
    e: dict, attribute_value: str, substring=False
) -> str | None:
    """
    Returns Attributes founds in MISP Events
    """
    for a in e["Event"]["Attribute"]:
        if a["value"] == attribute_value:
            return a
        if "|" in a["type"] or a["type"] == "malware-sample":
            if attribute_value in a["value"].split("|"):
                return a
        if substring:
            keyword = attribute_value.strip("%")
            if attribute_value.startswith("%") and attribute_value.endswith("%"):
                if attribute_value in a["value"]:
                    return a
                if "|" in a["type"] or a["type"] == "malware-sample":
                    val1, val2 = a["value"].split("|")
                    if attribute_value in val1 or attribute_value in val2:
                        return a
            elif attribute_value.startswith("%"):
                if a["value"].endswith(keyword):
                    return a
                if "|" in a["type"] or a["type"] == "malware-sample":
                    val1, val2 = a["value"].split("|")
                    if val1.endswith(keyword) or val2.endswith(keyword):
                        return a

            elif attribute_value.endswith("%"):
                if a["value"].startswith(keyword):
                    return a
                if "|" in a["type"] or a["type"] == "malware-sample":
                    val1, val2 = a["value"].split("|")
                    if val1.startswith(keyword) or val2.startswith(keyword):
                        return a

    return None


def get_attribute_in_object(
    o: dict, attribute_type=False, attribute_value=False, drop=False, substring=False
) -> dict:
    """Gets the first attribute of a specific type within an object"""
    found_attribute = {"value": ""}
    for i, a in enumerate(o["Attribute"]):
        if a["type"] == attribute_type:
            found_attribute = a.copy()
            if drop:  # drop the attribute from the object
                o["Attribute"].pop(i)
            break
        if a["value"] == attribute_value:
            found_attribute = a.copy()
            if drop:  # drop the attribute from the object
                o["Attribute"].pop(i)
            break
        if "|" in a["type"] or a["type"] == "malware-sample":
            if attribute_value in a["value"].split("|"):
                found_attribute = a.copy()
                if drop:  # drop the attribute from the object
                    o["Attribute"].pop(i)
                break
        # substring matching
        if substring:
            keyword = attribute_value.strip("%")
            if attribute_value.startswith("%") and attribute_value.endswith("%"):
                if attribute_value in a["value"]:
                    found_attribute = a.copy()
                    if drop:  # drop the attribute from the object
                        o["Attribute"].pop(i)
                    break
                if "|" in a["type"] or a["type"] == "malware-sample":
                    val1, val2 = a["value"].split("|")
                    if attribute_value in val1 or attribute_value in val2:
                        found_attribute = a.copy()
                        if drop:  # drop the attribute from the object
                            o["Attribute"].pop(i)
                        break
            elif attribute_value.startswith("%"):
                if a["value"].endswith(keyword):
                    found_attribute = a.copy()
                    if drop:  # drop the attribute from the object
                        o["Attribute"].pop(i)
                    break
                if "|" in a["type"] or a["type"] == "malware-sample":
                    val1, val2 = a["value"].split("|")
                    if val1.endswith(keyword) or val2.endswith(keyword):
                        found_attribute = a.copy()
                        if drop:  # drop the attribute from the object
                            o["Attribute"].pop(i)
                        break

            elif attribute_value.endswith("%"):
                if a["value"].startswith(keyword):
                    return a
                if "|" in a["type"] or a["type"] == "malware-sample":
                    val1, val2 = a["value"].split("|")
                    if val1.startswith(keyword) or val2.startswith(keyword):
                        found_attribute = a.copy()
                        if drop:  # drop the attribute from the object
                            o["Attribute"].pop(i)
                        break
    return found_attribute


def get_object_in_event(uuid: str, e: dict) -> dict:
    """
    Gets the full object in the event
    """
    for o in e["Event"]["Object"]:
        if o["uuid"] == uuid:
            return o


def object_to_entity_result(o: dict, api_url: str, api_key: str) -> dict:
    """
    Takes an Object and returns a dictionary of result
    """
    # find a nice icon for it
    try:
        icon_url = mapping_object_icon[o["name"]]
    except KeyError:
        # it's not in our mapping, just ignore and leave the default icon
        icon_url = None
    # Generate a human readable display-name:
    # - find the first RequiredOneOf that exists
    # - if none, use the first RequiredField
    # LATER further finetune the human readable version of this object

    misp_query = MISPQuery(api_url=api_url, api_key=api_key)
    o_template = misp_query.get_object_template(o["template_uuid"])
    human_readable = None
    try:
        found = False
        while not found:  # the while loop is broken once something is found, or the requiredOneOf has no elements left
            required_ote_type = o_template["ObjectTemplate"]["requirements"][
                "requiredOneOf"
            ].pop(0)
            for ote in o_template["ObjectTemplateElement"]:
                if ote["object_relation"] == required_ote_type:
                    required_a_type = ote["type"]
                    break
            for a in o["Attribute"]:
                if a["type"] == required_a_type:
                    # human_readable = '{}:\n{}'.format(o['name'], a['value'])
                    human_readable = f"{o['name']}, \n, {a['value']}"
                    found = True
                    break
    except Exception:
        pass
    if not human_readable:
        try:
            found = False
            parts = []
            for required_ote_type in o_template["ObjectTemplate"]["requirements"][
                "required"
            ]:
                for ote in o_template["ObjectTemplateElement"]:
                    if ote["object_relation"] == required_ote_type:
                        required_a_type = ote["type"]
                        break
                for a in o["Attribute"]:
                    if a["type"] == required_a_type:
                        parts.append(a["value"])
                        break
            # human_readable = '{}:\n{}'.format(o['name'], '|'.join(parts))
            human_readable = f'{o["name"]}:\n{"|".join(parts)}'
        except Exception:
            human_readable = o["name"]

    if o["uuid"]:
        uuid = o["uuid"]
        event_id = int(o["event_id"])
        meta_category = o.get("meta_category")
        description = o.get("description")
        comment = o.get("comment")
        icon_url = icon_url
        bookmark = 1

        result = {
            "hr": human_readable,
            "uuid": uuid,
            "event_id": event_id,
            "meta_category": meta_category,
            "description": description,
            "comment": comment,
            "icon_url": icon_url,
            "bookmark": bookmark,
        }

        return result


def object_to_entity(
    input_val: dict, api_url: str, api_key: str, response: MaltegoTransform
) -> MaltegoTransform:
    """
    Takes a MISP Object and returns Maltego Entity
    """
    if input_val:
        result = object_to_entity_result(o=input_val, api_url=api_url, api_key=api_key)
        if result:
            entity = response.addEntity("maltego.misp.MISPObject", result["hr"])
            entity.addProperty(
                fieldName="uuid", displayName="uuid", value=result["uuid"]
            )
            entity.addProperty(
                fieldName="event_id", displayName="event_id", value=result["event_id"]
            )
            entity.addProperty(
                fieldName="meta_category",
                displayName="meta_category",
                value=result["meta_category"],
            )
            entity.addProperty(
                fieldName="description",
                displayName="description",
                value=result["description"],
            )
            entity.addProperty(
                fieldName="comment", displayName="comment", value=result["comment"]
            )
            entity.setIconURL(url=result["icon_url"])
            entity.setBookmark(bookmark=result["bookmark"])


def object_to_attributes(o: dict, response: MaltegoTransform) -> any:
    """
    Takes an object and returns the attributes
    """
    # first process attributes from an object that belong together
    # (eg: first-name + last-name), and remove them from the list
    if o["name"] == "person":
        first_name = get_attribute_in_object(
            o, attribute_type="first-name", drop=True
        ).get("value")
        last_name = get_attribute_in_object(
            o, attribute_type="last-name", drop=True
        ).get("value")
        full_name = {
            "first_name": first_name,
            "last_name": last_name,
            "fullname": " ".join([first_name, last_name]).strip(),
        }
        yield full_name

    # process normal attributes
    for a in o["Attribute"]:
        attribute_to_entity_details(a, response)


def object_to_relations(
    o: dict, e: dict, api_url: str, api_key: str, response: MaltegoTransform
) -> any:
    """
    Takes and object and returns related entities.
    """
    # process forward and reverse references, so just loop over all the objects of the event
    if "Object" in e["Event"]:
        for eo in e["Event"]["Object"]:
            if "ObjectReference" in eo:
                for ref in eo["ObjectReference"]:
                    # we have found original object. Expand to the related object and attributes
                    if eo["uuid"] == o["uuid"]:
                        # the reference is an Object
                        if ref.get("Object"):
                            # get the full object in the event, as our objectReference
                            # included does not contain everything we need
                            sub_object = get_object_in_event(ref["Object"]["uuid"], e)
                            yield object_to_entity(
                                input_val=sub_object,
                                response=response,
                                api_url=api_url,
                                api_key=api_key,
                            )
                        # the reference is an Attribute
                        if ref.get("Attribute"):
                            ref["Attribute"]["event_id"] = ref[
                                "event_id"
                            ]  # LATER remove this ugly workaround - object can't be requested directly from MISP
                            # using the uuid, and to find a full object we need the event_id
                            attribute_to_entity_details(ref["Attribute"], response)

                    # reverse-lookup - this is another objects relating the original object
                    if ref["referenced_uuid"] == o["uuid"]:
                        yield object_to_entity(
                            input_val=eo,
                            response=response,
                            api_url=api_url,
                            api_key=api_key,
                        )


def object_to_attributes_helper(
    event_id: int, uuid: str, response: MaltegoTransform, api_url: str, api_key: str
) -> MaltegoTransform:
    """
    Main helper function that takes a MISP Object and returns attributes.
    """

    misp_query = MISPQuery(api_url=api_url, api_key=api_key)
    event_json = misp_query.obj_to_attribute(event_id)
    for o in event_json["Event"]["Object"]:
        if o["uuid"] == uuid:
            for name in object_to_attributes(o, response):
                if name:
                    entity = response.addEntity(Person, name["fullname"])
                    entity.addProperty(
                        fieldName="firstname",
                        displayName="firstname",
                        value=name["first_name"],
                    )
                    entity.addProperty(
                        fieldName="lastname",
                        displayName="lastname",
                        value=name["last_name"],
                    )
                    entity.setBookmark(1)
            for entity in object_to_relations(
                o=o, e=event_json, response=response, api_url=api_url, api_key=api_key
            ):
                pass


def object_to_relations_helper(
    event_id: int, uuid: str, response: MaltegoTransform, api_url: str, api_key: str
) -> MaltegoTransform:
    """
    Object to Relations
    """

    misp_query = MISPQuery(api_url=api_url, api_key=api_key)
    event_json = misp_query.obj_to_attribute(event_id)
    for o in event_json["Event"]["Object"]:
        if o["uuid"] == uuid:
            object_to_relations(
                o=o, e=event_json, response=response, api_url=api_url, api_key=api_key
            )
