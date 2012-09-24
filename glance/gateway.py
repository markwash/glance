import glance.db
import glance.store

class ImageRepoFactory(object):
    def __init__(self, db_api=None, store_api=None):
        self.db_api = db_api or glance.db.get_api()
        self.db_api.configure_db()
        self.store_api = store_api or glance.store

    def get_repo(self, context):
        image_repo = glance.db.ImageRepo(context, self.db_api)
        return glance.store.ImageRepoDecorator(context, self.store_api,
                                               image_repo)
