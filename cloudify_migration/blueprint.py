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


class BaseBlueprintDict(object):

    def __init__(self, key, definition):
        self.key = key
        self.definition = definition


class BlueprintImport(object):

    def __init__(self, key):
        self.key = key


class BlueprintInput(BaseBlueprintDict):

    @property
    def type(self):
        return self.definition.get('type')

    @property
    def description(self):
        return self.definition.get('description')

    @property
    def default(self):
        return self.definition.get('default')

    @property
    def required(self):
        return self.definition.get('required')


class NodeType(BaseBlueprintDict):

    @property
    def id(self):
        return self.key

    @property
    def derived_from(self):
        return self.definition.get('derived_from')

    @property
    def properties(self):
        return self.definition.get('properties')

    @property
    def interfaces(self):
        return self.definition.get('interfaces')


class NodeTemplate(BaseBlueprintDict):

    @property
    def id(self):
        return self.key

    @property
    def type(self):
        return self.definition.get('type')

    @property
    def properties(self):
        return self.definition.get('properties')

    @property
    def interfaces(self):
        return self.definition.get('interfaces')

    @property
    def relationships(self):
        return self.definition.get('relationships')

    def update_properties(self, property_name, property_value):
        self.definition['properties'] = {property_name: property_value}

    @property
    def __dict__(self):
        data = {
            self.id: {
                'type': self.type,
                'properties': self.properties,
                'interfaces': self.interfaces,
                'relationships': self.relationships,
            }
        }
        return data


class BlueprintOutput(BaseBlueprintDict):

    @property
    def description(self):
        return self.definition.get('description')

    @property
    def value(self):
        return self.definition.get('value')


class MigrationBlueprint(object):

    def __init__(self,
                 blueprint_yaml,
                 imports=None,
                 inputs=None,
                 node_templates=None,
                 node_types=None,
                 outputs=None):
        """Convert a Blueprint YAML file into some object.

        :param blueprint_yaml:
        :param imports:
        :param inputs:
        :param node_templates:
        :param node_types:
        :param outputs:
        :return: None
        """

        self.yaml = blueprint_yaml
        self._imports = imports if isinstance(imports, list) else []
        self._inputs = inputs if isinstance(inputs, dict) else {}
        self._node_templates = node_templates if isinstance(
            node_templates, dict) else {}
        self._node_types = node_types if isinstance(node_types, dict) else {}
        self._outputs = outputs if isinstance(outputs, dict) else {}

    @property
    def imports(self):
        for import_key in self.yaml['imports']:
            self._imports.append(
                BlueprintImport(import_key)
            )
        return self._imports

    @property
    def inputs(self):
        for input_key in self.yaml['inputs'].keys():
            self._inputs.update(
                BlueprintInput(input_key, self.yaml.get(input_key)))
        return self._inputs

    @property
    def node_types(self):
        for node_type_name in self.yaml['node_types'].keys():
            if node_type_name not in self._node_types.keys():
                self._node_types.update({
                    node_type_name: NodeType(
                        node_type_name,
                        self.yaml['node_types'][node_type_name]
                    )
                })
        return self._node_types

    @property
    def node_templates(self):
        for node_name in self.yaml['node_templates'].keys():
            if node_name not in self._node_templates.keys():
                self._node_templates.update({
                    node_name: NodeTemplate(
                        node_name,
                        self.yaml['node_templates'][node_name])
                })
        return self._node_templates

    @property
    def outputs(self):
        for output_key in self.yaml['outputs'].keys():
            self._outputs.update(
                BlueprintOutput(output_key, self.yaml.get(output_key)))
        return self._outputs
