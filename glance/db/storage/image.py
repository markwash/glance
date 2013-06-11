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


class Repository(object):
    """
    An abstraction for storing and retreiving images.
    """
    def query(self):
        """
        Initiate a query against the repository.

        :returns an object that satisfies the `Query` interface
        """
        pass

    def insert(self, image):
        """
        Add an image to the repository.

        :param image: the image to add, in the form of a dictionary
        """
        pass


class Query(object):
    """
    An abstraction for efficiently querying images from a repository.
    """
    def filter(self, specification):
        """
        Return a form of this query that is restricted to images that satisfy
        the given image specification.

        :param specification: an image specification
        :returns an object that satisfies the `Query` interface
        """
        pass

    def fetch(self):
        """
        Return all images that match this query.
        
        :returns a list of images, where each image takes the form of a dict
        """
        pass

    def delete(self):
        """
        Remove all images that match this query from the underlying repository

        :returns how many images were deleted
        """
        pass

    def update(self, image_update):
        """
        Update all images that match this query with the given values.

        :param image_update: a dictionary of updates
        :returns how many images were updated
        """
        pass


class AttrSpec(object):
    """ Specifies a condition on an image attribute

    Examples: 
        AttrSpec('is_public', IsTrue())
        - would match public images
        AttrSpec('created_by', GreaterThan(yesterday))
        - would match images created more recently than yesterday
    """
    def __init__(self, attr, value_spec):
        self.attr = attr
        self.value_spec = value_spec

    def match(self, image):
        return self.value_spec.match(image.get(self.attr))


class PropSpec(object):
    """ Specifies a condition on an image property

    Examples:
        PropSpec('instance_type_ram', Not(GreaterThan(512)))
         - would match images that have the instance_type_ram property
           with a value less than or equal to 512 (MB)
    """
    def __init__(self, prop, value_spec):
        self.prop = prop
        self.value_spec = value_spec

    def match(self, image):
        return self.value_spec.match(image['extra_properties'].get(self.prop))


class ContainsTagsSpec(object):
    """ Specifies images that contain the given tags. """
    def __init__(self, tags):
        self.tags = tags

    def match(self, image):
        for tag in self.tags:
            if tag not in image['tags']:
                return False
        return True


class HasMemberSpec(object):
    """ Specifies images where the given tenant is a member """
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id

    def match(self, image):
        """ No generic way to do this one. """
        raise NotImplementedError
