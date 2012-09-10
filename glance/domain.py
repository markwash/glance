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
        del db_api_image['deleted']
        properties = {}
        for prop in db_api_image.pop('properties'):
            # db api requires us to filter deleted
            if not prop['deleted']:
                properties[prop['name']] = prop['value']
        properties.update(db_api_image)
        tags = set(self.db_api.image_tag_get_all(self.context, image_id))
        return Image(properties, tags)

class Image(object):
    
    def __init__(self, properties=None, tags=None):
        self.properties = properties or {}
        self.tags = tags or []
