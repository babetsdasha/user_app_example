import datetime

from users_app.models import User


class ExecuteCQL:
    def __init__(self, app):
        self.app = app

    def create_db_user(self, data):
        return User.objects.create(
            created=datetime.datetime.now(),
            updated=datetime.datetime.now(),
            **data)

    def update_db_user(self, user_id, data):
        User.objects(user_id=user_id).update(
            updated=datetime.datetime.now(),
            **data
        )
        return User.objects.get(user_id=user_id)

    def get_users_count(self):
        return User.objects.all().count()

    def get_db_user(self, user_id):
        return User.objects.get(user_id=user_id)

    def get_db_user_by_username(self, username):
        return User.objects.get(username=username)

    def get_db_users(self, filters):
        return list(User.objects.filter(**filters))

    def get_db_users_all(self):
        return list(User.objects.all())

    def get_db_user_by_api_key(self, api_key):
        return User.objects.get(api_key=api_key)

    def delete_db_user(self, user_id):
        User.objects(user_id=user_id).delete()
        return True

    def __getitem__(self, name):
        method = getattr(self, name)

        def execute_in_thread(*args, **kwargs):
            loop = self.app.loop

            return loop.run_in_executor(None, method, *args, **kwargs)

        return execute_in_thread
