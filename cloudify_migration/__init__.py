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


from cloudify_migration import constants
from cloudify_migration.blueprint import MigrationBlueprint
from cloudify_migration.mapping import MigrationMapping
from cloudify_migration.node_template import SimplifiedNode
from cloudify_migration.exceptions import MigrationException
from cloudify_migration.validation import validate_mapping
from utils import read_yaml_file


class CloudifyMigration(object):

    def __init__(self, cloudify_context, mapping_file_resource):

        self._ctx = cloudify_context
        self.mapping_file_resource = mapping_file_resource
        self.mapping_file_path = \
            self._ctx.download_resource(self.mapping_file_resource)
        self.runtime_properties = self._ctx.instance.runtime_properties

    @property
    def logger(self, logger=None):
        return logger or self._ctx.logger

    @property
    def mapping(self):
        if constants.RESOURCE_ATTRIBUTE not in self.runtime_properties:
            migration = \
                read_yaml_file(self.mapping_file_path)
            if 'migration' not in migration:
                raise MigrationException(
                    'Invalid Migration: required list "migration" missing.')
            self.runtime_properties[constants.RESOURCE_ATTRIBUTE] = \
                migration['migration']
        return self.runtime_properties[constants.RESOURCE_ATTRIBUTE]

    @property
    def variables(self):
        if constants.VARS not in self.runtime_properties:
            self.runtime_properties[constants.VARS] = {}
        if not isinstance(self.runtime_properties[constants.VARS], dict):
            raise MigrationException(
                'Runtime property variables must be a dict.')
        return self.runtime_properties[constants.VARS]

    @property
    def common_fields(self):
        return self.mapping[constants.COMMON_FIELDS]

    @property
    def nodes_to_keep(self):
        return self.mapping[constants.NODES_TO_KEEP]

    @property
    def nodes_to_remove(self):
        return self.mapping[constants.NODES_TO_REMOVE]

    @property
    def nodes_to_add(self):
        return self.mapping[constants.NODES_TO_ADD]

    @property
    def blueprint_yaml(self):
        if constants.BLUEPRINT_YAML not in self.runtime_properties:
            return {}
        return self.runtime_properties[constants.BLUEPRINT_YAML]

    @property
    def blueprint(self):
        return MigrationBlueprint(self.blueprint_yaml)

    @property
    def removed_nodes(self):
        if constants.REMOVED_NODES not in self.runtime_properties:
            self.runtime_properties[constants.REMOVED_NODES] = []
        return self.runtime_properties[constants.REMOVED_NODES]

    def update_blueprint_yaml(self, old_blueprint_yaml=None):
        old_blueprint_yaml = old_blueprint_yaml or self.blueprint_yaml
        self.runtime_properties[constants.BLUEPRINT_YAML] = old_blueprint_yaml

    def update_variables(self, key, mapping, value):
        # TODO: Fix this garbage.
        if isinstance(mapping, basestring):
            mapping_steps = mapping.split('.')
            for step in mapping_steps:
                try:
                    value = getattr(value, step)
                except AttributeError:
                    if isinstance(value, dict):
                        value = value[step]
                    else:
                        raise
        self.variables[key] = value

    def apply_variables(self, mapping_key, mapping_value, node_template):
        # TODO: Fix this garbage.

        def recurse_mapping(_mapping_steps, _mapping_value):
            _mapping_steps.reverse()
            _value = {
                _mapping_steps[0]: self.variables.get(_mapping_value)
            }
            del _mapping_steps[0]
            for step in _mapping_steps:
                _value = {step: _value}
            return _value

        if isinstance(mapping_key, dict):
            pass

        if isinstance(mapping_key, basestring):
            mapping_steps = mapping_key.split('.')
            if not mapping_steps[0] == constants.PROPERTIES:
                return
            del mapping_steps[0]
            value = recurse_mapping(mapping_steps, mapping_value)
            for key in value.keys():
                node_template.update_properties(key, value[key])

    def validate(self):
        validate_mapping(self)

    def remove_nodes(self):
        # Check that we have a blueprint to work on.
        if not self.blueprint_yaml:
            raise MigrationException(
                constants.OPERATION_REMOVE_NODES.format(
                    'the blueprint_yaml is not set.'))
        self._remove_nodes_from_blueprint_yaml()

    def _remove_nodes_from_blueprint_yaml(self):
        """Remove nodes from the blueprint.yaml.
        """
        for node_to_remove in self.nodes_to_remove:
            for blueprint_node in self.blueprint.node_templates:
                if blueprint_node.id == node_to_remove.get('name') or \
                        blueprint_node.type == node_to_remove.get('type'):
                    # The blueprint_node is not JSON-serializable.
                    self.removed_nodes.append(
                        self.blueprint_yaml[constants.NT][blueprint_node.id])
                    del self.blueprint_yaml[constants.NT][blueprint_node.id]
                    self.blueprint.remove_node(blueprint_node.id)
                    self.update_blueprint_yaml()
                    for mapping_definition in node_to_remove['mappings']:
                        mm = MigrationMapping(**mapping_definition)
                        self.update_variables(mm.key, mm.value, blueprint_node)

    def add_nodes(self):
        # Check that we have a blueprint to work on.
        if not self.blueprint_yaml:
            raise MigrationException(
                constants.OPERATION_ADD_NODES.format(
                    'the blueprint_yaml is not set.'))
        self._add_nodes_to_blueprint_yaml()

    def _add_nodes_to_blueprint_yaml(self):
        for node_to_add in self.nodes_to_add:
            blueprint_node = SimplifiedNode(
                node_name=node_to_add['name'],
                node_definition={'type': node_to_add['type']})
            for mapping_definition in node_to_add['mappings']:
                mm = MigrationMapping(**mapping_definition)
                self.apply_variables(mm.key, mm.value, blueprint_node)
                self.blueprint_yaml[constants.NT].update(
                    blueprint_node.__dict__)
