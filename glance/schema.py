# Copyright 2012 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import copy
import json
import logging

import jsonschema

from glance.common import exception


logger = logging.getLogger(__name__)


_BASE_SCHEMA_PROPERTIES = {
    'image': {
        'id': {
            'type': 'string',
            'description': 'An identifier for the image',
            'maxLength': 36,
        },
        'name': {
            'type': 'string',
            'description': 'Descriptive name for the image',
            'maxLength': 255,
        },
        'visibility': {
            'type': 'string',
            'description': 'Scope of image accessibility',
            'enum': ['public', 'private'],
        },
    },
    'access': {
        'tenant_id': {
          'type': 'string',
          'description': 'The tenant identifier',
        },
        'can_share': {
          'type': 'boolean',
          'description': 'Ability of tenant to share with others',
          'default': False,
        },
    },
}


class PropertyHelper(object):
    def __init__(self, desc, required, default):
        self.description = desc
        self.required = required
        self.default = default

    def jsonschema(self):
        schema = {'description': self.description}
        if not self.required:
            schema['optional'] = True
        if self.default is not None:
            schema['default'] = self.default
        return schema

    @classmethod
    def parse(self, config, name):
        if config.has_option(name, 'required'):
            required = config.getboolean(name, 'required')
        else:
            required = False
        if config.has_option(name, 'default'):
            default = config.get(name, 'default')
        else:
            default = None
        desc = config.get(name, 'description')
        return desc, required, default


class StringProperty(object):
    def __init__(self, desc, max_length=None, required=False, default=None):
        self.helper = PropertyHelper(desc, required, default)
        if max_length is not None:
            max_length = int(max_length)
        self.max_length = max_length

    def jsonschema(self):
        schema = self.helper.jsonschema()
        schema['type'] = 'string'
        if self.max_length is not None:
            schema['maxLength'] = self.max_length
        return schema

    @classmethod
    def parse(cls, config, name):
        desc, required, default = PropertyHelper.parse(config, name)
        if config.has_option(name, 'max_length'):
            max_length = config.getint(name, 'max_length')
        else:
            max_length = None
        return StringProperty(desc=desc, required=required, default=default,
                      max_length=max_length)


class EnumProperty(object):
    def __init__(self, desc, options, required=False, default=None):
        self.helper = PropertyHelper(desc, required, default)
        self.options = options

    def jsonschema(self):
        schema = self.helper.jsonschema()
        schema['type'] = 'string'
        schema['enum'] = self.options
        return schema

    @classmethod
    def parse(cls, config, name):
        desc, required, default = PropertyHelper.parse(config, name)
        options = config.get(name, 'options').split(',')
        return EnumProperty(desc, options, required=required, default=default)


class BoolProperty(object):
    def __init__(self, desc, required=False, default=None):
        self.helper = PropertyHelper(desc, required, default)

    def jsonschema(self):
        schema = self.helper.jsonschema()
        schema['type'] = 'boolean'
        return schema


class Type(object):
    def __init__(self, name, properties=None, additional=False):
        self.name = name
        if properties is None:
            properties = {}
        self.properties = properties
        self.additional = additional

    def jsonschema(self):
        properties = {}
        for name, prop in self.properties.iteritems():
            properties[name] = prop.jsonschema()
        if self.additional:
            additional_props = {'type': 'string'}
        else:
            additional_props = False
        return {
            'name': self.name,
            'properties': properties,
            'additionalProperties': additional_props,
        }

    def parse(self, config):
        names = config.sections()
        self._check_property_name_conflicts(names)
        for name in names:
            # NOTE(markwash): only support string-backed custom properties
            klasses = {'string': StringProperty, 'enum': EnumProperty}
            klass = klasses[config.get(name, 'type')]
            prop = klass.parse(config, name)
            self.properties[name] = prop

    def _check_property_name_conflicts(self, names):
        existing_names = set(self.properties.keys())
        new_names = set(names)
        conflicts = new_names.intersection(existing_names)
        if len(conflicts) > 0:
            props = ', '.join(conflicts)
            reason = _("custom properties (%(props)s) conflict "
                       "with base properties")
            raise exception.SchemaLoadError(reason=reason % {'props': props})


class API(object):
    def __init__(self, conf, base_properties=_BASE_SCHEMA_PROPERTIES):
        self.conf = conf
        self.base_properties = base_properties
        self.schema_properties = copy.deepcopy(self.base_properties)

    def get_schema(self, name):
        if name == 'image' and self.conf.allow_additional_image_properties:
            additional = {'type': 'string'}
        else:
            additional = False
        return {
            'name': name,
            'properties': self.schema_properties[name],
            'additionalProperties': additional
        }

    def set_custom_schema_properties(self, schema_name, custom_properties):
        """Update the custom properties of a schema with those provided."""
        schema_properties = copy.deepcopy(self.base_properties[schema_name])

        # Ensure custom props aren't attempting to override base props
        base_keys = set(schema_properties.keys())
        custom_keys = set(custom_properties.keys())
        intersecting_keys = base_keys.intersection(custom_keys)
        conflicting_keys = [k for k in intersecting_keys
                            if schema_properties[k] != custom_properties[k]]
        if len(conflicting_keys) > 0:
            props = ', '.join(conflicting_keys)
            reason = _("custom properties (%(props)s) conflict "
                       "with base properties")
            raise exception.SchemaLoadError(reason=reason % {'props': props})

        schema_properties.update(copy.deepcopy(custom_properties))
        self.schema_properties[schema_name] = schema_properties

    def validate(self, schema_name, obj):
        schema = self.get_schema(schema_name)
        try:
            jsonschema.validate(obj, schema)
        except jsonschema.ValidationError as e:
            raise exception.InvalidObject(schema=schema_name, reason=str(e))


def read_schema_properties_file(conf, schema_name):
    """Find the schema properties files and load them into a dict."""
    schema_filename = 'schema-%s.json' % schema_name
    match = conf.find_file(schema_filename)
    if match:
        schema_file = open(match)
        schema_data = schema_file.read()
        return json.loads(schema_data)
    else:
        msg = _('Could not find schema properties file %s. Continuing '
                'without custom properties')
        logger.warn(msg % schema_filename)
        return {}


def load_custom_schema_properties(conf, api):
    """Extend base image and access schemas with custom properties."""
    for schema_name in ('image', 'access'):
        image_properties = read_schema_properties_file(conf, schema_name)
        api.set_custom_schema_properties(schema_name, image_properties)
