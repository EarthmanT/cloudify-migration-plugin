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

from cloudify_migration.constants import NT
from cloudify_migration.node_template import SimplifiedNode


class MigrationBlueprint(object):

    def __init__(self, blueprint_yaml, node_templates=None):
        self.yaml = blueprint_yaml
        self._node_templates = \
            node_templates if isinstance(node_templates, list) else []

    @property
    def node_templates(self):
        node_names = [n.id for n in self._node_templates]
        for node_name in self.yaml[NT].keys():
            if node_name not in node_names:
                self._node_templates.append(
                    SimplifiedNode(
                        node_name=node_name,
                        node_definition=self.yaml[NT][node_name]))
        return self._node_templates

    def remove_node(self, node_id):
        nodes = self.node_templates
        for node in nodes:
            if node.id == node_id:
                index = self.node_templates.index(node)
                del self.node_templates[index]
