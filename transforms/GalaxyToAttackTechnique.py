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
from maltego_trx.transform import DiscoverableTransform

from utils.galaxy_helper import galaxy_to_transform


@registry.register_transform(
    display_name="To Attack Technique",
    input_entity="maltego.misp.MISPGalaxy",
    description="Expands a Galaxy to Attack Technique",
    output_entities=["maltego.AttackTechnique"],
)
class GalaxyToAttackTechnique(DiscoverableTransform):
    """This transform searches MISP Instance
    for a given galaxy and returns Attack Techniques"""

    @classmethod
    def create_entities(cls, request: MaltegoMsg, response: MaltegoTransform):
        # Get the value from the request
        input_val = request.Value
        # limit = request.Slider
        uuid = request.getProperty("uuid")
        tag = request.getProperty("tag")
        name = request.getProperty("name")

        value_dict = {
            "input_val": input_val,
            "uuid": uuid,
            "tag_name": tag,
            "name": name,
        }

        return galaxy_to_transform(value_dict, response, type_filter="AttackTechnique")
