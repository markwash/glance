# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack, LLC
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

import os.path
import shutil
import tempfile

import stubout

from glance.common import config
from glance.common import context
from glance.image_cache import pruner
from glance.openstack.common import cfg
from glance.tests import utils as test_utils


class TestPasteApp(test_utils.BaseTestCase):

    def setUp(self):
        super(TestPasteApp, self).setUp()
        self.stubs = stubout.StubOutForTesting()

    def tearDown(self):
        super(TestPasteApp, self).tearDown()
        self.stubs.UnsetAll()

    def _do_test_load_paste_app(self,
                                expected_app_type,
                                paste_flavor=None,
                                paste_config_file=None,
                                paste_append=None):

        def _writeto(path, str):
            with open(path, 'wb') as f:
                f.write(str or '')
                f.flush()

        def _appendto(orig, copy, str):
            shutil.copy(orig, copy)
            with open(copy, 'ab') as f:
                f.write(str or '')
                f.flush()

        self.config(flavor=paste_flavor,
                    config_file=paste_config_file,
                    group='paste_deploy')

        temp_file = os.path.join(tempfile.mkdtemp(), 'testcfg.conf')

        try:
            _writeto(temp_file, '[DEFAULT]\n')

            config.parse_args(['--config-file', temp_file])

            paste_to = temp_file.replace('.conf', '-paste.ini')
            if not paste_config_file:
                paste_from = os.path.join(os.getcwd(),
                                          'etc/glance-registry-paste.ini')
                _appendto(paste_from, paste_to, paste_append)

            app = config.load_paste_app('glance-registry')

            self.assertEquals(expected_app_type, type(app))
        finally:
            shutil.rmtree(os.path.dirname(temp_file))

    def test_load_paste_app(self):
        expected_middleware = context.UnauthenticatedContextMiddleware
        self._do_test_load_paste_app(expected_middleware)

    def test_load_paste_app_with_paste_flavor(self):
        pipeline = ('[pipeline:glance-registry-incomplete]\n'
                    'pipeline = context registryapp')
        expected_middleware = context.ContextMiddleware
        self._do_test_load_paste_app(expected_middleware,
                                     paste_flavor='incomplete',
                                     paste_append=pipeline)

    def test_load_paste_app_with_paste_config_file(self):
        paste_config_file = os.path.join(os.getcwd(),
                                         'etc/glance-registry-paste.ini')
        expected_middleware = context.UnauthenticatedContextMiddleware
        self._do_test_load_paste_app(expected_middleware,
                                     paste_config_file=paste_config_file)

    def test_load_paste_app_with_conf_name(self):
        def fake_join(*args):
            if (len(args) == 2 and
                args[0].endswith('.glance') and
                args[1] == 'glance-cache.conf'):
                return os.path.join(os.getcwd(), 'etc', args[1])
            else:
                return orig_join(*args)

        orig_join = os.path.join
        self.stubs.Set(os.path, 'join', fake_join)

        config.parse_cache_args([])

        self.stubs.Set(config, 'setup_logging', lambda *a: None)
        self.stubs.Set(pruner, 'Pruner', lambda conf, **lc: 'pruner')

        app = config.load_paste_app('glance-pruner')

        self.assertEquals('pruner', app)
