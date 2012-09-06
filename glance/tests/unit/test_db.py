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

import glance.context
from glance.common import exception
from glance.common import utils
import glance.db
import glance.tests.unit.utils as unit_test_utils
import glance.tests.utils as test_utils


UUID1 = 'c80a1a6c-bd1f-41c5-90ee-81afedb1d58d'
UUID2 = 'a85abd86-55b3-4d5b-b0b4-5d0a6e6042fc'
UUID3 = '971ec09a-8067-4bc8-a91f-ae3557f1c4c7'
UUID4 = '6bbe7cc2-eae7-4c0f-b50d-a7160b0c6a86'

TENANT1 = '6838eb7b-6ded-434a-882c-b344c77fe8df'
TENANT2 = '2c014f32-55eb-467d-8fcb-4bd706012f81'
TENANT3 = '5a3e60e8-cfa9-4a9e-a90a-62b42cea92b8'
TENANT4 = 'c6c87f25-8a94-47ed-8c83-053c25f42df4'

USER1 = '54492ba0-f4df-4e4e-be62-27f4d76b29cf'


def _db_fixture(id, **kwargs):
    obj = {
        'id': id,
        'name': None,
        'is_public': False,
        'properties': {},
        'checksum': None,
        'owner': None,
        'status': 'queued',
        'tags': [],
        'size': None,
        'location': None,
        'protected': False,
        'disk_format': None,
        'container_format': None,
        'deleted': False,
        'min_ram': None,
        'min_disk': None,
    }
    obj.update(kwargs)
    return obj


class TestImageRepo(test_utils.BaseTestCase):

    def setUp(self):
        self.db = unit_test_utils.FakeDB()
        self.db.reset()
        self.context = glance.context.RequestContext(user=USER1, tenant=TENANT1)
        self.image_repo = glance.db.ImageRepo(self.context, self.db)
        self._create_images()
        super(TestImageRepo, self).setUp()

    def _create_images(self):
        self.db.reset()
        self.images = [
            _db_fixture(UUID1, owner=TENANT1, name='1', size=256,
                        is_public=True, status='active'),
            _db_fixture(UUID2, owner=TENANT1, name='2',
                        size=512, is_public=False),
            _db_fixture(UUID3, owner=TENANT3, name='3',
                        size=512, is_public=True),
            _db_fixture(UUID4, owner=TENANT4, name='4', size=1024),
        ]
        [self.db.image_create(None, image) for image in self.images]

        self.db.image_tag_set_all(None, UUID1, ['ping', 'pong'])

    def test_get(self):
        image = self.image_repo.get(UUID1) 
        self.assertEquals(image.image_id, UUID1)
        self.assertEquals(image.name, '1')
        self.assertEquals(image.tags, set(['ping', 'pong']))
        self.assertEquals(image.visibility, 'public')
        self.assertEquals(image.status, 'active')
        self.assertEquals(image.size, 256)
        self.assertEquals(image.owner, TENANT1)

    def test_get_not_found(self):
        self.assertRaises(exception.NotFound, self.image_repo.get,
                          utils.generate_uuid()) 

    def test_get_forbidden(self):
        self.assertRaises(exception.NotFound, self.image_repo.get, UUID4)

    def test_list(self):
        images = self.image_repo.list()
        image_ids = set([i.image_id for i in images])
        self.assertEqual(set([UUID1, UUID2, UUID3]), image_ids)

