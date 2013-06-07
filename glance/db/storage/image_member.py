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
    An abstraction for storing and retreiving image membership records.
    """
    def query(self):
        """
        Initiate a query against the repository.

        :returns an object that satisfies the `Query` interface
        """
        pass

    def insert(self, image_member):
        """
        Add an image to the repository.

        :param image_member: the image membership record to add, in the form 
          of a dictionary
        """
        pass


class Query(object):
    """
    An abstraction for efficiently querying image membership from a repository.
    """
    def filter(self, specification):
        """
        Return a form of this query that is restricted to image membership 
        records that satisfy the given member specification.

        :param specification: an image membership record specification
        :returns an object that satisfies the `Query` interface
        """
        pass

    def fetch(self):
        """
        Return all image membership records that match this query.
        
        :returns a list of images, where each image takes the form of a dict
        """
        pass

    def delete(self):
        """
        Remove all image membership records that match this query from the
        underlying repository
        """
        pass

    def update(self, member_update):
        """
        Update all image membership records that match this query with the
        given values.

        :param member_update: a dictionary of updates
        """
        pass
