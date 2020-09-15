import json
from aiohttp import web
from cassandra.cluster import NoHostAvailable
from cassandra.cqlengine.query import DoesNotExist
from cryptography.hazmat.backends.openssl.backend import backend
from cryptography.hazmat.primitives import serialization

from users_app.cql_queries import ExecuteCQL
from users_app.kafka_producer import send_one
from users_app.models import AuthToken, Key, RefreshToken, User
from users_app.serializers import KeySchema, UserSchema
from users_app.utils import APIException, dumps


class APIView(web.View):
    def __init__(self, request):
        super(APIView, self).__init__(request)
        self.execute_cql = ExecuteCQL(app=self.request.app)

    async def check_request_data(self):
        if 'username' not in self.data or 'password' not in self.data:
            return False
        return True

    async def is_user_exists(self):
        username = self.data.get('username')
        try:
            self.user_obj = await self.execute_cql['get_db_user_by_username'](
                username
            )
            return True
        except DoesNotExist:
            self.user_obj = None
            return False

    async def check_credentials(self):
        username = self.data.get('username')
        password = self.data.get('password')

        try:
            self.user_obj = await self.execute_cql['get_db_user_by_username'](
                username
            )
        except DoesNotExist:
            return False
        return self.user_obj.check_password(password)


class UserView(APIView):
    async def get(self):
        self.data = self.request.query
        try:
            user = await self.execute_cql['get_db_user'](self.data['user_id'])
        except DoesNotExist:
            raise APIException(message='user does not exists')
        schema = UserSchema()
        userdata = schema.dump(user).data
        return web.json_response(userdata, dumps=dumps)

    async def post(self):
        self.data = await self.request.json()
        if not await self.check_request_data():
            raise APIException(message='username or password is not provided')
        schema = UserSchema()
        user_data = schema.load(self.data)
        if user_data.errors:
            raise APIException(message=user_data.errors)
        if await self.is_user_exists():
            raise APIException(message='user with username {} already exists'.format(
                self.data['username']
            ))
        user_data = user_data.data
        user_data['api_key'] = User.generate_api_key()
        user_obj = await self.execute_cql['create_db_user'](user_data)
        userdata = schema.dump(user_obj).data
        await self.request.app['logger'].info(
            'users_app.views.UserView.post',
            'user created: {}'.format(schema.dumps(userdata).data)
        )
        return web.json_response(userdata, dumps=dumps)

    async def put(self):
        self.data = await self.request.json()
        schema = UserSchema()
        user_data = schema.load(self.data)
        try:
            await self.execute_cql['get_db_user'](
                self.data['user_id'])  # to check is user exists
            user = await self.execute_cql['update_db_user'](
                self.data.pop('user_id'),
                user_data.data)
        except DoesNotExist:
            raise APIException(message='user does not exists')

        if 'email' in user_data.data.keys():
            notification = [{
                "name": "change-profile",
                "channel": str(user.user_id),
                "data": {
                    "message": "change email",
                    "new_email": user_data.data['email']
                }
            }]
            await send_one(
                self.request.app,
                self.request.app['config']['notification_topic'],
                json.dumps(notification)
            )
        schema = UserSchema()
        userdata = schema.dump(user).data
        await self.request.app['logger'].info(
            'users_app.views.UserView.put',
            schema.dumps(userdata).data
        )
        return web.json_response(userdata)

    async def delete(self):
        self.data = await self.request.json()
        deleted = self.data.get('deleted', True)
        try:
            user = await self.execute_cql['get_db_user'](
                self.data['user_id'])  # to check is user exists
            await self.execute_cql['update_db_user'](self.data['user_id'],
                                                     {'deleted': deleted})
            await self.request.app['logger'].info(
                'users_app.views.UserView.delete',
                'user {} marked as deleted'.format(
                    str(user.user_id)))
        except DoesNotExist:
            await self.request.app['logger'].info(
                'users_app.views.UserView.delete',
                'user does not exists', user_id=self.data['user_id'])
            return web.Response(status=404)
        return web.Response(status=200)


class UsersListView(APIView):
    async def get(self):
        return web.json_response(dict(users=[
            UserSchema().dump(user).data for user in
            await self.execute_cql['get_db_users']({'deleted': False})
        ]))


class UserStatusView(APIView):
    async def get(self):
        self.data = self.request.query
        try:
            user = await self.execute_cql['get_db_user'](
                self.data['user_id']
            )
        except DoesNotExist:
            raise APIException(message='user does not exists')
        return web.json_response(
            dict(is_active=user.is_active, ban_reason=user.ban_reason)
        )

    async def post(self):
        self.data = await self.request.json()
        is_active = bool(int(self.data['is_active']))
        ban_reason = self.data['ban_reason']
        try:
            await self.execute_cql['update_db_user'](
                self.data.pop('user_id'),
                {'is_active': is_active, 'ban_reason': ban_reason}
            )
            await self.request.app['logger'].info(
                'users_app.views.UserStatusView.post',
                'user status changed to {}'.format(str(is_active))
                )
        except DoesNotExist:
            raise APIException(message='User does not exists')
        return web.Response(status=200)


class UserLoginView(APIView):
    async def post(self):
        self.data = await self.request.json()
        if not await self.check_request_data():
            raise APIException(message='Missing password or username')
        if not (
            await self.is_user_exists() and
            await self.check_credentials()
        ):
            raise APIException(message='Invalid password or username')
        try:
            key = await self.execute_cql['get_key_by_user_id'](
                self.user_obj.user_id)
        except DoesNotExist:
            raise APIException('key doesnt exists')
        schema = UserSchema()
        userdata = schema.dump(self.user_obj).data
        return web.json_response(userdata, dumps=dumps)


class UserRegistrationView_v1(APIView):
    async def post(self):
        self.data = await self.request.json()
        if not await self.check_request_data():
            raise APIException(message='username or password is not provided')
        if await self.is_user_exists():
            raise APIException(
                message='user with username {} already exists'.format(
                    self.data['username']))
        schema = UserSchema()
        user_data = schema.load(self.data)
        if user_data.errors:
            raise APIException(message=user_data.errors)
        user_data = user_data.data
        user_data['api_key'] = User.generate_api_key()
        user_obj = await self.execute_cql['create_db_user'](user_data)
        userdata = schema.dump(user_obj).data
        return web.json_response(userdata, dumps=dumps)


async def health_check(request):
    try:
        execute_cql = ExecuteCQL(app=request.app)
        await execute_cql['get_users_count']()
    except NoHostAvailable:
        return web.Response(status=500)
    return web.Response(status=200)
