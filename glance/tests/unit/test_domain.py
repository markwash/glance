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

from glance.common import exception

from glance import domain

import glance.tests.unit.utils as unit_test_utils
import glance.tests.utils as test_utils


UUID1 = 'c80a1a6c-bd1f-41c5-90ee-81afedb1d58d'

TENANT1 = '6838eb7b-6ded-434a-882c-b344c77fe8df'


class TestImageFactory(test_utils.BaseTestCase):

    def setUp(self):
        super(TestImageFactory, self).setUp()

    def test_minimal_new_image(self):
        request = unit_test_utils.get_fake_request()
        self.image_factory = domain.ImageFactory(request.context)
        self.image = self.image_factory.new_image()
        self.assertTrue(self.image.image_id is not None)
        self.assertTrue(self.image.created_at is not None)
        self.assertEqual(self.image.created_at, self.image.updated_at)
        self.assertEqual(self.image.status, 'queued')
        self.assertEqual(self.image.visibility, 'private')
        self.assertEqual(self.image.owner, request.context.owner)
        self.assertEqual(self.image.name, None)
        self.assertEqual(self.image.size, None)
        self.assertEqual(self.image.min_disk, 0)
        self.assertEqual(self.image.min_ram, 0)
        self.assertEqual(self.image.protected, False)
        self.assertEqual(self.image.disk_format, None)
        self.assertEqual(self.image.container_format, None)
        self.assertEqual(self.image.extra_properties, {})
        self.assertEqual(self.image.tags, set([]))

    def test_new_image(self):
        request = unit_test_utils.get_fake_request()
        self.image_factory = domain.ImageFactory(request.context)
        self.image = self.image_factory.new_image(image_id=UUID1,
        name='image-1', min_disk=256)
        self.assertEqual(self.image.image_id, UUID1)
        self.assertTrue(self.image.created_at is not None)
        self.assertEqual(self.image.created_at, self.image.updated_at)
        self.assertEqual(self.image.status, 'queued')
        self.assertEqual(self.image.visibility, 'private')
        self.assertEqual(self.image.owner, request.context.owner)
        self.assertEqual(self.image.name, 'image-1')
        self.assertEqual(self.image.size, None)
        self.assertEqual(self.image.min_disk, 256)
        self.assertEqual(self.image.min_ram, 0)
        self.assertEqual(self.image.protected, False)
        self.assertEqual(self.image.disk_format, None)
        self.assertEqual(self.image.container_format, None)
        self.assertEqual(self.image.extra_properties, {})
        self.assertEqual(self.image.tags, set([]))

    def test_new_image_with_extra_properties_and_tags(self):
        request = unit_test_utils.get_fake_request()
        self.image_factory = domain.ImageFactory(request.context)

        extra_properties = {'foo': 'bar'}
        tags = ['one', 'two']
        self.image = self.image_factory.new_image(
                image_id=UUID1, name='image-1',
                extra_properties=extra_properties, tags=tags)

        self.assertEqual(self.image.image_id, UUID1)
        self.assertTrue(self.image.created_at is not None)
        self.assertEqual(self.image.created_at, self.image.updated_at)
        self.assertEqual(self.image.status, 'queued')
        self.assertEqual(self.image.visibility, 'private')
        self.assertEqual(self.image.owner, request.context.owner)
        self.assertEqual(self.image.name, 'image-1')
        self.assertEqual(self.image.size, None)
        self.assertEqual(self.image.min_disk, 0)
        self.assertEqual(self.image.min_ram, 0)
        self.assertEqual(self.image.protected, False)
        self.assertEqual(self.image.disk_format, None)
        self.assertEqual(self.image.container_format, None)
        self.assertEqual(self.image.extra_properties, {'foo': 'bar'})
        self.assertEqual(self.image.tags, set(['one', 'two']))

    def test_new_image_with_extra_properties_and_tags(self):
        request = unit_test_utils.get_fake_request()
        self.image_factory = domain.ImageFactory(request.context)

        extra_properties = {'foo': 'bar'}
        tags = ['one', 'two']
        self.image = self.image_factory.new_image(
                image_id=UUID1, name='image-1',
                extra_properties=extra_properties, tags=tags)

        self.assertEqual(self.image.image_id, UUID1)
        self.assertTrue(self.image.created_at is not None)
        self.assertEqual(self.image.created_at, self.image.updated_at)
        self.assertEqual(self.image.status, 'queued')
        self.assertEqual(self.image.visibility, 'private')
        self.assertEqual(self.image.owner, request.context.owner)
        self.assertEqual(self.image.name, 'image-1')
        self.assertEqual(self.image.size, None)
        self.assertEqual(self.image.min_disk, 0)
        self.assertEqual(self.image.min_ram, 0)
        self.assertEqual(self.image.protected, False)
        self.assertEqual(self.image.disk_format, None)
        self.assertEqual(self.image.container_format, None)
        self.assertEqual(self.image.extra_properties, {'foo': 'bar'})
        self.assertEqual(self.image.tags, set(['one', 'two']))

    def test_new_image_read_only_property(self):
        request = unit_test_utils.get_fake_request()
        self.image_factory = domain.ImageFactory(request.context)

        self.assertRaises(exception.ReadonlyProperty,
                        self.image_factory.new_image, image_id=UUID1,
                        name='image-1', size=256)

    def test_new_image_unexpected_property(self):
        request = unit_test_utils.get_fake_request()
        self.image_factory = domain.ImageFactory(request.context)

        self.assertRaises(TypeError,
                        self.image_factory.new_image, image_id=UUID1,
                        image_name='name-1')

    def test_new_image_reserved_property(self):
        request = unit_test_utils.get_fake_request()
        self.image_factory = domain.ImageFactory(request.context)
        extra_properties = {'deleted': True}
        self.assertRaises(exception.ReservedProperty,
                        self.image_factory.new_image, image_id=UUID1,
                        extra_properties=extra_properties)
