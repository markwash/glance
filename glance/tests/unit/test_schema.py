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

from glance.common import exception
import glance.schema
from glance.tests import utils as test_utils


class TestBasicSchema(test_utils.BaseTestCase):

    def setUp(self):
        super(TestBasicSchema, self).setUp()
        properties = {
            'ham': {'type': 'string'},
            'eggs': {'type': 'string'},
        }
        self.schema = glance.schema.Schema('basic', properties)

    def test_validate_passes(self):
        obj = {'ham': 'no', 'eggs': 'scrambled'}
        self.schema.validate(obj) # No exception raised

    def test_validate_fails_on_extra_properties(self):
        obj = {'ham': 'virginia', 'eggs': 'scrambled', 'bacon': 'crispy'}
        self.assertRaises(exception.InvalidObject, self.schema.validate, obj)

    def test_validate_fails_on_bad_type(self):
        obj = {'eggs': 2}
        self.assertRaises(exception.InvalidObject, self.schema.validate, obj)

    def test_filter_strips_extra_properties(self):
        obj = {'ham': 'virginia', 'eggs': 'scrambled', 'bacon': 'crispy'}
        filtered = self.schema.filter(obj)
        expected = {'ham': 'virginia', 'eggs': 'scrambled'}
        self.assertEqual(filtered, expected)

    def test_raw_json_schema(self):
        expected = {
            'name': 'basic',
            'properties': {
                'ham': {'type': 'string'},
                'eggs': {'type': 'string'},
            },
            'additionalProperties': False,
        }
        self.assertEqual(self.schema.jsonschema, expected)


class TestPermissiveSchema(test_utils.BaseTestCase):

    def setUp(self):
        super(TestPermissiveSchema, self).setUp()
        properties = {
            'ham': {'type': 'string'},
            'eggs': {'type': 'string'},
        }
        self.schema = glance.schema.Schema('permissive', properties,
                                           additional_properties=True)

    def test_validate_with_additional_properties_allowed(self):
        obj = {'ham': 'virginia', 'eggs': 'scrambled', 'bacon': 'crispy'}
        self.schema.validate(obj) # No exception raised

    def test_validate_rejects_non_string_extra_properties(self):
        obj = {'ham': 'virginia', 'eggs': 'scrambled', 'grits': 1000}
        self.assertRaises(exception.InvalidObject, self.schema.validate, obj)

    def test_filter_passes_extra_properties(self):
        obj = {'ham': 'virginia', 'eggs': 'scrambled', 'bacon': 'crispy'}
        filtered = self.schema.filter(obj)
        self.assertEqual(filtered, obj)

    def test_raw_json_schema(self):
        expected = {
            'name': 'permissive',
            'properties': {
                'ham': {'type': 'string'},
                'eggs': {'type': 'string'},
            },
            'additionalProperties': {'type': 'string'},
        }
        self.assertEqual(self.schema.jsonschema, expected)
        

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


class TestSchemaAPI(test_utils.BaseTestCase):

    def setUp(self):
        super(TestSchemaAPI, self).setUp()
        self.schema_api = glance.schema.API(FAKE_BASE_PROPERTIES)

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
        self.config(allow_additional_image_properties=False)
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
        self.config(allow_additional_image_properties=True)
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
        self.config(allow_additional_image_properties=False)
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
