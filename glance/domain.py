import glance.common.utils
from glance.common import exception
from glance.openstack.common import timeutils

#CONF = cfg.CONF

#class AuthDomain(object):
#
#    def __init__(self, db_api=None):
#        self.db_api = db_api or glance.db.get_api()
#        self.db_api.configure_db()
#
#    def get_image_repo(self, context):
#        return ImageRepo(context, self.db_api)
#
class ImageRepoInterface(object):

    def find(self, image_id):
        pass

    def find_many(self, marker, limit, filters):
        pass

    def save(self, image):
        pass

    def remove(self, image_id):
        pass


class ImageFactoryInterface(object):

    def new_image(self, extra_properties, tags, **kwargs):
        pass

class ImageFactory(object):
    _readonly_properties = ['created_at', 'updated_at', 'status', 'checksum',
            'size']
    _reserved_properties = ['owner', 'is_public', 'location',
            'deleted', 'deleted_at', 'direct_url', 'self', 'file', 'schema']

    def __init__(self, context):
        self.context = context

    def _check_readonly(self, kwargs):
        for key in self._readonly_properties:
            if key in kwargs:
                raise exception.ReadonlyProperty(property=key)

    def _check_unexpected(self, kwargs):
        if len(kwargs) > 0:
            msg = 'new_image() got unexpected keywords %s'
            raise TypeError(msg % kwargs.keys())

    def _check_reserved(self, properties):
        for key in self._reserved_properties:
            if key in properties:
                raise exception.ReservedProperty(property=key)

    def new_image(self, image_id=None, name=None, visibility='private',
                  min_disk=0, min_ram=0, protected=False, owner=None,
                 disk_format=None, container_format=None,
                 extra_properties=None, tags=None, **other_args):
        self._check_readonly(other_args)
        self._check_unexpected(other_args)
        self._check_reserved(extra_properties)

        if image_id is None:
            image_id = glance.common.utils.generate_uuid()
        created_at = timeutils.utcnow()
        updated_at = created_at
        status = 'queued'
        owner = self.context.owner

        return Image(image_id=image_id, name=name, status=status,
                     created_at=created_at, updated_at=updated_at,
                     visibility=visibility, min_disk=min_disk,
                     min_ram=min_ram, protected=protected,
                     owner=owner, disk_format=disk_format,
                     container_format=container_format,
                     extra_properties=extra_properties, tags=tags)

class Image(object):

    def __init__(self, image_id, status, created_at, updated_at, name=None,
                 visibility='private', min_disk=0, min_ram=0, protected=False,
                 location=None, checksum=None, owner=None, disk_format=None,
                 container_format=None, size=None,
                 extra_properties=None, tags=None):
        if visibility not in ('public', 'private'):
            raise ValueError('Visibility must be either "public" or "private"')
        self.image_id = image_id
        self.name = name
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self.visibility = visibility
        self.min_disk = min_disk
        self.min_ram = min_ram
        self.protected = protected
        self.location = location
        self.checksum = checksum
        self.owner = owner
        self.disk_format = disk_format
        self.container_format = container_format
        self.size = size
        self.extra_properties = extra_properties or {}
        if tags is None:
            tags = []
        self.tags = tags

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, value):
        self._tags = set(value)

    def delete(self):
        if self.protected:
            raise exception.ProtectedImageDelete(image_id=self.image_id)
        self.status = 'deleted'
