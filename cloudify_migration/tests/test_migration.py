########
# Copyright (c) 2018 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
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
# from cloudify_migration import constants
from cloudify_migration import CloudifyMigration
# from cloudify_migration.exceptions import MigrationException
# from cloudify_migration.mapping import MigrationMapping


class TestMigration(unittest.TestCase):

    def setUp(self):
        super(TestMigration, self).setUp()
        self.migration_mapping_file_name = \
            os.path.join(os.path.dirname(__file__), 'migration-mapper.yaml')
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
            node_id='test_node_id',
            node_name='test_node_name',
            deployment_id='test_deployment_name',
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
            'tosca_definitions_version': 'cloudify_dsl_1_3',
            'imports': [],
            'inputs': {},
            'node_types': {
                'cloudify.nodes.Root': {
                },
                'type.one': {
                    'properties': {
                        'common_field_one': {
                            'default': {}
                        },
                        'common_field_two': {
                            'default': {}
                        },
                        'variable_one': {
                            'required': True,
                            'type': 'string'
                        }
                    },
                    'derived_from': 'cloudify.nodes.Root'
                },
                'type.two': {
                    'properties': {
                        'common_field_two': {
                            'default': {}
                        },
                        'common_field_one': {
                            'required': True,
                            'type': 'string'
                        },
                        'config': {
                            'default': {}
                        }
                    },
                    'derived_from': 'cloudify.nodes.Root'
                }
            },
            'node_templates': {
                'node_one': {
                    'type': 'type.one',
                    'properties': {
                        'common_field_two': '2',
                        'common_field_one': 'one',
                        'variable_one': 'one'
                    }
                },
                'node_two': {
                    'type': 'type.two',
                    'properties': {
                        'common_field_one': 'one',
                        'config': {
                            'variable_two': 'two'
                        }
                    }
                },
                'node_three': {
                    'type': 'cloudify.nodes.Root'
                }
            },
            'outputs': {}
        }
        return data

    @property
    def new_blueprint(self):
        data = {
            'tosca_definitions_version': 'cloudify_dsl_1_3',
            'imports': [],
            'node_types': {
                'cloudify.nodes.Root': {
                },
                'type.three': {
                    'properties': {
                        'common_field_one': {
                            'default': {}
                        },
                        'common_field_two': {
                            'default': {}
                        },
                        'variable_one': {
                            'type': 'string'
                        }
                    },
                    'derived_from': 'cloudify.nodes.Root'
                },
                'type.four': {
                    'properties': {
                        'common_field_one': {
                            'default': {}
                        },
                        'common_field_two': {
                            'default': {}
                        },
                        'resource_config': {
                            'default': {}
                        }
                    },
                    'derived_from': 'cloudify.nodes.Root'
                },
                'type.five': {
                    'properties': {
                        'common_field_one': {
                            'default': {}
                        },
                        'common_field_two': {
                            'default': {}
                        },
                        'variables': {
                            'default': {}
                        }
                    },
                    'derived_from': 'cloudify.nodes.Root'
                }
            },
            'node_templates': {
                'node_one_converted': {
                    'type': 'type.three',
                    'properties': {
                        'common_field_two': '2',
                        'common_field_one': 'one',
                        'variable_one': 'one'
                    }
                },
                'node_two_converted': {
                    'type': 'type.four',
                    'properties': {
                        'common_field_one': 'one',
                        'resource_config': {
                            'variable_two': 'two'
                        }
                    }
                },
                'node_three': {
                    'type': 'cloudify.nodes.Root'
                },
                'new_resource': {
                    'type': 'type.five',
                    'properties': {
                        'variables': {
                            'variable_one': 'one',
                            'variable_two': 'two'
                        }
                    }
                }
            }
        }
        return data

    @property
    def mapping_member_names(self):
        return ['node.type.one',
                'node.type.two',
                'node.type.three',
                'node.type.four',
                'node.type.five']

    @property
    def merged_mapping_specs(self):
        data = {
            'specification': {
                'properties': {
                    'variables': {
                        'new_variable': 'new_variable',
                        'variable_one': 'variable_one',
                        'variable_two': 'variable_two'
                    },
                    'config': {
                        'attributes': ['nested_property', 'nested_property']
                    }
                }
            }
        }
        return data

    def test_0_cloudify_migration_properties(self):
        ctx = self.get_ctx()
        cfy_migration = CloudifyMigration(
            ctx, self.migration_mapping_file_name)
        self.assertTrue(hasattr(cfy_migration, 'logger'))
        self.assertTrue(hasattr(cfy_migration, 'blueprint'))
        self.assertTrue(hasattr(cfy_migration, 'read_blueprint_yaml'))
        self.assertTrue(hasattr(cfy_migration, 'update_blueprint_yaml'))
        self.assertTrue(hasattr(cfy_migration, 'blueprint_yaml'))
        self.assertTrue(hasattr(cfy_migration, 'mapping'))
        self.assertTrue(hasattr(cfy_migration, 'update_mapping_yaml'))
        self.assertTrue(hasattr(cfy_migration, 'read_mapping_yaml'))
        self.assertTrue(hasattr(cfy_migration, 'mapping_yaml'))

    def test_1_cloudify_migration_blueprint_properties(self):
        ctx = self.get_ctx()
        cfy_migration = CloudifyMigration(
            ctx, self.migration_mapping_file_name,
            self.old_blueprint_file.name)

        self.assertTrue(hasattr(cfy_migration.blueprint, 'imports'))
        for _ in cfy_migration.blueprint.imports:
            self.assertTrue(hasattr(cfy_migration.blueprint.imports, 'key'))
        self.assertEqual(len(cfy_migration.blueprint.imports), 0)

        self.assertTrue(hasattr(cfy_migration.blueprint, 'inputs'))
        for _, v in cfy_migration.blueprint.inputs:
            self.assertTrue(hasattr(v, 'type'))
            self.assertTrue(hasattr(v, 'description'))
            self.assertTrue(hasattr(v, 'default'))
        self.assertEqual(len(cfy_migration.blueprint.inputs), 0)

        self.assertTrue(hasattr(cfy_migration.blueprint, 'node_types'))
        for _, v in cfy_migration.blueprint.node_types.items():
            self.assertTrue(hasattr(v, 'id'))
            self.assertTrue(hasattr(v, 'derived_from'))
            self.assertTrue(hasattr(v, 'properties'))
            self.assertTrue(hasattr(v, 'interfaces'))
        self.assertEqual(len(cfy_migration.blueprint.node_types), 3)

        self.assertTrue(hasattr(cfy_migration.blueprint, 'node_templates'))
        for _, v in cfy_migration.blueprint.node_templates.items():
            self.assertTrue(hasattr(v, 'id'))
            self.assertTrue(hasattr(v, 'type'))
            self.assertTrue(hasattr(v, 'properties'))
            self.assertTrue(hasattr(v, 'relationships'))
            self.assertTrue(hasattr(v, 'update_properties'))
            self.assertTrue(hasattr(v, '__dict__'))
        self.assertEqual(len(cfy_migration.blueprint.node_templates), 3)
        test_node_template = cfy_migration.blueprint.node_templates.get(
            'node_one')
        self.assertEqual(test_node_template.type, 'type.one')
        self.assertEqual(test_node_template.properties, {
                        'common_field_two': '2',
                        'common_field_one': 'one',
                        'variable_one': 'one'
        })
        self.assertEqual(test_node_template.type, 'type.one')

        self.assertTrue(hasattr(cfy_migration.blueprint, 'outputs'))
        for _, v in cfy_migration.blueprint.outputs:
            self.assertTrue(hasattr(v, 'description'))
            self.assertTrue(hasattr(v, 'value'))
        self.assertEqual(len(cfy_migration.blueprint.outputs), 0)

    def test_2_cloudify_migration_mapping_properties(self):
        ctx = self.get_ctx()
        cfy_migration = CloudifyMigration(
            ctx, self.migration_mapping_file_name,
            self.old_blueprint_file.name)
        self.assertTrue(hasattr(cfy_migration.mapping, 'yaml'))
        self.assertTrue(hasattr(cfy_migration.mapping, 'members'))
        self.assertTrue(hasattr(cfy_migration.mapping, 'update_members'))
        self.assertEqual(len(cfy_migration.mapping.members), 5)
        for mapping_member in cfy_migration.mapping.members:
            self.assertIn(mapping_member.key, self.mapping_member_names)
        for member_name in self.mapping_member_names:
            self.assertIsNotNone(cfy_migration.mapping.get_member(member_name))
        test_member_name = 'node.type.five'
        test_member = cfy_migration.mapping.get_member(test_member_name)
        self.assertIsNone(test_member.node_name)
        self.assertEqual(test_member.node_type, 'type.five')
        self.assertEqual(test_member.mapping_direction, 'destination')
        self.assertEqual(len(test_member.mapping_specs), 4)
        self.assertEqual(
            test_member.merged_specifications, self.merged_mapping_specs)

    def test_1_old_blueprint_valid(self):
        ''' Validate the old blueprint data as YAML file.
        '''
        self._validate_blueprint(self.old_blueprint_file.name)

    def test_2_old_blueprint_with_plugin_yaml_valid(self):
        ''' Validate the old blueprint data as YAML file with plugin.yaml added.
        '''

        self._validate_blueprint(self.modified_blueprint_file.name)

    def test_3_new_blueprint_valid(self):
        ''' Validate the new blueprint data as YAML file.
        '''
        self._validate_blueprint(self.new_blueprint_file.name)
