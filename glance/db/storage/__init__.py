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


class Storage(object):
    """
    High level abstraction for a given database implementation.

    This is the interface for a factory for all the "real" objects that one
    can use to interact with a storage system. Since it is just an interface
    description, there is no good reason to inherit from it.
    """
    def get_image_repository(self):
        """
        :returns an object satisfying the `glance.db.storage.image.Repository`
          interface
        """
        pass

    def get_image_member_repository(self):
        """
        :returns an object satisfying the
          `glance.db.storage.image_member.Repository` interface
        """
        pass

    def get_migrator(self):
        """
        :returns an object satisfying the
          `glance.db.storage.migration.StorageMigrator` interface
        """
        pass
