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
import os
import unittest
import tempfile
import yaml

from cloudify.mocks import MockCloudifyContext
from cloudify.state import current_ctx
from cloudify_cli.utils import (
    get_import_resolver, is_validate_definitions_version)
from dsl_parser.parser import parse_from_path
from cloudify_migration import constants
from cloudify_migration import CloudifyMigration
from cloudify_migration.exceptions import MigrationException

MIGRATION_MAPPING = os.path.join(
    os.path.dirname(__file__), 'migration-mapper.yaml')


class TestMigration(unittest.TestCase):

    def setUp(self):
        super(TestMigration, self).setUp()
        self.old_blueprint_file = self._get_blueprint_file(
            self.old_blueprint)
        self.new_blueprint_file = self._get_blueprint_file(
            self.new_blueprint)
        self.plugin_yaml_path = os.path.join(
            os.path.dirname(__file__), '../../plugin.yaml')
        old_blueprint_yaml = deepcopy(self.old_blueprint)
        old_blueprint_yaml['imports'].append(self.plugin_yaml_path)
        self.modified_blueprint_file = self._get_blueprint_file(
            old_blueprint_yaml)

    def tearDown(self):
        super(TestMigration, self).tearDown()
        os.remove(self.old_blueprint_file.name)
        os.remove(self.new_blueprint_file.name)

    def _get_blueprint_file(self, blueprint_contents):
        f = tempfile.NamedTemporaryFile()
        with open(f.name, 'w') as outfile:
            yaml.dump(blueprint_contents, outfile, default_flow_style=False)
        return f

    def _validate_blueprint(self, blueprint_file):
        resolver = get_import_resolver()
        validate_version = is_validate_definitions_version()
        parse_from_path(
            dsl_file_path=blueprint_file,
            resolver=resolver,
            validate_version=validate_version)

    def get_ctx(self,
                properties=None,
                runtime_properties=None,
                relationships=None):

        def _mock_download_resource(_file_path):
            return _file_path

        _ctx = MockCloudifyContext(
            node_id="test_node_id",
            node_name="test_node_name",
            deployment_id="test_deployment_name",
            properties=properties or {},
            runtime_properties=runtime_properties or {},
            relationships=relationships or [],
            operation={'retry_number': 0}
        )
        setattr(_ctx, 'download_resource', _mock_download_resource)
        current_ctx.set(_ctx)
        return _ctx

    @property
    def old_blueprint(self):
        data = {
            "tosca_definitions_version": "cloudify_dsl_1_3",
            "imports": [],
            "node_types": {
                "cloudify.nodes.Root": {
                },
                "type.one": {
                    "properties": {
                        "common_field_one": {
                            "default": {}
                        },
                        "common_field_two": {
                            "default": {}
                        },
                        "variable_one": {
                            "required": True,
                            "type": "string"
                        }
                    },
                    "derived_from": "cloudify.nodes.Root"
                },
                "type.two": {
                    "properties": {
                        "common_field_two": {
                            "default": {}
                        },
                        "common_field_one": {
                            "required": True,
                            "type": "string"
                        },
                        "config": {
                            "default": {}
                        }
                    },
                    "derived_from": "cloudify.nodes.Root"
                }
            },
            "node_templates": {
                "node_one": {
                    "type": "type.one",
                    "properties": {
                        "common_field_two": "2",
                        "common_field_one": "one",
                        "variable_one": "one"
                    }
                },
                "node_two": {
                    "type": "type.two",
                    "properties": {
                        "common_field_one": "one",
                        "config": {
                            "variable_two": "two"
                        }
                    }
                },
                "node_three": {
                    "type": "cloudify.nodes.Root"
                }
            }
        }
        return data

    @property
    def new_blueprint(self):
        data = {
            "tosca_definitions_version": "cloudify_dsl_1_3",
            "imports": [],
            "node_types": {
                "cloudify.nodes.Root": {
                },
                "type.three": {
                    "properties": {
                        "common_field_one": {
                            "default": {}
                        },
                        "common_field_two": {
                            "default": {}
                        },
                        "variable_one": {
                            "type": "string"
                        }
                    },
                    "derived_from": "cloudify.nodes.Root"
                },
                "type.four": {
                    "properties": {
                        "common_field_one": {
                            "default": {}
                        },
                        "common_field_two": {
                            "default": {}
                        },
                        "resource_config": {
                            "default": {}
                        }
                    },
                    "derived_from": "cloudify.nodes.Root"
                },
                "type.five": {
                    "properties": {
                        "common_field_one": {
                            "default": {}
                        },
                        "common_field_two": {
                            "default": {}
                        },
                        "variables": {
                            "default": {}
                        }
                    },
                    "derived_from": "cloudify.nodes.Root"
                }
            },
            "node_templates": {
                "node_one_converted": {
                    "type": "type.three",
                    "properties": {
                        "common_field_two": "2",
                        "common_field_one": "one",
                        "variable_one": "one"
                    }
                },
                "node_two_converted": {
                    "type": "type.four",
                    "properties": {
                        "common_field_one": "one",
                        "resource_config": {
                            "variable_two": "two"
                        }
                    }
                },
                "node_three": {
                    "type": "cloudify.nodes.Root"
                },
                "new_resource": {
                    "type": "type.five",
                    "properties": {
                        "variables": {
                            "variable_one": "one",
                            "variable_two": "two"
                        }
                    }
                }
            }
        }
        return data

    @property
    def common_fields(self):
        return ['common_field_one', 'common_field_two']

    @property
    def nodes_names_to_keep(self):
        return ['node_three', 'node_not']

    @property
    def nodes_types_to_remove(self):
        return ['type.one', 'type.two']

    @property
    def nodes_names_to_add(self):
        return ['node_one_converted', 'node_two_converted', 'new_resource']

    def test_0_migration_class(self):
        """ Spot check the cloudify_migration.CloudifyMigration class.
        Called "test_0", because tests are executed alphabetical order.
        This test checks that:
          * The class has the required properties.
          * The values of the properties are as expected with the example.
          * The example builds a valid class.
        """

        ctx = self.get_ctx()
        cfy_migration = CloudifyMigration(ctx, MIGRATION_MAPPING)

        # Check that basic properties are all there.
        self.assertTrue(hasattr(cfy_migration, 'mapping_file_resource'))
        self.assertTrue(hasattr(cfy_migration, 'mapping_file_path'))
        self.assertTrue(hasattr(cfy_migration, 'logger'))
        self.assertTrue(hasattr(cfy_migration, 'variables'))
        # Initialize resource and make sure it's the right format.
        self.assertTrue(isinstance(cfy_migration.mapping, dict))
        self.assertTrue(
            isinstance(
                ctx.instance.runtime_properties['resource'], dict))

        # Make sure the resource has the expected values.
        self.assertTrue(self.common_fields == cfy_migration.common_fields)
        self.assertTrue(
            self.nodes_names_to_keep ==
            [node['name'] for node in cfy_migration.nodes_to_keep])
        self.assertTrue(
            self.nodes_types_to_remove ==
            [node['type'] for node in cfy_migration.nodes_to_remove])
        self.assertTrue(
            self.nodes_names_to_add ==
            [node['name'] for node in cfy_migration.nodes_to_add])

        # Make sure it is a valid migration resource.
        self.assertIsNone(cfy_migration.validate())

    def test_1_old_blueprint_valid(self):
        """ Validate the old blueprint data as YAML file.
        """
        self._validate_blueprint(self.old_blueprint_file.name)

    def test_2_old_blueprint_with_plugin_yaml_valid(self):
        """ Validate the old blueprint data as YAML file with plugin.yaml added.
        """

        self._validate_blueprint(self.modified_blueprint_file.name)

    def test_3_new_blueprint_valid(self):
        """ Validate the new blueprint data as YAML file.
        """
        self._validate_blueprint(self.new_blueprint_file.name)

    def test_4_blueprint_yaml(self):
        """ Check that we can set the old blueprint and that what is stored is
        what is expected.
        """
        ctx = self.get_ctx()
        cfy_migration = CloudifyMigration(ctx, MIGRATION_MAPPING)
        # First check that its None before we set it.
        self.assertTrue(not cfy_migration.blueprint_yaml)
        with open(self.modified_blueprint_file.name, 'r') as stream:
            modified_yaml = yaml.load(stream)
        cfy_migration.update_blueprint_yaml(modified_yaml)
        self.assertEqual(
            modified_yaml,
            cfy_migration.blueprint_yaml)
        cfy_migration.update_blueprint_yaml(
            old_blueprint_yaml={'pawned': True})
        self.assertEqual(
            {'pawned': True},
            cfy_migration.blueprint_yaml)

    def test_5_remove_nodes(self):
        """Check that:
        * remove_nodes raises an error if no blueprint is loaded.
        * remove_nodes removes the right nodes.
        * remove_nodes sets the correct variables.
        """

        ctx = self.get_ctx()
        cfy_migration = CloudifyMigration(ctx, MIGRATION_MAPPING)
        self.assertRaises(MigrationException, cfy_migration.remove_nodes)
        cfy_migration.update_blueprint_yaml(self.old_blueprint)
        cfy_migration.remove_nodes()
        self.assertEqual(
            len(cfy_migration.removed_nodes), 2)
        self.assertNotIn('node_one',
                         cfy_migration.blueprint_yaml[constants.NT].keys())
        self.assertNotIn('node_two',
                         cfy_migration.blueprint_yaml[constants.NT].keys())
        VARIABLES = {'variable_one': 'one', 'variable_two': 'two'}
        self.assertEqual(
            VARIABLES,
            ctx.instance.runtime_properties[constants.VARS]
        )
        self.assertEqual(
            VARIABLES,
            cfy_migration.variables)

    def test_6_add_nodes(self):
        ctx = self.get_ctx()
        cfy_migration = CloudifyMigration(ctx, MIGRATION_MAPPING)
        self.assertRaises(MigrationException, cfy_migration.remove_nodes)
        cfy_migration.update_blueprint_yaml(self.old_blueprint)
        cfy_migration.add_nodes()
