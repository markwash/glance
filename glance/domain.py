class AuthDomain(object):

    def __init__(self, db_api=None):
        self.db_api = db_api or glance.db.get_api()
        self.db_api.configure_db()
    
    def get_image_repo(self, context):
        return ImageRepo(context, self.db_api)

class ImageRepo(object):

    def __init__(self, context, db_api=None):
        self.context = context
        self.db_api = db_api or glance.db.get_api()
        self.db_api.configure_db()

    def find(self, image_id):
        db_api_image = dict(self.db_api.image_get(self.context, image_id))
        if db_api_image['is_public']:
            visibility = 'public'
        else:
            visibility = 'private'
        properties = {}
        for prop in db_api_image.pop('properties'):
            # db api requires us to filter deleted
            if not prop['deleted']:
                properties[prop['name']] = prop['value']
        tags = self.db_api.image_tag_get_all(self.context, image_id)
        return Image(
            image_id=db_api_image['id'],
            name=db_api_image['name'],
            status=db_api_image['status'],
            created_at=db_api_image['created_at'],
            updated_at=db_api_image['updated_at'],
            visibility=visibility,
            min_disk=db_api_image['min_disk'],
            min_ram=db_api_image['min_ram'],
            protected=db_api_image['protected'],
            location=db_api_image['location'],
            checksum=db_api_image['checksum'],
            owner=db_api_image['owner'],
            disk_format=db_api_image['disk_format'],
            container_format=db_api_image['container_format'],
            size=db_api_image['size'],
            extra_properties=properties,
            tags=tags
        )


class Image(object):
    
    def __init__(self, image_id, name, status, created_at, updated_at,
                 visibility='private', min_disk=0, min_ram=0, protected=False,
                 location=None, checksum=None, owner=None, disk_format=None,
                 container_format=None, size=None,
                 extra_properties=None, tags=None):
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
        self.tags = set(tags)
