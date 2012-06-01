# Copyright 2012 OpenStack LLC.
# All Rights Reserved.
#
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

import datetime
import json

import webob.exc

from glance.api.v2 import base
from glance.common import exception
from glance.common import utils
from glance.common import wsgi
import glance.registry.db.api


class ImagesController(base.Controller):
    def __init__(self, domain):
        super(ImagesController, self).__init__(conf)
        self.domain = domain

    def _populate_image(self, image, properties, tags):
        try:
            for key, value in properties.iteritems():
                image[key] = value # may raise 403
            image.tags = tags # may raise 403
        except exception.Forbidden, e:
            raise webob.exc.HTTPForbidden(e)

    def create(self, req, properties, tags):
        image = self.domain.new_image(req.context)
        self._populate_image(image, properties, tags)
        self.domain.get_image_repo(req.context).save(image)
        return image

    def index(self, req):
        return self.domain.get_image_repo(req.context).list()

    def show(self, req, image_id):
        return self.domain.get_image_repo(req.context).find(image_id)

    def update(self, req, image_id, properties, tags):
        repo = self.domain.get_image_repo(req.context)
        image = repo.find(image_id)
        self._populate_image(image, properties, tags)
        repo.save(image)
        return image

    def delete(self, req, image_id):
        self.domain.get_image_repo(req.context).remove(image_id)


class RequestDeserializer(wsgi.JSONRequestDeserializer):
    def __init__(self, conf, image_schema):
        super(RequestDeserializer, self).__init__()
        self.conf = conf
        self.image_schema = image_schema

    def _parse_image(self, request):
        output = super(RequestDeserializer, self).default(request)
        body = output.pop('body')
        self.image_schema.validate(body)
        properties = body
        tags = properties.pop('tags')
        return {'properties': properties, 'tags': tags}

    def create(self, request):
        return self._parse_image(request)

    def update(self, request):
        return self._parse_image(request)


class ResponseSerializer(wsgi.JSONResponseSerializer):
    """Converts internal domain model Images to dicts for json serialization,
    adding any http-appropriate links that are needed."""

    def __init__(self):
        super(ResponseSerializer, self).__init__()

    def _get_image_link(self, image, subcollection=None):
        link = '/v2/images/%s' % image['id']
        if subcollection is not None:
            link = '%s/%s' % (link, subcollection)
        return link

    def _format_image(self, image):
        image_dict = dict(image.iteritems())
        image_dict['tags'] = list(image.tags)
        image_dict['self'] = self._get_image_link(image)
        image_dict['access'] = self._get_image_link(image, 'access')
        image_dict['file'] = self._get_image_link(image, 'file')
        return image_dict

    def create(self, response, image):
        response.body = json.dumps({'image': self._format_image(image)})
        response.location = self._get_image_link(image)

    def show(self, response, image):
        response.body = json.dumps({'image': self._format_image(image)})

    def update(self, response, image):
        response.body = json.dumps({'image': self._format_image(image)})

    def index(self, response, images):
        body = {
            'images': [self._format_image(i) for i in images],
            'first': '',
            'next': '',
            'prev': '',
            'last': '', # obviously these need to be filled in or removed
        }
        response.body = json.dumps(body)

    def delete(self, response, result):
        response.status_int = 204


def create_resource(conf):
    """Images resource factory method"""
    image_schema = glance.api.v2.schemas.Image(conf)
    domain = glance.api.v2.domain.create_domain(conf)
    deserializer = RequestDeserializer(image_schema)
    serializer = ResponseSerializer()
    controller = ImagesController(domain)
    return wsgi.Resource(controller, deserializer, serializer)
