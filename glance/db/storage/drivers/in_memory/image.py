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

import copy

from glance.db.storage import spec


class Repository(object):
    def __init__(self, data):
        self.data = data

    def query(self):
        return Query(self.data, _HasMemberSpecTranslator())

    def insert(self, image):
        if image['id'] in self.data['images']:
            raise KeyError()
        self.data['images'][image['id']] = copy.deepcopy(image)


class Query(object):
    def __init__(self, data, spec_translator, specification=None):
        self.data = data
        self.spec_translator = spec_translator
        self.spec = specification

    def filter(self, specification):
        if self.spec is not None:
            specification = spec.And(self.spec, specification)
        return Query(self.data, specification)

    def _matching_images(self):
        translated_spec = self.spec_translator.translate(self.spec)
        for image_id, image in self.data['images'].iteritems():
            if translated_spec.match(image):
                yield image_id, image

    def fetch(self):
        results = []
        for image_id, image in self._matching_images():
            results.append(copy.deepcopy(image))
        return results

    def delete(self):
        to_delete = [image_id for image_id, image in self._matching_images()]
        for image_id in to_delete:
            del self.data['images'][image_id]
        return len(to_delete)

    def update(self, image_update):
        count = 0
        for image_id, image in self._matching_images():
            image.update(image_update)
            count += 1
        return count


class _HasMemberSpecTranslator(object):
    def translate(self, specification):
        return spec.visit(self)

    def visit_and(self, and_spec):
        return 
