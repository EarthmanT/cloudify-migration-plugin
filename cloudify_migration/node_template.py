########
# Copyright (c) 2018 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.


from cloudify import ctx

from cloudify_migration import constants
from cloudify_migration.exceptions import MigrationException


class SimplifiedNode(object):

    def __init__(self,
                 cloudify_context=None,
                 node_name=None,
                 node_definition=None):

        self._ctx = cloudify_context or ctx
        self.id = node_name
        self.node_id = self.id
        self.node_name = self.id
        self.node_definition = node_definition

    @property
    def properties(self):
        return self.node_definition.get(constants.PROPERTIES, {})

    @property
    def type(self):
        if constants.TYPE not in self.node_definition:
            raise MigrationException(
                'Improperly formed node definition: {0}'.format(
                    self.node_definition))
        return self.node_definition.get(constants.TYPE)

    @property
    def __dict__(self):
        data = {
            self.id: {
                'type': self.type,
                'properties': self.properties
            }
        }
        return data

    def update_properties(self, property_name, property):
        self.node_definition[constants.PROPERTIES] = {property_name: property}
