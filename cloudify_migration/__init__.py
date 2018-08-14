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


from copy import deepcopy
from tempfile import NamedTemporaryFile

from cloudify_migration import constants
from cloudify_migration.blueprint import (
    MigrationBlueprint,
    NodeTemplate,
    NodeType)
from cloudify_migration.mapping import MigrationMapping
from cloudify_migration.variables import MigrationVariable
from cloudify_migration.utils import (
    read_yaml_file,
    write_yaml_file)


class CloudifyMigration(object):

    def __init__(self,
                 cloudify_context,
                 mapping_blueprint_resource, blueprint_yaml=None):

        self._ctx = cloudify_context
        self.runtime_properties = self._ctx.instance.runtime_properties

        self.mapping_blueprint_resource = mapping_blueprint_resource
        self.mapping_blueprint_file_path = \
            self._ctx.download_resource(self.mapping_blueprint_resource)

        self._read_mapping_yaml(self.mapping_blueprint_file_path)

        if blueprint_yaml:
            self._read_blueprint_yaml(blueprint_yaml)

    @property
    def _blueprint_yaml(self):
        """This is the raw source for the blueprint.
        """
        if constants.BLUEPRINT_YAML not in self.runtime_properties:
            return {}
        return self.runtime_properties[constants.BLUEPRINT_YAML]

    @property
    def _mapping_yaml(self):
        """This is the raw source for the mappings
        """
        if constants.MAPPING_YAML not in self.runtime_properties:
            return {}
        return self.runtime_properties[constants.MAPPING_YAML]

    @property
    def blueprint(self):
        return MigrationBlueprint(self._blueprint_yaml)

    @property
    def logger(self, logger=None):
        return logger or self._ctx.logger

    @property
    def mapping(self):
        return MigrationMapping(self._mapping_yaml)

    @property
    def translated_blueprint(self):
        return self._translate_blueprint()

    @property
    def variables(self):
        return self._get_variables()

    def _effect_additions(self, _blueprint=None):
        _blueprint = _blueprint or self.blueprint
        for _addition in self.mapping.additions:
            node_type = _addition.node_type_to_add
            node_template = _addition.node_template_to_add
            if _addition.is_node_type and _addition.add_node_types:
                _blueprint.update_yaml_node_types(node_type.__dict__)
            if _addition.is_node_type and _addition.add_node_templates:
                _blueprint.update_yaml_node_templates(node_template.__dict__)
            else:
                raise NotImplemented(
                    'Only node_types can be added right not.')

    def _effect_removals(self, _blueprint=None):
        _blueprint = _blueprint or self.blueprint
        for _remove in self.mapping.removals:
            if _remove.is_node_type and _remove.remove_node_types:
                try:
                    _blueprint.remove_yaml_node_types(_remove.key)
                except KeyError:
                    self.logger.error(
                        'Won\'t remove node type {0}. Not found.'.format(
                            _remove.key))
            if _remove.is_node_type and _remove.remove_node_templates:
                for k, v in _blueprint.node_templates.iteritems():
                    if v.type == _remove.key:
                        _blueprint.remove_yaml_node_templates(k)
            else:
                raise NotImplemented(
                    'Only node_types can be added right not.')

    def _get_variables(self):
        variable_mappings = {}
        for member in self.mapping.members:
            if not member.mapping_direction == 'source':
                # We only assign variables from source mapping members.
                continue
            for mapping_spec in member.mapping_specs:
                variable = MigrationVariable(
                    mapping_spec.value,
                    mapping_spec.specification['specification'])
                variable_mappings.update({mapping_spec.value: variable})
        return variable_mappings

    def _read_blueprint_yaml(self, blueprint_yaml_file):
        self.update_blueprint_yaml(read_yaml_file(blueprint_yaml_file))

    def _read_mapping_yaml(self, mapping_yaml_file):
        self.update_mapping_yaml(read_yaml_file(mapping_yaml_file))

    def _set_node_type_variable(self,
                                node_type_key,
                                mapping_specs,
                                _blueprint=None):
        if node_type_key not in _blueprint.node_types:
            node_type = NodeType(node_type_key, {})
        else:
            node_type = _blueprint.node_types.get(node_type_key)
        for spec in mapping_specs:
            variable = self.variables.get(spec.value)
            node_type.update_node(
                spec.specification['specification'], variable)
        _blueprint.update_yaml_node_types(node_type.__dict__)

    def _set_node_template_variable(self,
                                    node_template_key,
                                    mapping_specs,
                                    _blueprint=None):
        if node_template_key not in _blueprint.node_templates:
            node_template = NodeTemplate(node_template_key, {})
        else:
            node_template = _blueprint.node_templates.get(node_template_key)
        for spec in mapping_specs:
            variable = self.variables.get(spec.value)
            node_template.update_node(
                spec.specification['specification'], variable)
        _blueprint.update_yaml_node_templates(node_template.__dict__)

    def _write_blueprint_yaml(self, blueprint_path=None, yaml_content=None):
        yaml_content = yaml_content or self.blueprint.yaml
        if not blueprint_path:
            f = NamedTemporaryFile()
            blueprint_path = f.name
        write_yaml_file(blueprint_path, yaml_content)
        return blueprint_path

    def _translate_blueprint(self):
        _blueprint = deepcopy(self.blueprint)
        self._effect_additions(_blueprint)
        self.set_variables(_blueprint)
        self._effect_removals(_blueprint)
        return _blueprint

    def write_translated_blueprint(self, _path=None, _blueprint=None):
        _blueprint = _blueprint or self.translated_blueprint
        return self._write_blueprint_yaml(_path, _blueprint.yaml)

    def update_blueprint_yaml(self, blueprint_yaml=None):
        blueprint_yaml = blueprint_yaml or self.blueprint_yaml
        self.runtime_properties[constants.BLUEPRINT_YAML] = blueprint_yaml

    def update_mapping_yaml(self, mapping_yaml=None):
        mapping_yaml = mapping_yaml or self.mapping_yaml
        self.runtime_properties[constants.MAPPING_YAML] = mapping_yaml

    def set_variables(self, _blueprint=None):
        _blueprint = _blueprint or self.blueprint
        for member in self.mapping.members:
            if not member.mapping_direction == 'destination':
                continue
            if member.node_type and not member.node_name:
                self._set_node_type_variable(
                    member.node_type,
                    member.mapping_specs,
                    _blueprint)
            elif member.node_type and member.node_name:
                self._set_node_template_variable(
                    member.node_name,
                    member.mapping_specs,
                    _blueprint
                )
            else:
                raise NotImplemented('Unsupported case called.')
