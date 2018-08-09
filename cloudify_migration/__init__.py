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

import yaml

from cloudify_migration import constants
from cloudify_migration.blueprint import MigrationBlueprint
from cloudify_migration.exceptions import MigrationException
from cloudify_migration.mapping import MigrationMapping
from cloudify_migration.variables import MigrationVariable


class CloudifyMigration(object):

    def __init__(self,
                 cloudify_context,
                 mapping_blueprint_resource, blueprint_yaml=None):

        self._ctx = cloudify_context
        self.runtime_properties = self._ctx.instance.runtime_properties

        self.mapping_blueprint_resource = mapping_blueprint_resource
        self.mapping_blueprint_file_path = \
            self._ctx.download_resource(self.mapping_blueprint_resource)

        self.read_mapping_yaml(self.mapping_blueprint_file_path)

        if blueprint_yaml:
            self.read_blueprint_yaml(blueprint_yaml)

    @staticmethod
    def read_yaml_file(file_path):
        with open(file_path, 'r') as stream:
            try:
                return yaml.load(stream)
            except yaml.YAMLError as e:
                raise MigrationException('Invalid YAML: {0}'.format(str(e)))

    @property
    def blueprint(self):
        return MigrationBlueprint(self.blueprint_yaml)

    @property
    def blueprint_yaml(self):
        if constants.BLUEPRINT_YAML not in self.runtime_properties:
            return {}
        return self.runtime_properties[constants.BLUEPRINT_YAML]

    @property
    def logger(self, logger=None):
        return logger or self._ctx.logger

    @property
    def mapping(self):
        return MigrationMapping(self.mapping_yaml)

    @property
    def mapping_yaml(self):
        if constants.MAPPING_YAML not in self.runtime_properties:
            return {}
        return self.runtime_properties[constants.MAPPING_YAML]

    def update_blueprint_yaml(self, blueprint_yaml=None):
        blueprint_yaml = blueprint_yaml or self.blueprint_yaml
        self.runtime_properties[constants.BLUEPRINT_YAML] = blueprint_yaml

    def read_blueprint_yaml(self, blueprint_yaml_file):
        self.update_blueprint_yaml(self.read_yaml_file(blueprint_yaml_file))

    def update_mapping_yaml(self, mapping_yaml=None):
        mapping_yaml = mapping_yaml or self.mapping_yaml
        self.runtime_properties[constants.MAPPING_YAML] = mapping_yaml

    def read_mapping_yaml(self, mapping_yaml_file):
        self.update_mapping_yaml(self.read_yaml_file(mapping_yaml_file))

    def _get_variables_and_assign_values(self):
        variable_mappings = {}
        for member in self.mapping.members:
            if not member.mapping_direction == 'source':
                continue
            for mapping_spec in member.mapping_specs:
                variable = MigrationVariable(
                    mapping_spec.value,
                    mapping_spec.specification['specification'])
                variable_mappings.update({mapping_spec.value: variable})
        return variable_mappings

    @property
    def variables(self):
        return self._get_variables_and_assign_values()
