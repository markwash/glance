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


class StorageMigrator(object):
    """
    An interface for managing the version of the schema of a given database.

    This interface takes the schema-driven view of RDBMS, suggesting that a
    schema migration takes place across all affected objects at once, rather
    than proceeding one object at a time (as one might in a schema-less
    implementation). It is, of course, possible to adapt a per-object approach
    as the implementation of this interface.
    """
    def get_version(self):
        """
        Return the current version of the storage system.

        :returns a storage version identifier string
        """
        pass

    def force_set_version(self, version):
        """
        Mark the version of the storage system.

        Note, this method does not perform any actual migrations. It is
        primarily useful to recover from errors, or for initially setting
        up a database.
        """
        pass

    def migrate(self, from_version=None, to_version=None):
        """
        Run each migration required to get from one version to another.

        This method can be used both for upgrades and downgrades.

        :param from_version: the starting point for migrations, default is to
          use the current version as inspected from the database
        :param to_version: the end point for migrations, default is to use the
          most recent version that exists
        """
        pass

    def list_versions(self):
        """
        List all known versions.
        :returns a list of version identifier strings in order from earliest
          version to latest version
        """
        pass
