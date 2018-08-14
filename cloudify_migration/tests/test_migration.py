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
from cloudify_migration import CloudifyMigration
from cloudify_migration.mapping.azure import sources as az_sources


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
                'node_one_translated': {
                    'type': 'type.three',
                    'properties': {
                        'common_field_two': '2',
                        'common_field_one': 'one',
                        'variable_one': 'one'
                    }
                },
                'node_two_translated': {
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
                'node.type.five',
                'node.cloudify.nodes.Root']

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

    @property
    def expected_variables(self):
        return {
            'variable_one': 'variable_one',
            'variable_two': 'variable_two'
        }

    @property
    def expected_new_node_types(self):
        return [
            {
                'type.one': {
                    'properties': {
                        'common_field_two': {
                            'default': {}
                        },
                        'common_field_one': {
                            'default': {}
                        },
                        'variable_one': {
                            'default': {
                                'required': True,
                                'type': 'string'
                            }
                        }
                    },
                    'derived_from': 'cloudify.nodes.Root'
                }
            }, {
                'type.five': {
                    'properties': {
                        'variables': {
                            'default': {
                                'new_variable': 'new_variable',
                                'variable_two': 'variable_two',
                                'variable_one': 'variable_one'
                            }
                        },
                        'config': {
                            'default': {
                                'attributes': [
                                    'nested_property', 'nested_property']
                            }
                        }
                    },
                    'derived_from': 'cloudify.nodes.Root'
                }
            }, {
                'type.two': {
                    'properties': {
                        'common_field_two': {
                            'default': {}
                        },
                        'common_field_one': {
                            'default': {
                                'required': True,
                                'type': 'string'
                            }
                        },
                        'config': {
                            'default': {}
                        }
                    },
                    'derived_from': 'cloudify.nodes.Root'
                }
            }, {
                'cloudify.nodes.Root': {
                    'derived_from': 'cloudify.nodes.Root'
                }
            }, {
                'type.three': {
                    'properties': {
                        'variable_one': {
                            'default': 'variable_one'
                        }
                    },
                    'derived_from': 'cloudify.nodes.Root'
                }
            }, {
                'type.four': {
                    'properties': {
                        'resource_config': {
                            'default': {
                                'variable_two': 'variable_two'
                            }
                        }
                    },
                    'derived_from': 'cloudify.nodes.Root'
                }
            }]

    def test_0_cloudify_migration_properties(self):
        ctx = self.get_ctx()
        cfy_migration = CloudifyMigration(
            ctx, self.migration_mapping_file_name)
        self.assertTrue(hasattr(cfy_migration, 'logger'))
        self.assertTrue(hasattr(cfy_migration, 'blueprint'))
        self.assertTrue(hasattr(cfy_migration, '_read_blueprint_yaml'))
        self.assertTrue(hasattr(cfy_migration, 'update_blueprint_yaml'))
        self.assertTrue(hasattr(cfy_migration, '_blueprint_yaml'))
        self.assertTrue(hasattr(cfy_migration, 'mapping'))
        self.assertTrue(hasattr(cfy_migration, 'update_mapping_yaml'))
        self.assertTrue(hasattr(cfy_migration, '_read_mapping_yaml'))
        self.assertTrue(hasattr(cfy_migration, '_mapping_yaml'))

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
            self.assertTrue(hasattr(v, '__dict__'))
        self.assertEqual(len(cfy_migration.blueprint.node_templates), 3)
        test_node_template = cfy_migration.blueprint.node_templates.get(
            'node_one')
        self.assertEqual(test_node_template.type, 'type.one')
        for k, v in test_node_template.properties.iteritems():
            if k == 'common_field_two':
                self.assertEqual(v.value, '2')
            elif k == 'common_field_one' or k == 'variable_one':
                self.assertEqual(v.value, 'one')
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
        self.assertEqual(len(cfy_migration.mapping.members), 6)
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
        self.assertEqual(len(cfy_migration.variables), 2)
        test_variables = {}
        for k, v in cfy_migration.variables.iteritems():
            test_variables[k] = v.value
        self.assertEqual(test_variables, self.expected_variables)
        self.assertEqual(
            test_member.merged_specifications, self.merged_mapping_specs)

    def test_3_cloudify_migration_translating_blueprint(self):
        ctx = self.get_ctx()
        cfy_migration = CloudifyMigration(
            ctx, self.migration_mapping_file_name,
            self.old_blueprint_file.name)
        old_blueprint = deepcopy(cfy_migration.blueprint)
        cfy_migration.set_variables()
        new_blueprint = cfy_migration.blueprint
        self.assertNotEqual(new_blueprint, old_blueprint)
        self.assertNotIn('type.five', old_blueprint.node_types)
        self.assertIn('type.five', new_blueprint.node_types)
        self.assertNotIn('type.four', old_blueprint.node_types)
        self.assertIn('type.four', new_blueprint.node_types)
        self.assertNotIn('type.three', old_blueprint.node_types)
        self.assertIn('type.three', new_blueprint.node_types)
        self.assertEqual(
            self.expected_new_node_types,
            [v.__dict__ for k, v in new_blueprint.node_types.items()])
        self.assertIn(
            'type.five',
            cfy_migration.translated_blueprint.yaml['node_types'])
        self.assertIn(
            'type.three',
            cfy_migration.translated_blueprint.yaml['node_types'])
        self.assertIn(
            'type.four',
            cfy_migration.translated_blueprint.yaml['node_types'])
        self.assertIn(
            'cloudify.nodes.Root',
            cfy_migration.translated_blueprint.yaml['node_types'])
        self.assertNotIn(
            'type.one',
            cfy_migration.translated_blueprint.yaml['node_types'])
        self.assertNotIn(
            'type.two',
            cfy_migration.translated_blueprint.yaml['node_types'])
        self.assertIn(
            'type_four_generated',
            cfy_migration.translated_blueprint.yaml['node_templates'])
        self.assertIn(
            'node_three',
            cfy_migration.translated_blueprint.yaml['node_templates'])
        self.assertIn(
            'type_five_generated',
            cfy_migration.translated_blueprint.yaml['node_templates'])
        self.assertIn(
            'type_three_generated',
            cfy_migration.translated_blueprint.yaml['node_templates'])
        self.assertNotIn(
            'node_two',
            cfy_migration.translated_blueprint.yaml['node_templates'])
        self.assertNotIn(
            'node_one',
            cfy_migration.translated_blueprint.yaml['node_templates'])
        # print cfy_migration.translated_blueprint.yaml
        # self.assertTrue(False)

    def test_4_old_blueprint_valid(self):
        """ Validate the old blueprint data as YAML file.
        """
        self._validate_blueprint(self.old_blueprint_file.name)

    def test_5_old_blueprint_with_plugin_yaml_valid(self):
        """ Validate the old blueprint data as YAML file with plugin.yaml added.
        """

        self._validate_blueprint(self.modified_blueprint_file.name)

    def test_6_new_blueprint_valid(self):
        """ Validate the new blueprint data as YAML file.
        """
        self._validate_blueprint(self.new_blueprint_file.name)

    def test_7_azure_sources(self):
        member = az_sources.AzureResourceGroupSource()
        expected_common_spec = ['name', 'use_external_resource']
        self.assertEqual(
            member.node_type,
            'cloudify.azure.nodes.ResourceGroup')
        member_spec = [
            s.specification['specification']['properties'].keys()[0]
            for s in member.mapping_specs
        ]
        print member_spec
        for spec in member_spec:
            self.assertIn(
                spec,
                expected_common_spec)
        self.assertEqual(len(member.mapping_specs), 2)
