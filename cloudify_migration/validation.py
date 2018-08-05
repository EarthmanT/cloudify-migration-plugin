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
from cloudify_migration.exceptions import MigrationException


def check_common_fields(migration_spec):
    """Validate the contents of the common_fields key.
    :param migration_spec: CloudifyMigration class.
    :return:
    """

    # Check that migration_spec.common_fields is a list.
    if not isinstance(migration_spec.common_fields, list):
        raise MigrationException(
            constants.VALIDATE_FIELD_TYPE.format(
                'common_fields', 'list'))

    # Check that migration_spec.common_fields are all strings.
    for li in migration_spec.common_fields:
        if not isinstance(li, basestring):
            raise MigrationException(
                constants.VALIDATE_FIELD_TYPE.format(
                    'common_fields', 'list of strings'))


def check_nodes_to_keep(migration_spec):
    """Validate the contents of the nodes_to_keep key.
    :param migration_spec: CloudifyMigration class.
    :return:
    """

    # Check that migration_spec.nodes_to_keep is a list.
    if not isinstance(migration_spec.nodes_to_keep, list):
        raise MigrationException(
            constants.VALIDATE_FIELD_TYPE.format(
                'nodes_to_keep', 'list'))

    # Check that migration_spec.nodes_to_keep are all valid.
    for li in migration_spec.nodes_to_keep:
        # Check that migration_spec.nodes_to_keep contains dictionaries.
        if not isinstance(li, dict):
            raise MigrationException(
                constants.VALIDATE_FIELD_TYPE.format(
                    'nodes_to_keep', 'list of dictionaries'))
        # Check that migration_spec.nodes_to_keep have name and type.
        if 'name' not in li and 'type' not in li:
            raise MigrationException(
                constants.VALIDATE_FIELD_CONTENT.format(
                    'nodes_to_remove', '"name" or "type"'))


def check_nodes_to_remove(migration_spec):
    """Validate the contents of the nodes_to_remove key.
    :param migration_spec: CloudifyMigration class.
    :return:
    """

    # Check that migration_spec.nodes_to_remove is a list.
    if not isinstance(migration_spec.nodes_to_remove, list):
        raise MigrationException(
            constants.VALIDATE_FIELD_TYPE.format(
                'nodes_to_remove', 'list'))
    for li in migration_spec.nodes_to_remove:
        if not isinstance(li, dict):
            raise MigrationException(
                constants.VALIDATE_FIELD_TYPE.format(
                    'nodes_to_remove', 'list of dictionaries'))
        if 'name' not in li and 'type' not in li:
            raise MigrationException(
                constants.VALIDATE_FIELD_CONTENT.format(
                    'nodes_to_remove', '"name" or "type"'))
        if 'mappings' not in li or \
                not isinstance(li.get('mappings'), list):
            raise MigrationException(
                constants.VALIDATE_FIELD_CONTENT.format(
                    'nodes_to_remove', ' a dictionary "mappings"'))


def check_nodes_to_add(migration_spec):
    """Validate the contents of the nodes_to_add key.
    :param migration_spec: CloudifyMigration class.
    :return:
    """

    # Check that migration_spec.nodes_to_add is a list.
    if not isinstance(migration_spec.nodes_to_add, list):
        raise MigrationException(
            constants.VALIDATE_FIELD_TYPE.format(
                'nodes_to_add', 'list'))
    for li in migration_spec.nodes_to_add:
        if not isinstance(li, dict):
            raise MigrationException(
                constants.VALIDATE_FIELD_TYPE.format(
                    'nodes_to_remove', 'list of dictionaries'))
        if 'name' not in li and 'type' not in li:
            raise MigrationException(
                constants.VALIDATE_FIELD_CONTENT.format(
                    'nodes_to_add', '"name" or "type"'))
        if 'mappings' not in li or \
                not isinstance(li.get('mappings'), list):
            raise MigrationException(
                constants.VALIDATE_FIELD_CONTENT.format(
                    'nodes_to_add', ' a dictionary "mappings"'))


def validate_mapping(migration_spec):
    check_common_fields(migration_spec)
    check_nodes_to_keep(migration_spec)
    check_nodes_to_remove(migration_spec)
    check_nodes_to_add(migration_spec)
