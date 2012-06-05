# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010-2011 OpenStack, LLC
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

import logging
import os
import sys
import time

from glance.common import exception
from glance.common import utils
from glance.openstack.common import cfg
from glance.openstack.common import importutils
from glance import registry
from glance.store import location

logger = logging.getLogger('glance.store')

store_opts = [
    cfg.ListOpt('known_stores',
                default=['glance.store.filesystem.Store', ]),
    cfg.StrOpt('scrubber_datadir',
               default='/var/lib/glance/scrubber'),
    cfg.BoolOpt('delayed_delete', default=False),
    cfg.IntOpt('scrub_time', default=0),
    ]

CONF = cfg.CONF
CONF.register_opts(store_opts)

# Set of store objects, constructed in create_stores()
STORES = {}


class ImageAddResult(object):

    """
    Class that represents the succesful result of adding
    an image to a backend store.
    """

    def __init__(self, location, bytes_written, checksum=None):
        """
        Initialize the object

        :param location: `glance.store.StoreLocation` object representing
                         the location of the image in the backend store
        :param bytes_written: Number of bytes written to store
        :param checksum: Optional checksum of the image data
        """
        self.location = location
        self.bytes_written = bytes_written
        self.checksum = checksum


class BackendException(Exception):
    pass


class UnsupportedBackend(BackendException):
    pass


class Indexable(object):

    """
    Wrapper that allows an iterator or filelike be treated as an indexable
    data structure. This is required in the case where the return value from
    Store.get() is passed to Store.add() when adding a Copy-From image to a
    Store where the client library relies on eventlet GreenSockets, in which
    case the data to be written is indexed over.
    """

    def __init__(self, wrapped, size):
        """
        Initialize the object

        :param wrappped: the wrapped iterator or filelike.
        :param size: the size of data available
        """
        self.wrapped = wrapped
        self.size = int(size) if size else (wrapped.len
                                            if hasattr(wrapped, 'len') else 0)
        self.cursor = 0
        self.chunk = None

    def __iter__(self):
        """
        Delegate iteration to the wrapped instance.
        """
        for self.chunk in self.wrapped:
            yield self.chunk

    def __getitem__(self, i):
        """
        Index into the next chunk (or previous chunk in the case where
        the last data returned was not fully consumed).

        :param i: a slice-to-the-end
        """
        start = i.start if isinstance(i, slice) else i
        if start < self.cursor:
            return self.chunk[(start - self.cursor):]

        self.chunk = self.another()
        if self.chunk:
            self.cursor += len(self.chunk)

        return self.chunk

    def another(self):
        """Implemented by subclasses to return the next element"""
        raise NotImplementedError

    def getvalue(self):
        """
        Return entire string value... used in testing
        """
        return self.wrapped.getvalue()

    def __len__(self):
        """
        Length accessor.
        """
        return self.size


def _get_store_class(store_entry):
    store_cls = None
    try:
        logger.debug("Attempting to import store %s", store_entry)
        store_cls = importutils.import_class(store_entry)
    except exception.NotFound:
        raise BackendException('Unable to load store. '
                               'Could not find a class named %s.'
                               % store_entry)
    return store_cls


def create_stores():
    """
    Registers all store modules and all schemes
    from the given config. Duplicates are not re-registered.
    """
    store_count = 0
    for store_entry in CONF.known_stores:
        store_entry = store_entry.strip()
        if not store_entry:
            continue
        store_cls = _get_store_class(store_entry)
        store_instance = store_cls()
        schemes = store_instance.get_schemes()
        if not schemes:
            raise BackendException('Unable to register store %s. '
                                   'No schemes associated with it.'
                                   % store_cls)
        else:
            if store_cls not in STORES:
                logger.debug("Registering store %s with schemes %s",
                         store_cls, schemes)
                STORES[store_cls] = store_instance
                scheme_map = {}
                for scheme in schemes:
                    loc_cls = store_instance.get_store_location_class()
                    scheme_map[scheme] = {
                        'store_class': store_cls,
                        'location_class': loc_cls,
                    }
                location.register_scheme_map(scheme_map)
                store_count += 1
            else:
                logger.debug("Store %s already registered", store_cls)
    return store_count


def get_store_from_scheme(scheme):
    """
    Given a scheme, return the appropriate store object
    for handling that scheme.
    """
    if scheme not in location.SCHEME_TO_CLS_MAP:
        raise exception.UnknownScheme(scheme=scheme)
    scheme_info = location.SCHEME_TO_CLS_MAP[scheme]
    return STORES[scheme_info['store_class']]


def get_store_from_uri(uri):
    """
    Given a URI, return the store object that would handle
    operations on the URI.

    :param uri: URI to analyze
    """
    scheme = uri[0:uri.find('/') - 1]
    return get_store_from_scheme(scheme)


def get_from_backend(uri, **kwargs):
    """Yields chunks of data from backend specified by uri"""

    store = get_store_from_uri(uri)
    loc = location.get_location_from_uri(uri)

    return store.get(loc)


def get_size_from_backend(uri):
    """Retrieves image size from backend specified by uri"""

    store = get_store_from_uri(uri)
    loc = location.get_location_from_uri(uri)

    return store.get_size(loc)


def delete_from_backend(uri, **kwargs):
    """Removes chunks of data from backend specified by uri"""
    store = get_store_from_uri(uri)
    loc = location.get_location_from_uri(uri)

    try:
        return store.delete(loc)
    except NotImplementedError:
        raise exception.StoreDeleteNotSupported


def get_store_from_location(uri):
    """
    Given a location (assumed to be a URL), attempt to determine
    the store from the location.  We use here a simple guess that
    the scheme of the parsed URL is the store...

    :param uri: Location to check for the store
    """
    loc = location.get_location_from_uri(uri)
    return loc.store_name


def schedule_delete_from_backend(uri, context, image_id, **kwargs):
    """
    Given a uri and a time, schedule the deletion of an image.
    """
    if not CONF.delayed_delete:
        registry.update_image_metadata(context, image_id,
                                       {'status': 'deleted'})
        try:
            return delete_from_backend(uri, **kwargs)
        except (UnsupportedBackend,
                exception.StoreDeleteNotSupported,
                exception.NotFound):
            exc_type = sys.exc_info()[0].__name__
            msg = (_("Failed to delete image at %s from store (%s)") %
                   (uri, exc_type))
            logger.error(msg)
        finally:
            # avoid falling through to the delayed deletion logic
            return

    datadir = CONF.scrubber_datadir
    delete_time = time.time() + CONF.scrub_time
    file_path = os.path.join(datadir, str(image_id))
    utils.safe_mkdirs(datadir)

    if os.path.exists(file_path):
        msg = _("Image id %(image_id)s already queued for delete") % {
                'image_id': image_id}
        raise exception.Duplicate(msg)

    with open(file_path, 'w') as f:
        f.write('\n'.join([uri, str(int(delete_time))]))
    os.chmod(file_path, 0600)
    os.utime(file_path, (delete_time, delete_time))

    registry.update_image_metadata(context, image_id,
                                   {'status': 'pending_delete'})


def add_to_backend(scheme, image_id, data, size):
    store = get_store_from_scheme(scheme)
    return store.add(image_id, data, size)
