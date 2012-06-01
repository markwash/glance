""" This is just a scratch file where I've been cobbling together ideas
in a loosely-cohesive group. If we go with this method, I'm fairly certain
that most of these classes would end up in separate modules or even
packages elsewhere in the glance code base. Some classes are just stubs
where every method is just "pass", some are probably close to functional"""


class Domain(object):
    """A domain is the central dependency injection point. This is the
    place where the consistency of data layer and authorization choices
    is guaranteed. I suspect a better name for this class could be found."""

    def get_image_repo(self, context):
        """Create an image repo appropriate for this context. I.e., its
        going to be appropriately restricted to the particular tenant
        and with the appropriate create, update, and read restrictions
        for any image objects it yields up."""
        pass

    def new_image(self, context):
        """Return a new empty image (well okay maybe id is set) with 
        appropriate create restrictions (since we know this image won't
        already be in any repos, anything we do with it is create-oriented)"""
        pass

    def get_image_member_repo(self, context, image):
        """A appropriately restricted view of the members of a given image"""
        pass

    def get_image_tag_repo(self, context, image):
        """An appropriately restricted view of the tags of an image"""
        pass


class ImageRepo(object):
    """Performs the mapping between the database representation
    and the image domain model object, while presenting a roughly
    collection-like interface.
    
    This repo inherits some authz restrictions from the relationship
    that is hard-coded between context and dbapi. To me that's not ideal
    but we'll just work with it for now."""

    def __init__(self, context, dbapi):
        # really shouldn't need context here
        # and dbapi should be something much simpler
        # but here we'll work with what we have
        self.context = context
        self.dbapi = dbapi

    def find(self, image_id):
        raw_image = self.dbapi.image_get(self.context, image_id)
        tags = self.dbapi.image_tags_get_all(self.context, image_id)
        return Image(properties=raw_image, tags=tags)

    def save(self, image):
        self.dbapi.image_update(self.context, image['id'], dict(image))
        self.dbapi.image_tag_set_all(self.context, image['id'], image.tags)

    def remove(self, image_id):
        pass # ...


class RestrictedImageRepo(object):
    """Wraps an existing image repo with authz restrictions"""

    def __init__(self, context, image_repo, property_config):
        self.context = context
        self.image_repo = image_repo
        self.property_conf = property_conf

    def find(self, image_id):
        property_restrictions = self.some_magic(...)
        tag_restrictions = self.some_other_magic(...)
        image = self.image_repo.find(image_id)
        return RestrictedImage(image, property_restrictions, tag_restrictions)

    def save(self, image):
        """If the base image repo were more wide-open in terms of permissions
        as I'd prefer, then this function would need some checks in it. As
        things are, we can just roll."""
        self.image_repo.save(image)

    def delete(self, image_id):
        """ Ditto """
        self.image_repo.delete(image_id)


class Image(dict):

    def __init__(self, properties, tags):
        super(Image, self).__init__(properties)
        self.tags = tags

    @property
    def tags(self):
        return self._tags

    # Tags has to be a set
    @tags.setter
    def tags(self, values):
        self._tags = set(values)


# Below are some example restrictions classes that might be used
# by the domain or image repo to ensure only the allowed types
# of access are done to images.

class NoRestrictions(object):

    def can_read(self, attribute):
        return True

    def can_write(self, attribute):
        return True


class ReadonlyRestriction(object):

    def can_read(self, attribute):
        return True

    def can_write(self, attribute):
        return False


class SimpleRestrictions(object):

    def __init__(self, read_permits=None, write_permits=None):
        if read_permits is None:
            read_permits = []
        self.read_permits = read_permits
        if write_permits is None:
            write_permits = []
        self.write_permits = []

    def can_read(self, attribute):
        return attribute in self.read_permits

    def can_write(self, attribute):
        return attribute in self.write_permits


class RestrictedImage(object):

    def __init__(self, image, property_restrictions=None,
                 tag_restrictions=None):
        self._image = image
        if property_restrictions is None:
            property_restrictions = NoRestrictions()
        self._property_restrictions = property_restrictions
        tag_restrictions = NoRestrictions()
        self._tags = RestrictedTags(self.image.tags, tag_restrictions)

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, values):
        self._tags._set_all_tags(values)

    def __setitem__(self, key, value):
        if not self.property_restrictions.can_write(key):
            raise exception.Forbidden()
        self.image[key] = value

    def __getitem__(self, key):
        if not self.property_restrictions.can_read(key):
            raise exception.Forbidden()
        return self.image[key]

    def __delitem__(self, key):
        if not self.property_restrictions.can_write(key):
            raise exception.Forbidden()
        del self.image[key]

    def iterkeys(self):
        for key in self.image.iterkeys():
            if self.property_restrictions.can_read(key):
                yield key

    def itervalues(self):
        for key, value in self.image.iteritems():
            if self.property_restrictions.can_read(key):
                yield value

    def iteritems(self):
        for key, value in self.image.iteritems():
            if self.property_restrictions.can_read(key):
                yield key, value

    def keys(self):
        return [self.iterkeys()]

    def values(self):
        return [self.itervalues()]

    def items(self):
        return [self.iteritems()]

    def __len__(self):
        raise NotImplemented  # shouldn't need this, should we?


class RestrictedTags(object):

    def __init__(self, tags, restrictions):
        self.tags = tags
        self.restrictions = restrictions

    def __iter__(self):
        for tag in self.tags:
            if self.restrictions.can_read(tag):
                yield tag
    
    def _set_all(self, tags):
        for tag in tags:
            if not self.restrictions.can_write(tag):
                raise exception.Forbidden()
        self.tags = tags

    # lots more needed to retain set-like behavior

