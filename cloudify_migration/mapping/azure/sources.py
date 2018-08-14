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

from .. import MigrationMappingMember


class AzureSourceMapping(MigrationMappingMember):

    def __init__(self, mapping_key, mapping_definition):
        mapping_key = 'node_type.{0}'.format(mapping_key)
        common_mappings = {
            'mapping_direction': 'source',
            'mappings': [
                {
                    'value': '{0}.properties.name'.format(mapping_key),
                    'elements_path': 'properties.name',
                    'elements_types': 'dict.string'
                },
                {
                    'value': '{0}.properties.use_external_resource'.format(
                        mapping_key),
                    'elements_path': 'properties.use_external_resource',
                    'elements_types': 'dict.boolean'
                }
            ]
        }
        mapping_definition.update(common_mappings)
        super(AzureSourceMapping, self).__init__(
            mapping_key, mapping_definition)


class AzureResourceGroupSource(AzureSourceMapping):

    def __init__(self):
        node_type = 'cloudify.azure.nodes.ResourceGroup'
        mapping_def = {'node_type': node_type}
        super(AzureResourceGroupSource, self).__init__(node_type, mapping_def)
