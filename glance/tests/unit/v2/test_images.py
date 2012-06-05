import datetime
import json

import webob

from sqlalchemy import exc
from glance.common import context
from glance.common import utils
from glance.api.v2 import router as rserver
from glance.db import api as db_api
from glance.db import models as db_models
from glance.tests.unit import base


_gen_uuid = utils.generate_uuid

UUID1 = _gen_uuid()
UUID2 = _gen_uuid()


class TestRegistryAPI(base.IsolatedUnitTest):
    def setUp(self):
        """Establish a clean test environment"""
        super(TestRegistryAPI, self).setUp()
        self.api = context.UnauthenticatedContextMiddleware(
                rserver.API(self.conf), self.conf)
        self.FIXTURES = [
            {'id': UUID1,
             'name': 'fake image #1',
             'status': 'active',
             'disk_format': 'ami',
             'container_format': 'ami',
             'is_public': False,
             'created_at': datetime.datetime.utcnow(),
             'updated_at': datetime.datetime.utcnow(),
             'deleted_at': None,
             'deleted': False,
             'checksum': None,
             'min_disk': 0,
             'min_ram': 0,
             'size': 13,
             'location': "file:///%s/%s" % (self.test_dir, UUID1),
             'properties': {'type': 'kernel'}},
            {'id': UUID2,
             'name': 'fake image #2',
             'status': 'active',
             'disk_format': 'vhd',
             'container_format': 'ovf',
             'is_public': True,
             'created_at': datetime.datetime.utcnow(),
             'updated_at': datetime.datetime.utcnow(),
             'deleted_at': None,
             'deleted': False,
             'checksum': None,
             'min_disk': 5,
             'min_ram': 256,
             'size': 19,
             'location': "file:///%s/%s" % (self.test_dir, UUID2),
             'properties': {}}]
        self.context = context.RequestContext(is_admin=True)
        db_api.configure_db(self.conf)
        self.destroy_fixtures()
        self.create_fixtures()

    def tearDown(self):
        """Clear the test environment"""
        super(TestRegistryAPI, self).tearDown()
        self.destroy_fixtures()

    def create_fixtures(self):
        for fixture in self.FIXTURES:
            db_api.image_create(self.context, fixture)
            # We write a fake image file to the filesystem
            with open("%s/%s" % (self.test_dir, fixture['id']), 'wb') as image:
                image.write("chunk00000remainder")
                image.flush()

    def destroy_fixtures(self):
        # Easiest to just drop the models and re-create them...
        db_models.unregister_models(db_api._ENGINE)
        db_models.register_models(db_api._ENGINE)

    def test_get_index_marker(self):
        """
        Tests that the /images API returns list of
        public images that conforms to a marker query param
        """
        time1 = datetime.datetime.utcnow() + datetime.timedelta(seconds=5)
        time2 = datetime.datetime.utcnow() + datetime.timedelta(seconds=4)
        time3 = datetime.datetime.utcnow()

        UUID3 = _gen_uuid()
        extra_fixture = {'id': UUID3,
                         'status': 'active',
                         'is_public': True,
                         'disk_format': 'vhd',
                         'container_format': 'ovf',
                         'name': 'new name! #123',
                         'size': 19,
                         'checksum': None,
                         'created_at': time1}

        db_api.image_create(self.context, extra_fixture)

        UUID4 = _gen_uuid()
        extra_fixture = {'id': UUID4,
                         'status': 'active',
                         'is_public': True,
                         'disk_format': 'vhd',
                         'container_format': 'ovf',
                         'name': 'new name! #123',
                         'size': 20,
                         'checksum': None,
                         'created_at': time2}

        db_api.image_create(self.context, extra_fixture)

        UUID5 = _gen_uuid()
        extra_fixture = {'id': UUID5,
                         'status': 'active',
                         'is_public': True,
                         'disk_format': 'vhd',
                         'container_format': 'ovf',
                         'name': 'new name! #123',
                         'size': 20,
                         'checksum': None,
                         'created_at': time3}

        db_api.image_create(self.context, extra_fixture)

        req = webob.Request.blank('/images?marker=%s' % UUID4)
        res = req.get_response(self.api)
        res_dict = json.loads(res.body)
        self.assertEquals(res.status_int, 200)

        images = res_dict['images']
        # should be sorted by created_at desc, id desc
        # page should start after marker 4
        self.assertEquals(len(images), 2)
        self.assertEquals(images[0]['id'], UUID5)
        self.assertEquals(images[1]['id'], UUID2)

    def test_get_index_unknown_marker(self):
        """
        Tests that the /images API returns a 400
        when an unknown marker is provided
        """
        req = webob.Request.blank('/images?marker=%s' % _gen_uuid())
        res = req.get_response(self.api)
        self.assertEquals(res.status_int, 400)

    def test_get_index_malformed_marker(self):
        """
        Tests that the /images API returns a 400
        when a malformed marker is provided
        """
        req = webob.Request.blank('/images?marker=4')
        res = req.get_response(self.api)
        self.assertEquals(res.status_int, 400)
        self.assertTrue('marker' in res.body)

    def test_get_index_limit(self):
        """
        Tests that the /images API returns list of
        public images that conforms to a limit query param
        """
        UUID3 = _gen_uuid()
        extra_fixture = {'id': UUID3,
                         'status': 'active',
                         'is_public': True,
                         'disk_format': 'vhd',
                         'container_format': 'ovf',
                         'name': 'new name! #123',
                         'size': 19,
                         'checksum': None}

        db_api.image_create(self.context, extra_fixture)

        UUID4 = _gen_uuid()
        extra_fixture = {'id': UUID4,
                         'status': 'active',
                         'is_public': True,
                         'disk_format': 'vhd',
                         'container_format': 'ovf',
                         'name': 'new name! #123',
                         'size': 20,
                         'checksum': None}

        db_api.image_create(self.context, extra_fixture)

        req = webob.Request.blank('/images?limit=1')
        res = req.get_response(self.api)
        res_dict = json.loads(res.body)
        self.assertEquals(res.status_int, 200)

        images = res_dict['images']
        self.assertEquals(len(images), 1)

        # expect list to be sorted by created_at desc
        self.assertTrue(images[0]['id'], UUID4)

    def test_get_index_limit_negative(self):
        """
        Tests that the /images API returns list of
        public images that conforms to a limit query param
        """
        req = webob.Request.blank('/images?limit=-1')
        res = req.get_response(self.api)
        self.assertEquals(res.status_int, 400)

    def test_get_index_limit_non_int(self):
        """
        Tests that the /images API returns list of
        public images that conforms to a limit query param
        """
        req = webob.Request.blank('/images?limit=a')
        res = req.get_response(self.api)
        self.assertEquals(res.status_int, 400)

    def test_get_index_limit_marker(self):
        """
        Tests that the /images API returns list of
        public images that conforms to limit and marker query params
        """
        UUID3 = _gen_uuid()
        extra_fixture = {'id': UUID3,
                         'status': 'active',
                         'is_public': True,
                         'disk_format': 'vhd',
                         'container_format': 'ovf',
                         'name': 'new name! #123',
                         'size': 19,
                         'checksum': None}

        db_api.image_create(self.context, extra_fixture)

        extra_fixture = {'id': _gen_uuid(),
                         'status': 'active',
                         'is_public': True,
                         'disk_format': 'vhd',
                         'container_format': 'ovf',
                         'name': 'new name! #123',
                         'size': 20,
                         'checksum': None}

        db_api.image_create(self.context, extra_fixture)

        req = webob.Request.blank('/images?marker=%s&limit=1' % UUID3)
        res = req.get_response(self.api)
        res_dict = json.loads(res.body)
        self.assertEquals(res.status_int, 200)

        images = res_dict['images']
        self.assertEquals(len(images), 1)

        # expect list to be sorted by created_at desc
        self.assertEqual(images[0]['id'], UUID2)
