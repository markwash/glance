# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

import json

import requests

from glance.tests import functional


class TestSchemas(functional.FunctionalTest):

    def setUp(self):
        super(TestSchemas, self).setUp()
        self.cleanup()
        self.start_servers(**self.__dict__.copy())

    def test_resource(self):
        path = 'http://%s:%d/v2/schemas' % ('0.0.0.0', self.api_port)
        response = requests.get(path)
        self.assertEqual(response.status_code, 200)

        # Parse the links container into a usable dict
        output = json.loads(response.text)

        # We should only have links for image and access schemas
        self.assertEqual(set(['image', 'images', 'access']),
                         set(output.keys()))

        # Ensure the link works and custom properties are loaded
        path = 'http://%s:%d%s' % ('0.0.0.0', self.api_port, output['image'])
        response = requests.get(path)
        self.assertEqual(response.status_code, 200)
        schema = json.loads(response.text)
        expected = set([
            'id',
            'name',
            'visibility',
            'created_at',
            'updated_at',
            'tags',
            'type',
            'format',
            'self',
            'file',
            'access',
            'schema',
        ])
        self.assertEqual(expected, set(schema['properties'].keys()))

        path = 'http://%s:%d%s' % ('0.0.0.0', self.api_port, output['access'])
        response = requests.get(path)
        self.assertEqual(response.status_code, 200)
        json.loads(response.text)

        path = 'http://%s:%d%s' % ('0.0.0.0', self.api_port, output['images'])
        response = requests.get(path)
        self.assertEqual(response.status_code, 200)
        schema = json.loads(response.text)
        expected = set([
            'first',
            'next',
            'images',
            'schema',
        ])
        self.assertEqual(expected, set(schema['properties'].keys()))
