from glance.api import policy
import glance.db
import glance.domain
import glance.store

class Gateway(object):
    def __init__(self, db_api=None, store_api=None, policy_enforcer=None):
        self.db_api = db_api or glance.db.get_api()
        self.db_api.configure_db()
        self.store_api = store_api or glance.store
        self.policy = policy_enforcer or policy.Enforcer()

    def get_builder(self, context):
        image_builder = glance.domain.ImageBuilder(context)
        policy_image_builder = policy.ImageBuilderDecorator(
                image_builder, context, self.policy)
        return policy_image_builder

    def get_repo(self, context):
        image_repo = glance.db.ImageRepo(context, self.db_api)
        store_image_repo = glance.store.ImageRepoDecorator(
                context, self.store_api, image_repo)
        policy_image_repo = policy.ImageRepoDecorator(
                context, self.policy, store_image_repo)
        return policy_image_repo

