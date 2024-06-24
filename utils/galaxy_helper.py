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
import os
import tempfile
import time
import json
from typing import Optional

from maltego_trx.maltego import MaltegoTransform

from utils.mappings import mapping_galaxy_icon, mapping_galaxy_type

local_path_root = os.path.join(tempfile.gettempdir(), "MISP-maltego")
if not os.path.exists(local_path_root):
    os.mkdir(local_path_root)


def galaxycluster_to_cluster(cluster: dict) -> dict:
    """
    Takes in a dictionary loops through the items,
    checks with the mapping and returns another dictionary
    """
    if "meta" in cluster and "uuid" in cluster["meta"]:
        cluster["uuid"] = cluster["meta"]["uuid"].pop(0)

    if "meta" in cluster and "synonyms" in cluster["meta"]:
        cluster["synonyms"] = ", ".join(cluster["meta"]["synonyms"])
    else:
        cluster["synonyms"] = ""

    galaxy_cluster = get_galaxy_cluster(uuid=cluster["uuid"])
    # map the 'icon' name from the cluster to the icon filename of the intelligence-icons repository
    try:
        cluster["icon_url"] = mapping_galaxy_icon[galaxy_cluster["icon"]]
    except KeyError:
        # it's not in our mapping, just ignore and leave the default icon
        cluster["icon_url"] = None

    # create the right sub-galaxy: ThreatActor, Software, AttackTechnique, ... or MISPGalaxy
    try:
        galaxy_type = mapping_galaxy_type[galaxy_cluster["type"]]
        cluster["galaxy_type"] = galaxy_type
    except KeyError:
        cluster["galaxy_type"] = "MISPGalaxy"

    return cluster


# LATER this uses the galaxies from github as the MISP web UI does not fully support the Galaxies in the webui.
# See https://github.com/MISP/MISP/issues/3801
# galaxy_archive_url should be updated to github URL when it's published.
galaxy_archive_url = ""
local_path_uuid_mapping = os.path.join(
    local_path_root, "MISP_maltego_galaxy_mapping.json"
)
local_path_clusters = os.path.join(local_path_root, "misp-galaxy-main", "clusters")
galaxy_cluster_uuids = None


def galaxy_update_local_copy(force=False):
    """
    As Galaxy cluster info is usually large, the better option is to download it
    save it locally in a zip file, and use it later, this can be updated when needed.
    """
    import io
    import json
    import os
    import requests
    from zipfile import ZipFile

    # some aging and automatic re-downloading
    if not os.path.exists(local_path_uuid_mapping):
        force = True
    else:
        # force update if cache is older than 24 hours
        if time.time() - os.path.getmtime(local_path_uuid_mapping) > 60 * 60 * 24:
            force = True

    if force:
        # create a lock to prevent two processes doing the same, and writing to the file at the same time
        lockfile = local_path_uuid_mapping + ".lock"
        from pathlib import Path

        while os.path.exists(lockfile):
            time.sleep(0.3)
        Path(local_path_uuid_mapping + ".lock").touch()
        # download the latest zip of the public galaxy
        try:
            resp = requests.get(galaxy_archive_url)
            zf = ZipFile(io.BytesIO(resp.content))
            zf.extractall(local_path_root)
            zf.close()
        except Exception:
            # remove the lock
            os.remove(lockfile)
            # raise(response.addUIMessage(message="ERROR: Could not download Galaxy data from htts://github.com/MISP/MISP-galaxy/. Please check internet connectivity.", messageType='Inform'))

        # generate the uuid mapping and save it to a file
        galaxies_fnames = []
        for f in os.listdir(local_path_clusters):
            if ".json" in f:
                galaxies_fnames.append(f)
        galaxies_fnames.sort()

        cluster_uuids = {}
        for galaxy_fname in galaxies_fnames:
            try:
                fullPathClusters = os.path.join(local_path_clusters, galaxy_fname)
                with open(fullPathClusters) as fp:
                    galaxy = json.load(fp)
                with open(fullPathClusters.replace("clusters", "galaxies")) as fg:
                    galaxy_main = json.load(fg)
                for cluster in galaxy["values"]:
                    if "uuid" not in cluster:
                        continue
                    # skip deprecated galaxies/clusters
                    if galaxy_main["namespace"] == "deprecated":
                        continue
                    # keep track of the cluster, but also enhance it to look like the cluster we receive when accessing the web.
                    cluster_uuids[cluster["uuid"]] = cluster
                    cluster_uuids[cluster["uuid"]]["type"] = galaxy["type"]
                    cluster_uuids[cluster["uuid"]][
                        "tag_name"
                    ] = 'misp-galaxy:{}="{}"'.format(galaxy["type"], cluster["value"])
                    if "icon" in galaxy_main:
                        cluster_uuids[cluster["uuid"]]["icon"] = galaxy_main["icon"]
            except Exception:
                # we ignore incorrect galaxies
                pass

        with open(local_path_uuid_mapping, "w") as f:
            json.dump(cluster_uuids, f)
        # remove the lock
        os.remove(lockfile)


def search_galaxy_cluster(keyword: str) -> any:
    """
    Takes a string, and yields a generator item of dict
    """
    keyword = keyword.lower()
    global galaxy_cluster_uuids
    if not galaxy_cluster_uuids:
        galaxy_cluster_uuids = galaxy_load_cluster_mapping()

    # % only at start
    if keyword.startswith("%") and not keyword.endswith("%"):
        keyword = keyword.strip("%")
        for item in galaxy_cluster_uuids.values():
            if item["value"].lower().endswith(keyword):
                yield item
            else:
                if "meta" in item and "synonyms" in item["meta"]:
                    for synonym in item["meta"]["synonyms"]:
                        if synonym.lower().endswith(keyword):
                            yield item

    # % only at end
    elif keyword.endswith("%") and not keyword.startswith("%"):
        keyword = keyword.strip("%")
        for item in galaxy_cluster_uuids.values():
            if item["value"].lower().startswith(keyword):
                yield item
            else:
                if "meta" in item and "synonyms" in item["meta"]:
                    for synonym in item["meta"]["synonyms"]:
                        if synonym.lower().startswith(keyword):
                            yield item

    # search substring assuming % at start and end
    else:
        keyword = keyword.strip("%")
        for item in galaxy_cluster_uuids.values():
            if keyword in item["value"].lower():
                yield item
            else:
                if "meta" in item and "synonyms" in item["meta"]:
                    for synonym in item["meta"]["synonyms"]:
                        if keyword in synonym.lower():
                            yield item


def galaxy_load_cluster_mapping():
    """
    Updates the local copy of galaxies json file
    """
    galaxy_update_local_copy()
    with open(local_path_uuid_mapping, "r") as f:
        cluster_uuids = json.load(f)
    return cluster_uuids


def get_galaxy_cluster(
    uuid: str = None, tag: str = None, request_entity: dict = None
) -> dict:
    """
    A way to get galaxy clusters with different input value types.
    """
    global galaxy_cluster_uuids
    if not galaxy_cluster_uuids:
        galaxy_cluster_uuids = galaxy_load_cluster_mapping()
    if uuid:
        return galaxy_cluster_uuids.get(uuid)
    if tag:
        for item in galaxy_cluster_uuids.values():
            if item["tag_name"] == tag:
                return item
    if request_entity:
        if request_entity["uuid"]:
            return get_galaxy_cluster(uuid=request_entity["uuid"])
        if request_entity["tag_name"]:
            return get_galaxy_cluster(tag=request_entity["tag_name"])
        if request_entity["name"]:
            return get_galaxy_cluster(tag=request_entity["name"])


def galaxy_to_transform(
    input_val: dict, response: MaltegoTransform, type_filter: str = "MISPGalaxy"
) -> Optional[MaltegoTransform]:
    """
    Takes the input value, and the entity type
    calls other helper functions to query based on the galaxy,
    and returns galaxy related info back.
    Main Galaxy To <ANY> Transform helper.
    """
    current_cluster = get_galaxy_cluster(request_entity=input_val)

    # legacy - replaced by Search in MISP
    if not current_cluster and input_val["name"] != "-":
        potential_clusters = search_galaxy_cluster(input_val["name"])
        if potential_clusters:
            for potential_cluster in potential_clusters:
                galaxycluster_to_entity(potential_cluster, response)
    # end of legacy

    if not current_cluster:
        return response.addUIMessage(
            message="Galaxy Cluster UUID not in local mapping. Please update local cache; "
            "non-public UUIDs are not supported yet.",
            messageType="Inform",
        )

    c = current_cluster
    icon_url = mapping_galaxy_icon.get(c.get("icon"), None)

    # update existing object
    galaxy_cluster = get_galaxy_cluster(uuid=c["uuid"])
    icon_url = None
    if "icon" in galaxy_cluster:
        try:
            icon_url = mapping_galaxy_icon[galaxy_cluster["icon"]]
        except Exception:
            pass

    if c["meta"].get("synonyms"):
        synonyms = ", ".join(c["meta"]["synonyms"])
    else:
        synonyms = ""
    # entity_value = '{}\n{}'.format(c['type'], c['value'])
    entity = response.addEntity(
        f"maltego.{type_filter}", f"{c['type']}, \n, {c['value']}"
    )
    entity.addProperty(fieldName="uuid", displayName="uuid", value=c["uuid"])
    entity.addProperty(
        fieldName="description", displayName="description", value=c.get("description")
    )
    entity.addProperty(
        fieldName="cluster_type", displayName="cluster_type", value=c.get("type")
    )
    entity.addProperty(
        fieldName="cluster_value", displayName="cluster_value", value=c.get("value")
    )
    entity.addProperty(fieldName="synonyms", displayName="synonyms", value=synonyms)
    entity.addProperty(
        fieldName="tag_name", displayName="tag_name", value=c["tag_name"]
    )
    entity.setIconURL(url=icon_url)

    # find related objects
    if "related" in current_cluster:
        for related in current_cluster["related"]:
            related_cluster = get_galaxy_cluster(uuid=related["dest-uuid"])
            if related_cluster:
                galaxycluster_to_entity(related_cluster, response)

    # find objects that are relating to this one
    for related in get_galaxies_relating(current_cluster["uuid"]):
        for rel_in_rel in related["related"]:
            if rel_in_rel["dest-uuid"] == current_cluster["uuid"]:
                break
        galaxycluster_to_entity(related, response)
    return None


def get_galaxies_relating(uuid: str) -> any:
    """
    Searches the galaxy clusters file for a given uuid
    returns a string
    """
    global galaxy_cluster_uuids
    if not galaxy_cluster_uuids:
        galaxy_cluster_uuids = galaxy_load_cluster_mapping()

    for item in galaxy_cluster_uuids.values():
        if "related" in item:
            for related in item["related"]:
                if related["dest-uuid"] == uuid:
                    yield item


def galaxycluster_to_entity(
    potential_cluster: dict, response: MaltegoTransform
) -> MaltegoTransform:
    """
    Takes a dictionary, creates and returns an entity
    """
    cluster = galaxycluster_to_cluster(potential_cluster)
    if cluster:
        display_value = cluster["type"] + "\n" + cluster["value"]
        entity_name = cluster["galaxy_type"]
        entity = response.addEntity(f"maltego.{entity_name}", display_value)
        entity.addProperty(fieldName="uuid", displayName="uuid", value=cluster["uuid"])
        # entity.addProperty(fieldName='description', displayName='description', value=cluster['description'])
        entity.addProperty(
            fieldName="cluster_type", displayName="cluster_type", value=cluster["type"]
        )
        entity.addProperty(
            fieldName="cluster_value",
            displayName="cluster_value",
            value=cluster["value"],
        )
        entity.addProperty(
            fieldName="synonyms", displayName="synonyms", value=cluster["synonyms"]
        )
        entity.addProperty(
            fieldName="tag_name", displayName="tag_name", value=cluster["tag_name"]
        )
        entity.addProperty(
            fieldName="icon_url", displayName="icon_url", value=cluster["icon_url"]
        )
