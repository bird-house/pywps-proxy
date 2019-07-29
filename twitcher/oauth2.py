# coding: utf-8
"""
twitcher.oauth2
---------------

This module implements the `OAuth2 <https://oauthlib.readthedocs.io/en/latest/oauth2/oauth2.html>`_
model to generate access tokens.
These tokens are used to access the compute services (*scope=compute*)
and the OWS registration service (*scope=register*).
The compute services are accessed via the OWS proxy.
The OWS registration service is used to register OWS services behind the proxy.

The implementation is using the OAuth2
`client credentials <https://oauthlib.readthedocs.io/en/latest/oauth2/grants/credentials.html>`_
grant type

Currently three types of access tokens can be used:

*random_token*
    The access token is a UUID string.
    The tokens are stored in a local database and can be used for local validation only.

*signed_token*
    A JWT token signed with a X.509 certificate.
    The token can be validated without contacting a validation service.

*custom_token*
    A JWT token with a secret (UUID string) which can be shared for validation.
    The token can be validated without contacting a validation service.

See also the OAuth2
`token documenation <https://oauthlib.readthedocs.io/en/latest/oauth2/tokens/tokens.html>`_

The implementation is using the `pyramid-oauthlib <https://github.com/tilgovi/pyramid-oauthlib/>`_ library.
The code is also inspired by the following OAuth libraries:

* https://github.com/thomsonreuters/bottle-oauthlib
* https://github.com/lepture/flask-oauthlib

Further reading:

* https://oauthlib.readthedocs.io/en/latest/index.html
* https://pypi.org/project/PyJWT/
* https://requests-oauthlib.readthedocs.io/en/latest/index.html
* https://www.slideshare.net/alvarosanchezmariscal/stateless-authentication-with-oauth-2-and-jwt-javazone-2015
* https://docs.apigee.com/api-platform/security/oauth/oauth-20-client-credentials-grant-type
"""

import datetime
import uuid

from oauthlib.oauth2 import RequestValidator
from oauthlib.oauth2.rfc6749 import tokens
import jwt

from pyramid.settings import asbool

from twitcher import models
from twitcher.utils import get_settings

import logging
LOGGER = logging.getLogger('TWITCHER')


TOKEN_ENDPOINT = '/oauth/token'
CLIENT_APP_ENDPOINT = '/oauth/client'


class Client():
    client_id = None


class BaseValidator(RequestValidator):
    # default_scopes = ["compute", "register"]
    default_grants = ["client_credentials"]

    def _get_client(self, request, client_id):
        query = request.dbsession.query(models.Client)
        client = query.filter(models.Client.client_id == client_id).first()
        return client

    def get_default_scopes(self, client_id, request, *args, **kwargs):
        LOGGER.debug('get_default_scopes: client_id={}'.format(client_id))
        client = self._get_client(request, request.client_id)
        if client:
            return client.default_scopes
        else:
            return []

    def authenticate_client(self, request, *args, **kwargs):
        LOGGER.debug('authenticate_client: {}'.format(request.client_id))
        client = self._get_client(request, request.client_id)
        if not client:
            return False
        request.client = Client()
        request.client.client_id = request.client_id
        request.user = request.client_id
        if request.client_secret == client.client_secret:
            return True
        return False

    def validate_grant_type(self, client_id, grant_type, client, request, *args, **kwargs):
        return grant_type in self.default_grants

    def validate_scopes(self, client_id, scopes, client, request, *args, **kwargs):
        LOGGER.debug('validate_scopes: client_id={}, scopes={}'.format(
            client_id, scopes))
        _client = self._get_client(request, client_id)
        if not _client:
            return False
        return all(scope in _client.default_scopes for scope in scopes)

    def save_bearer_token(self, token_response, request, *args, **kwargs):
        pass


class RandomTokenValidator(BaseValidator):
    def save_bearer_token(self, token_response, request, *args, **kwargs):
        """Persist the Bearer token."""
        token = models.Token(client_id=request.client_id, **token_response)
        request.dbsession.add(token)

    def generate_access_token(self, request):
        return tokens.random_token_generator(request)

    def validate_bearer_token(self, token, scopes, request):
        """Validate access token.

        :param token: A string of random characters
        :param scopes: A list of scopes
        :param request: The Request object passed by oauthlib

        The validation validates:

            1) if the token is available
            2) if the token has expired
            3) if the scopes are available
        """
        query = request.dbsession.query(models.Token)
        tok = query.filter(models.Token.access_token == token).first()
        if not tok:
            return False
        # validate expires
        if tok.expires is not None and \
                datetime.datetime.utcnow() > tok.expires:
            return False
        # validate scopes
        if scopes and not set(tok.scopes) & set(scopes):
            return False
        return True


class SignedTokenValidator(BaseValidator):
    def __init__(self, cert, key, issuer):
        self.cert = cert
        self.key = key
        self.issuer = issuer

    def generate_access_token(self, request):
        private_pem_key = open(self.key, "br").read()
        return tokens.signed_token_generator(private_pem_key, issuer=self.issuer)(request)

    def validate_bearer_token(self, token, scopes, request):
        public_pem = open(self.cert, "br").read()
        return tokens.common.verify_signed_token(public_pem, token)


class CustomTokenValidator(BaseValidator):
    def __init__(self, secret, issuer):
        self.secret = secret
        self.issuer = issuer

    def generate_access_token(self, request):
        token = jwt.encode({
            "ref": str(uuid.uuid4()),
            # "aud": request.client_id,
            "iss": self.issuer,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=request.expires_in)
        }, self.secret, algorithm='HS256').decode()
        return token

    def validate_bearer_token(self, token, scopes, request):
        try:
            jwt.decode(token, self.secret, verify=True, algorithms=['HS256'])
        except Exception:
            return False
        else:
            return True


def generate_token_view(request):
    """Core functionality is available directly from the request.

    Responses from OAuthLib are wrapped in a response object of type
    :class:`pyramid.response.Response` so they can be returned directly
    from views.
    """
    # Extra credentials we need in the validator
    # credentials = {'user': request.user}
    LOGGER.debug('generate_token_view: client_id={}, client_secret={}'.format(
        request.client_id, request.client_secret))
    return request.create_token_response(credentials=None)


def register_client_app_view(request):
    """
    Register a new client application and returns ``client_id`` and ``client_secret``.

    Uses basic authentication.
    """
    client = models.Client(
        name=request.params.get('name'),
        client_id=uuid.uuid4().hex,
        client_secret=uuid.uuid4().hex,
        _redirect_uris=request.params.get('redirect_uri'),
        default_scope='compute register')
    request.dbsession.add(client)
    return dict(
        name=client.name,
        client_id=client.client_id,
        client_secret=client.client_secret,
        redirect_uri=client.default_redirect_uri,
        scope=client.default_scopes)


def includeme(config):
    settings = get_settings(config)
    if asbool(settings.get('twitcher.oauth', True)):
        config.include('pyramid_oauthlib')
        # using basic auth for client app registration
        config.include('twitcher.basicauth')

        # Validator callback functions are passed Pyramid request objects so
        # you can access your request properties, database sessions, etc.
        # The request object is populated with accessors for the properties
        # referred to in the OAuthLib docs and used by its built in types.
        token_type = settings.get('twitcher.token.type', 'random_token')
        if token_type == 'random_token':
            validator = RandomTokenValidator()
        elif token_type == 'signed_token':
            validator = SignedTokenValidator(
                cert=settings.get('twitcher.token.certfile'),
                key=settings.get('twitcher.token.keyfile'),
                issuer=settings.get('twitcher.token.issuer'))
        elif token_type == 'custom_token':
            validator = CustomTokenValidator(
                secret=settings.get('twitcher.token.secret'),
                issuer=settings.get('twitcher.token.issuer'))
        else:  # default
            validator = RandomTokenValidator()

        # Register grant types to validate token requests.
        config.add_grant_type('oauthlib.oauth2.ClientCredentialsGrant',
                              request_validator=validator)

        # Register the token types to use at token endpoints.
        config.add_token_type('oauthlib.oauth2.BearerToken',
                              request_validator=validator,
                              token_generator=validator.generate_access_token,
                              expires_in=int(settings.get('twitcher.token.expires_in', '3600')))

        config.add_route('access_token', TOKEN_ENDPOINT)
        config.add_view(generate_token_view, route_name='access_token')
        config.add_route('client', CLIENT_APP_ENDPOINT)
        config.add_view(register_client_app_view, route_name='client', renderer='json', permission='view')
