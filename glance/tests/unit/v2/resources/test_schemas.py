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

from glance.api.v2.resources import schemas
import glance.tests.unit.utils as unit_test_utils
import glance.tests.utils as test_utils


class TestSchemasController(test_utils.BaseTestCase):

    def setUp(self):
        super(TestSchemasController, self).setUp()
        self.controller = schemas.Controller()

    def test_index(self):
        req = unit_test_utils.get_fake_request()
        output = self.controller.index(req)
        expected = {'links': [
            {'rel': 'image', 'href': '/v2/schemas/image'},
            {'rel': 'access', 'href': '/v2/schemas/image/access'},
        ]}
        self.assertEqual(expected, output)

    def test_image(self):
        req = unit_test_utils.get_fake_request()
        output = self.controller.image(req)
        self.assertEqual(output['name'], 'image')

    def test_access(self):
        req = unit_test_utils.get_fake_request()
        output = self.controller.access(req)
        self.assertEqual(output['name'], 'access')
