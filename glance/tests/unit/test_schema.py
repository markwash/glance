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


class TestString(unittest.TestCase):
    def test(self):
        prop = glance.schema.String('foo', 'bar')
        expected = {'type': 'string', 'description': 'bar', 'optional': True}
        self.assertEquals(prop.schema(), expected)

    def test_with_max(self):
        prop = glance.schema.String('foo', 'bar', 100)
        expected = {
            'type': 'string',
            'description': 'bar', 
            'maxLength': 100,
            'optional': True,
            }
        self.assertEquals(prop.schema(), expected)

    def test_with_max_not_int(self):
        self.assertRaises(ValueError,
                          glance.schema.String, 'foo', 'bar',
                          max_length='abc')

    def test_required(self):
        prop = glance.schema.String('foo', 'bar', required=True)
        expected = {'type': 'string', 'description': 'bar'}
        self.assertEquals(prop.schema(), expected)

    def test_default_specified(self):
        prop = glance.schema.String('foo', 'bar', default='baz')
        expected = {
            'type': 'string',
            'description': 'bar', 
            'optional': True,
            'default': 'baz',
            }
        self.assertEquals(prop.schema(), expected)


class TestEnum(unittest.TestCase):
     def test(self):
        prop = glance.schema.Enum('boo', 'bar', ['j', 'k', 'l'])
        expected = {
            'type': 'enum',
            'description': 'bar', 
            'enum' : ['j', 'k', 'l'],
            'optional': True,
            }
        self.assertEquals(prop.schema(), expected)
        
class TestBool(unittest.TestCase):
     def test(self):
        prop = glance.schema.Bool('boo', 'bar')
        expected = {'type': 'boolean', 'description': 'bar', 'optional': True}
        self.assertEquals(prop.schema(), expected)
 
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
