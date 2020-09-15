from users_app.views import (
    UserView, UserLoginView, UserStatusView, health_check, UsersListView,
    UserRegistrationView_v1
)


def setup_routes(app):
    app.router.add_get('/users_list', UsersListView)
    app.router.add_post('/users', UserView)
    app.router.add_get('/users', UserView)
    app.router.add_put('/users', UserView)
    app.router.add_delete('/users', UserView)
    app.router.add_post('/login', UserLoginView)
    app.router.add_post('/status', UserStatusView)
    app.router.add_get('/status', UserStatusView)
    app.router.add_post('/v1/register', UserRegistrationView_v1)

    app.router.add_get('/health-check/', health_check)
