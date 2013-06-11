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


from glance.db.storage.drivers.in_memory import image
from glance.db.storage.drivers.in_memory import image_member

DATA = {}


class Storage(object):
    """ "in memory" database implementation
    
    This db is used for testing purposes, and so does not persist and cannot
    be shared across processes. Nor are migrations supported.
    """
    def __init__(self, data=None):
        """ Create a new in memory storage database

        :param data: the dictionary used to back the storage database. If none
            is provided, a global dicionary will be used.
        """
        if data is None:
            data = DATA
        self.data = data
        self._prep_data()

    def _prep_data(self):
        if not 'images' in self.data:
            self.data['images'] = {}
        if not 'members' in self.data:
            self.data['members'] = []

    def get_image_repository(self):
        return image.Repository(self.data)

    def get_image_member_repository(self):
        return image_member.Repository(self.data)

    def get_migrator(self):
        message = _("In memory database does not support migrations.")
        raise NotImplementedError(message)
