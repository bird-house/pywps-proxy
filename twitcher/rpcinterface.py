import functools

from pyramid.view import view_config, view_defaults
from pyramid.exceptions import HTTPForbidden
from pyramid.authentication import BasicAuthAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid_rpc.xmlrpc import xmlrpc_method

from twitcher import registry, tokens

import logging
logger = logging.getLogger(__name__)


# shortcut for xmlrpc_method
api_xmlrpc = functools.partial(xmlrpc_method, endpoint="api")

# security
Admin = 'group.admin'

def groupfinder(username, password, request):
    if username == 'admin':
        return [Admin]
    else:
        return []
    return HTTPForbidden()


# Authentication and Authorization

from pyramid.security import (
        Allow,
        Everyone,
        ALL_PERMISSIONS)


class Root():
    __acl__ = [
        (Allow, Everyone, 'view'),
        (Allow, Admin, ALL_PERMISSIONS)
        ]

    def __init__(self, request):
        self.request = request

def root_factory(request):
    return Root(request)


@view_defaults(permission='admin')
class RPCInterface(object):
    def __init__(self, request):
        self.request = request

    # token management

    @api_xmlrpc()
    def generateToken(self):
        tokenstore = tokens.TokenStorage(self.request.db)
        access_token = tokenstore.create_access_token()
        return access_token.access_token


    # service registry

    @api_xmlrpc()
    def addService(self, url):
        service = registry.add_service(self.request, url=url)
        return service['name']


    @api_xmlrpc()
    def removeService(self, name):
        try:
            registry.remove_service(self.request, service_name=name)
        except:
            logger.exception('unregister failed')
            return False
        else:
            return True



    @api_xmlrpc()
    def listServices(self):
        try:
            services = registry.list_services(self.request)
            return services
        except:
            logger.exception('register failed')
            return []


    @api_xmlrpc()
    def clearServices(self):
        try:
            registry.clear_service(self.request)
        except:
            logger.exception('clear failed')
            return False
        else:
            return True

def includeme(config):
    """ The callable makes it possible to include rpcinterface
    in a Pyramid application.

    Calling ``config.include(twitcher.rpcinterface)`` will result in this
    callable being called.

    Arguments:

    * ``config``: the ``pyramid.config.Configurator`` object.
    """
    # pyramid xml-rpc
    # http://docs.pylonsproject.org/projects/pyramid-rpc/en/latest/xmlrpc.html
    config.include('pyramid_rpc.xmlrpc')
    config.include('twitcher.db')
    config.add_xmlrpc_endpoint('api', '/RPC2')

    # Security policies: basic auth
    authn_policy = BasicAuthAuthenticationPolicy(check=groupfinder, realm="Birdhouse")
    authz_policy = ACLAuthorizationPolicy()
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.set_root_factory(root_factory)
