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

from cloudify_migration.constants import (
    DEFAULT,
    DERIVED,
    DESC,
    IFACES,
    IMPORTS,
    INPUTS,
    NODE_PROPS,
    NODE_TEMPS,
    NODE_TYPES,
    OUTPUTS,
    RELS,
    REQ,
    ROOT_TYPE,
    TYPE)
from cloudify_migration.utils import merge_dicts


class BaseBlueprintDict(object):

    def __init__(self, key, definition=None):
        self.key = key
        self.definition = definition or {}

    def _update_node(self, s, v):
        self.definition = merge_dicts(s, self.definition, v)

    def update_node(self, spec, variable):
        return self._update_node(spec, variable)


class BlueprintImport(object):

    def __init__(self, key):
        self.key = key


class BlueprintInput(BaseBlueprintDict):

    @property
    def type(self):
        return self.definition.get(TYPE)

    @property
    def description(self):
        return self.definition.get(DESC)

    @property
    def default(self):
        return self.definition.get(DEFAULT)

    @property
    def required(self):
        return self.definition.get(REQ)

    @property
    def __dict__(self):
        data = {}
        if self.type:
            data[TYPE] = self.type
        if self.description:
            data[DESC] = self.description
        if self.default:
            data[DEFAULT] = self.default
        if self.required:
            data[REQ] = self.required
        return {self.key: data}


class NodeTypeProperty(object):

    def __init__(self, key, default, definition=None):
        self.key = key
        self._default = self._assign_default(default)
        self.definition = definition or {}

    @staticmethod
    def _assign_default(_default):
        if isinstance(_default, dict):
            if DEFAULT in _default:
                return _default.get(DEFAULT)
        return _default

    @property
    def description(self):
        return self.definition.get(DESC)

    @property
    def type(self):
        return self.definition.get(TYPE)

    @property
    def default(self):
        return self._default

    @property
    def required(self):
        return self.definition.get(REQ)

    @property
    def __dict__(self):
        data = {}
        if self.type is not None:
            data[TYPE] = self.type
        if self.description is not None:
            data[DESC] = self.description
        if self.default is not None:
            data[DEFAULT] = self.default
        if self.required is not None:
            data[REQ] = self.required
        return data


class NodeTemplateProperty(object):

    def __init__(self, key, value):
        self.key = key
        self.value = value

    @property
    def __dict__(self):
        return {self.key: self.value}


class NodeType(BaseBlueprintDict):

    @property
    def id(self):
        return self.key

    @property
    def derived_from(self):
        return self.definition.get(DERIVED, ROOT_TYPE)

    @property
    def properties(self):
        _properties = {}
        for k, v in self.definition.get(NODE_PROPS, {}).iteritems():
            _properties[k] = NodeTypeProperty(k, v)
        return _properties

    @property
    def interfaces(self):
        return self.definition.get(IFACES)

    @property
    def __dict__(self):
        data = {}
        if self.derived_from:
            data[DERIVED] = self.derived_from
        if self.properties:
            prop_data = {}
            for k, v in self.properties.iteritems():
                prop_data[k] = v.__dict__
            data[NODE_PROPS] = prop_data
        if self.interfaces:
            data[IFACES] = self.interfaces
        return {self.key: data}

    def generate_node_template(self):
        data = {TYPE: self.key}
        if self.interfaces:
            data[IFACES] = self.interfaces
        if self.properties:
            prop_data = {}
            for k, v in self.properties.iteritems():
                property_value = v.__dict__.get(DEFAULT)
                if property_value:
                    prop_data.update({k, property_value})
            if prop_data:
                data[NODE_PROPS].update(prop_data)
        return NodeTemplate(
            '{0}_generated'.format(self.key.replace('.', '_')), data)

    def update_node(self, spec, variable):
        # TODO: Make this non-retarded.
        if NODE_PROPS in spec:
            for k, v in spec[NODE_PROPS].iteritems():
                if DEFAULT not in v:
                    spec[NODE_PROPS][k] = {DEFAULT: v}
        return self._update_node(spec, variable)


class NodeTemplate(BaseBlueprintDict):

    @property
    def id(self):
        return self.key

    @property
    def type(self):
        return self.definition.get(TYPE, ROOT_TYPE)

    @property
    def properties(self):
        _properties = {}
        for k, v in self.definition.get(NODE_PROPS, {}).iteritems():
            _properties[k] = NodeTemplateProperty(k, v)
        return _properties

    @property
    def interfaces(self):
        return self.definition.get(IFACES, {})

    @property
    def relationships(self):
        return self.definition.get(RELS, [])

    @property
    def __dict__(self):
        data = {TYPE: self.type}
        if self.properties:
            data[NODE_PROPS] = self.properties
        if self.interfaces:
            data[IFACES] = self.interfaces
        return {self.key: data}

    def update_node(self, spec, variable):
        # TODO: Make this non-retarded.
        if NODE_PROPS in spec:
            for k, v in spec[NODE_PROPS].iteritems():
                if DEFAULT in v:
                    spec[NODE_PROPS][k] = v.get(DEFAULT)
        return self._update_node(spec, variable)


class BlueprintOutput(BaseBlueprintDict):

    @property
    def description(self):
        return self.definition.get(DESC)

    @property
    def value(self):
        return self.definition.get('value')

    @property
    def __dict__(self):
        data = {}
        if self.description:
            data[DESC] = self.description
        if self.value:
            data['value'] = self.value
        return {self.key: data}


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
        for import_key in self.yaml[IMPORTS]:
            self._imports.append(
                BlueprintImport(import_key)
            )
        return self._imports

    @property
    def inputs(self):
        for input_key in self.yaml[INPUTS].keys():
            self._inputs.update(
                BlueprintInput(input_key, self.yaml.get(input_key)))
        return self._inputs

    @property
    def node_types(self):
        for node_type_name in self.yaml[NODE_TYPES].keys():
            if node_type_name not in self._node_types.keys():
                self._node_types.update({
                    node_type_name: NodeType(
                        node_type_name,
                        self.yaml[NODE_TYPES][node_type_name]
                    )
                })
        return self._node_types

    @property
    def node_templates(self):
        for node_name in self.yaml[NODE_TEMPS].keys():
            if node_name not in self._node_templates.keys():
                self._node_templates.update({
                    node_name: NodeTemplate(
                        node_name,
                        self.yaml[NODE_TEMPS][node_name])
                })
        return self._node_templates

    @property
    def outputs(self):
        for output_key in self.yaml[OUTPUTS].keys():
            self._outputs.update(
                BlueprintOutput(output_key, self.yaml.get(output_key)))
        return self._outputs

    def _update_yaml_list_element(self, element_name, element_content):
        element = self.yaml.get(element_name, [])
        if element_content not in element:
            element.append(element_content)
        self.yaml[element_name] = element

    def _update_yaml_dict_element(self, element_name, element_content):
        element = self.yaml.get(element_name, {})
        self.yaml[element_name].update(merge_dicts(element_content, element))

    def remove_yaml_node_templates(self, node_template_key):
        try:
            del self.yaml[NODE_TEMPS][node_template_key]
        except KeyError:
            raise

    def remove_yaml_node_types(self, node_type_key):
        try:
            del self.yaml[NODE_TYPES][node_type_key]
        except KeyError:
            raise

    def update_yaml_imports(self, imports):
        self._update_yaml_list_element(IMPORTS, imports)

    def update_yaml_inputs(self, inputs):
        self._update_yaml_dict_element(INPUTS, inputs)

    def update_yaml_node_templates(self, node_templates):
        self._update_yaml_dict_element(NODE_TEMPS, node_templates)

    def update_yaml_node_types(self, node_types):
        self._update_yaml_dict_element(NODE_TYPES, node_types)

    def update_yaml_outputs(self, outputs):
        self._update_yaml_dict_element(OUTPUTS, outputs)
