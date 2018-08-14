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

from cloudify_migration.exceptions import MigrationException


def get_value_by_key(dictionary, find_key):
    if not isinstance(dictionary, dict):
        return
    for key, value in dictionary.iteritems():
        if key == find_key:
            return value
        elif isinstance(value, dict):
            return get_value_by_key(value, find_key)
        else:
            return


def merge_dicts(_source, _destination, variable=None):

    # TODO: I am uncertain about this condition.
    if isinstance(_destination, basestring) and not variable:
        print "_destination, basestring", _destination
        _destination = {_destination: _destination}
    elif isinstance(_destination, basestring) and variable \
            and _destination == variable.key:
        _destination = {_destination: variable.value}

    # This seems to work except when _destination.setdefault returns a string.
    # That's why we have the previous part. Messed up.
    for key, value in _source.items():
        if isinstance(value, dict):
            node = _destination.setdefault(key, {})
            merge_dicts(value, node, variable)
        else:
            if variable and value == variable.key:
                value = variable.value
            _destination[key] = value

    _source.update(_destination)

    return _source


def read_yaml_file(file_path):
    with open(file_path, 'r') as stream:
        try:
            return yaml.load(stream)
        except yaml.YAMLError as e:
            raise MigrationException('Invalid YAML: {0}'.format(str(e)))


def write_yaml_file(file_path, yaml_content):
    with open(file_path, 'w') as outfile:
        try:
            yaml.dump(yaml_content, outfile, default_flow_style=False)
        except yaml.YAMLError as e:
            raise MigrationException('Invalid YAML: {0}'.format(str(e)))
