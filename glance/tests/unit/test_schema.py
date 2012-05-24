# Copyright 2012 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the 'License'); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an 'AS IS' BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import ConfigParser
import io
import unittest

from glance.common import exception
import glance.schema
from glance.tests import utils as test_utils


FAKE_BASE_PROPERTIES = {
    'fake1': {
        'id': {
            'type': 'string',
            'description': 'An identifier for the image',
            'required': False,
            'maxLength': 36,
        },
        'name': {
            'type': 'string',
            'description': 'Descriptive name for the image',
            'required': True,
        },
    },
    'image': {
        'gazump': {
            'type': 'string',
            'description': 'overcharge; rip off',
            'required': False,
        },
        'cumulus': {
            'type': 'string',
            'description': 'a heap; pile',
            'required': True,
        },
    },
}


class TestStringProperty(unittest.TestCase):
    def test(self):
        prop = glance.schema.StringProperty('bar')
        expected = {'type': 'string', 'description': 'bar', 'optional': True}
        self.assertEquals(prop.jsonschema(), expected)

    def test_with_max(self):
        prop = glance.schema.StringProperty('bar', 100)
        expected = {
            'type': 'string',
            'description': 'bar',
            'maxLength': 100,
            'optional': True,
            }
        self.assertEquals(prop.jsonschema(), expected)

    def test_with_max_not_int(self):
        self.assertRaises(ValueError,
                          glance.schema.StringProperty,
                          'bar', max_length='abc')

    def test_required(self):
        prop = glance.schema.StringProperty('bar', required=True)
        expected = {'type': 'string', 'description': 'bar'}
        self.assertEquals(prop.jsonschema(), expected)

    def test_default_specified(self):
        prop = glance.schema.StringProperty('bar', default='baz')
        expected = {
            'type': 'string',
            'description': 'bar',
            'optional': True,
            'default': 'baz',
            }
        self.assertEquals(prop.jsonschema(), expected)


class TestStringPropertyLoadFromConfig(unittest.TestCase):
    def test_load_from_config(self):
        config = '\n'.join([
            '[foo]',
            'type = string',
            'description = bar',
        ])
        parser = ConfigParser.RawConfigParser()
        parser.readfp(io.BytesIO(config))
        prop = glance.schema.StringProperty.parse(parser, 'foo')
        expected = {
            'type': 'string',
            'description': 'bar',
            'optional': True,
            }
        self.assertEqual(prop.jsonschema(), expected)

    def test_load_from_config_with_required(self):
        config = '\n'.join([
            '[foo]',
            'type = string',
            'description = bar',
            'required = true',
        ])
        parser = ConfigParser.RawConfigParser()
        parser.readfp(io.BytesIO(config))
        prop = glance.schema.StringProperty.parse(parser, 'foo')
        expected = {
            'type': 'string',
            'description': 'bar',
            }
        self.assertEqual(prop.jsonschema(), expected)

    def test_load_from_config_with_default(self):
        config = '\n'.join([
            '[foo]',
            'type = string',
            'description = bar',
            'default = blah',
        ])
        parser = ConfigParser.RawConfigParser()
        parser.readfp(io.BytesIO(config))
        prop = glance.schema.StringProperty.parse(parser, 'foo')
        expected = {
            'type': 'string',
            'description': 'bar',
            'optional': True,
            'default': 'blah'
            }
        self.assertEqual(prop.jsonschema(), expected)

    def test_load_from_config_with_max_length(self):
        config = '\n'.join([
            '[foo]',
            'type = string',
            'description = bar',
            'max_length = 101',
        ])
        parser = ConfigParser.RawConfigParser()
        parser.readfp(io.BytesIO(config))
        prop = glance.schema.StringProperty.parse(parser, 'foo')
        expected = {
            'type': 'string',
            'description': 'bar',
            'maxLength': 101,
            'optional': True,
            }
        self.assertEqual(prop.jsonschema(), expected)


class TestEnumProperty(unittest.TestCase):
    def test(self):
        prop = glance.schema.EnumProperty('bar', ['j', 'k', 'l'])
        expected = {
            'type': 'string',
            'description': 'bar',
            'enum': ['j', 'k', 'l'],
            'optional': True,
            }
        self.assertEquals(prop.jsonschema(), expected)

    def test_load_from_config(self):
        config = '\n'.join([
            '[foo]',
            'type = enum',
            'description = bar',
            'options = alpha,beta,gamma',
        ])
        parser = ConfigParser.RawConfigParser()
        parser.readfp(io.BytesIO(config))
        prop = glance.schema.EnumProperty.parse(parser, 'foo')
        expected = {
            'type': 'string',
            'description': 'bar',
            'optional': True,
            'enum': ['alpha', 'beta', 'gamma'],
            }
        self.assertEqual(prop.jsonschema(), expected)


class TestBoolProperty(unittest.TestCase):
    def test(self):
        prop = glance.schema.BoolProperty('bar')
        expected = {'type': 'boolean', 'description': 'bar', 'optional': True}
        self.assertEquals(prop.jsonschema(), expected)


class TestType(unittest.TestCase):
    def test(self):
        prop = glance.schema.StringProperty(desc='bar', required=True)
        schema = glance.schema.Type('baz', {'foo': prop})
        expected = {
            'name': 'baz',
            'properties': {
                'foo': {
                    'type': 'string',
                    'description': 'bar',
                },
            },
            'additionalProperties': False,
        }
        self.assertEqual(schema.jsonschema(), expected)

    def test_with_additional_properties(self):
        prop = glance.schema.StringProperty(desc='bar', required=True)
        schema = glance.schema.Type('baz', {'foo': prop}, additional=True)
        expected = {
            'name': 'baz',
            'properties': {
                'foo': {
                    'type': 'string',
                    'description': 'bar',
                },
            },
            'additionalProperties': {
                'type': 'string',
            },
        }
        self.assertEqual(schema.jsonschema(), expected)

    def test_parse(self):
        schema = glance.schema.Type('baz')
        config = '\n'.join([
            '[foo]',
            'type = string',
            'description = bar',
            'required = true',
        ])
        parser = ConfigParser.RawConfigParser()
        parser.readfp(io.BytesIO(config))
        schema.parse(parser)
        expected = {
            'name': 'baz',
            'properties': {
                'foo': {
                    'type': 'string',
                    'description': 'bar',
                },
            },
            'additionalProperties': False,
        }
        self.assertEqual(schema.jsonschema(), expected)

    def test_load_multiple_properties_from_config(self):
        schema = glance.schema.Type('mytype')
        config = '\n'.join([
            '[stringprop]',
            'type = string',
            'description = A very cool description',
            'required = true',
            '[enumprop]',
            'type = enum',
            'description = one thing or another',
            'options = one thing,another',
        ])
        parser = ConfigParser.RawConfigParser()
        parser.readfp(io.BytesIO(config))
        schema.parse(parser)
        expected = {
            'name': 'mytype',
            'properties': {
                'stringprop': {
                    'type': 'string',
                    'description': 'A very cool description',
                },
                'enumprop': {
                    'type': 'string',
                    'description': 'one thing or another',
                    'enum': ['one thing', 'another'],
                    'optional': True
                },
            },
            'additionalProperties': False,
        }
        self.assertEqual(schema.jsonschema(), expected)

    def test_parse_name_conflict(self):
        prop = glance.schema.StringProperty('type of gas', default='helium')
        schema = glance.schema.Type('blimp', {'gas': prop})
        config = '\n'.join([
            '[size]',
            'type = enum',
            'description = size of blimp',
            'options = large,extra large,extra extra large',
            '[gas]',
            'type = enum',
            'description = type of gas',
            'default = hydrogen',
            'options = hydrogen,helium'
        ])
        parser = ConfigParser.RawConfigParser()
        parser.readfp(io.BytesIO(config))
        self.assertRaises(exception.SchemaLoadError, schema.parse, parser)

        # Schema should not have changed due to conflict
        expected = {
            'name': 'blimp',
            'properties': {
                'gas': {
                    'type': 'string',
                    'description': 'type of gas',
                    'default': 'helium',
                    'optional': True,
                },
            },
            'additionalProperties': False,
        }
        self.assertEqual(schema.jsonschema(), expected)

    def test_parse_name_conflict_but_equal(self):
        prop = glance.schema.EnumProperty('frame material',
                                          options=['Mg', 'Al', 'Pb'],
                                          default='Mg')
        schema = glance.schema.Type('zeppelin', {'frame': prop})
        config = '\n'.join([
            '[frame]',
            'type = enum',
            'options = Mg,Al,Pb',
            'default = Mg',
        ])
        parser = ConfigParser.RawConfigParser()
        parser.readfp(io.BytesIO(config))
        # Even though it isn't strictly necessary, we conflict here
        self.assertRaises(exception.SchemaLoadError, schema.parse, parser)


class TestSchemaAPI(unittest.TestCase):
    def setUp(self):
        self.conf = test_utils.TestConfigOpts()
        self.schema_api = glance.schema.API(self.conf, FAKE_BASE_PROPERTIES)

    def test_get_schema(self):
        output = self.schema_api.get_schema('fake1')
        expected = {
            'name': 'fake1',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'An identifier for the image',
                    'required': False,
                    'maxLength': 36,
                },
                'name': {
                    'type': 'string',
                    'description': 'Descriptive name for the image',
                    'required': True,
                },
            },
            'additionalProperties': False,
        }
        self.assertEqual(output, expected)

    def test_get_schema_after_load(self):
        extra_props = {
            'prop1': {
                'type': 'string',
                'description': 'Just some property',
                'required': False,
                'maxLength': 128,
            },
        }

        self.schema_api.set_custom_schema_properties('fake1', extra_props)
        output = self.schema_api.get_schema('fake1')

        expected = {
            'name': 'fake1',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'An identifier for the image',
                    'required': False,
                    'maxLength': 36,
                },
                'name': {
                    'type': 'string',
                    'description': 'Descriptive name for the image',
                    'required': True,
                },
                'prop1': {
                    'type': 'string',
                    'description': 'Just some property',
                    'required': False,
                    'maxLength': 128,
                },
            },
            'additionalProperties': False,
        }
        self.assertEqual(output, expected)

    def test_get_schema_load_conflict(self):
        extra_props = {
            'name': {
                    'type': 'int',
                    'description': 'Descriptive integer for the image',
                    'required': False,
                },
        }
        self.assertRaises(exception.SchemaLoadError,
                          self.schema_api.set_custom_schema_properties,
                          'fake1',
                          extra_props)

        # Schema should not have changed due to the conflict
        output = self.schema_api.get_schema('fake1')
        expected = {
            'name': 'fake1',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'An identifier for the image',
                    'required': False,
                    'maxLength': 36,
                },
                'name': {
                    'type': 'string',
                    'description': 'Descriptive name for the image',
                    'required': True,
                },
            },
            'additionalProperties': False,
        }
        self.assertEqual(output, expected)

    def test_get_schema_load_conflict_base_property(self):
        extra_props = {
            'name': {
                    'type': 'string',
                    'description': 'Descriptive name for the image',
                    'required': True,
                },
        }

        # Schema update should not raise an exception, but it should also
        # remain unchanged
        self.schema_api.set_custom_schema_properties('fake1', extra_props)
        output = self.schema_api.get_schema('fake1')
        expected = {
            'name': 'fake1',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'An identifier for the image',
                    'required': False,
                    'maxLength': 36,
                },
                'name': {
                    'type': 'string',
                    'description': 'Descriptive name for the image',
                    'required': True,
                },
            },
            'additionalProperties': False,
        }
        self.assertEqual(output, expected)

    def test_get_image_schema_with_additional_properties_disabled(self):
        self.conf.allow_additional_image_properties = False
        output = self.schema_api.get_schema('image')
        expected = {
            'name': 'image',
            'properties': {
                'gazump': {
                    'type': 'string',
                    'description': 'overcharge; rip off',
                    'required': False,
                },
                'cumulus': {
                    'type': 'string',
                    'description': 'a heap; pile',
                    'required': True,
                },
            },
            'additionalProperties': False,
        }
        self.assertEqual(output, expected)

    def test_get_image_schema_with_additional_properties_enabled(self):
        self.conf.allow_additional_image_properties = True
        output = self.schema_api.get_schema('image')
        expected = {
            'name': 'image',
            'properties': {
                'gazump': {
                    'type': 'string',
                    'description': 'overcharge; rip off',
                    'required': False,
                },
                'cumulus': {
                    'type': 'string',
                    'description': 'a heap; pile',
                    'required': True,
                },
            },
            'additionalProperties': {'type': 'string'},
        }
        self.assertEqual(output, expected)

    def test_get_other_schema_with_additional_image_properties_enabled(self):
        self.conf.allow_additional_image_properties = True
        output = self.schema_api.get_schema('fake1')
        expected = {
            'name': 'fake1',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'An identifier for the image',
                    'required': False,
                    'maxLength': 36,
                },
                'name': {
                    'type': 'string',
                    'description': 'Descriptive name for the image',
                    'required': True,
                },
            },
            'additionalProperties': False,
        }
        self.assertEqual(output, expected)
