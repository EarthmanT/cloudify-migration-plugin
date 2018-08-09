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

from cloudify_migration import constants
from cloudify_migration.exceptions import MigrationException


class MigrationMappingMemberSpecElement(object):

    def __init__(self,
                 element_index,
                 element_key,
                 element_type,
                 child=None,
                 value=None):

        self.key = element_key
        self.type = self.set_type(element_type)
        self.index = element_index
        self.child = child
        self.value = self._get_value(value)

    @staticmethod
    def set_type(type_key):
        if type_key == 'dict':
            return {}
        elif type_key == 'list':
            return []
        elif type_key == 'string':
            return ''
        else:
            return None

    def _assign_value_as_child(self):
        if isinstance(self.type, dict):
            return {self.child.key: self.child.value}
        elif isinstance(self.type, list):
            return [self.child.value]
        else:
            return self.child.value

    def _get_value(self, value):
        if not value and self.child is not None:
            return self._assign_value_as_child()
        else:
            return value

    @property
    def __dict__(self):
        return {
            'index': self.index,
            'key': self.key,
            'type': self.type,
            'value': self.value,
        }


class MigrationMappingMemberSpec(object):

    def __init__(self, mapping_spec):
        self.value = mapping_spec.get('value')
        self._elements_path = mapping_spec.get('elements_path', '').split('.')
        self._elements_types = \
            mapping_spec.get('elements_types', '').split('.')
        self._elements = sorted(self._get_elements(), key=lambda x: x.index)

    def _get_elements(self):
        element_list = []
        reversed_keys = deepcopy(self._elements_path)
        reversed_types = deepcopy(self._elements_types)
        reversed_keys.reverse()
        reversed_types.reverse()
        for n in range(0, len(reversed_keys)):
            init_args = {
                'element_index': n,
                'element_key': reversed_keys[n],
                'element_type': reversed_types[n]
            }
            if n == 0:
                init_args.update({'value': self.value})
            elif n > 0:
                init_args.update({'child': element_list[0]})
            e = MigrationMappingMemberSpecElement(**init_args)
            element_list.insert(0, e)
        return element_list

    @property
    def specification(self):
        previous = None
        for current in self._elements:
            if previous:
                current = self.merge_specification_elements(previous, current)
            previous = current
        return {
            'specification': {
                current.__dict__['key']: current.__dict__['value']
            }
        }

    @staticmethod
    def merge_specification_elements(older, newer):

        if older.index == newer.index:
            newer.value.update(merge_dicts(older.value, newer.value))
        elif older.index == newer.index - 1:
            if isinstance(newer.type, dict) and isinstance(older.type, dict):
                if older.key not in newer.value:
                    newer.value[older.key] = older.value
            elif isinstance(newer.type, list) and isinstance(
                    older.type, basestring):
                if older.value not in newer.value:
                    newer.value.append(older.value)
            elif isinstance(newer.type, dict) and isinstance(older.type, list):
                if older.key not in newer.value:
                    newer.value[older.key] = older.value
                elif not isinstance(newer.value[older.key], list):
                    # TODO: Check this out.
                    raise MigrationException()
                else:
                    newer.value[older.key] = \
                        newer.value[older.key] + older.value
        return newer


class MigrationMappingMember(object):

    def __init__(self, mapping_key, mapping_definition):
        self.key = mapping_key
        self.definition = mapping_definition
        self.node_name = self.definition.get('node_name')
        self.node_type = self.definition.get('node_type')
        self.mapping_direction = self.definition.get('mapping_direction')
        self._mapping_specs_yaml = self.definition.get('mappings')
        self._mapping_specs = self._get_mapping_specs()

    @property
    def mapping_specs(self):
        return self._mapping_specs

    @property
    def merged_specifications(self):
        older = None
        for mapping_spec in self._mapping_specs:
            newer = mapping_spec.specification
            if older:
                newer = merge_dicts(older, newer)
            older = newer
        return newer

    def _get_mapping_specs(self):
        mapping_spec_list = []
        for spec_yaml in self._mapping_specs_yaml:
            mapping_spec_list.append(MigrationMappingMemberSpec(spec_yaml))
        return mapping_spec_list


class MigrationMapping(object):

    def __init__(self, mapping_yaml):
        self._members = {}
        self.yaml = mapping_yaml
        self._mappings = self.yaml.get(constants.MAPPINGS)
        for k, v in self._mappings.items():
            self.update_members(k, MigrationMappingMember(k, v))

    @property
    def members(self):
        member_list = []
        for _, _member in self._members.items():
            member_list.append(_member)
        return member_list

    def update_members(self, member_key, member_definition):
        if member_key in self._members:
            member_definition.update(self._members[member_key])
        self._members[member_key] = member_definition

    def get_member(self, member_name):
        for _name, _member in self._members.items():
            if _name == member_name:
                return _member
        return None


def merge_dicts(_source, _destination):
    for key, value in _source.items():
        if isinstance(value, dict):
            # get node or create one
            node = _destination.setdefault(key, {})
            merge_dicts(value, node)
        else:
            _destination[key] = value
    return _destination
