from django.contrib.auth import get_user_model
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.db.models import signals
from django.db import connections, router

DJANGO_NATIVE_PERMISSION = {
    'add', 'change', 'delete'}
PERM_FIRST_TIME_SET = None


def check_and_create_model_initial_data(model):
    """
    check initial_data existent, if it is vacant, then create it
    :param model:
    :return:
    """
    if not (hasattr(model, 'Admin') and hasattr(model.Admin, 'initial_data')):
        return
    datum = getattr(model.Admin, 'initial_data')
    if isinstance(datum, (list, tuple)):
        pass
    else:
        if callable(datum):
            model.Admin().initial_data()


def admin_initial_data(admin):
    """
    parse initial_data from src.admin class
    :param admin:
    :return:
    """
    initial_data = admin.initial_data
    if callable(initial_data):
        try:
            initial_data()
        except Exception:
            import traceback
            traceback.print_exc()

    else:
        if isinstance(initial_data, (list, tuple)):
            pass


def maintain_model_initial_data(**kwargs):

    app_config = kwargs.get('app_config')
    db = kwargs.get('using')
    connection = connections[db]
    user_model = get_user_model()
    if user_model.objects.count() == 0:
        super_user = user_model.objects.create_superuser(
            'root@root.com', 'root')
        super_user.name = 'Super Admin'
        super_user.save()
    admin_user = user_model.objects.get(id=1)

    for model in router.get_migratable_models(app_config,
                                              (connection.alias), include_auto_created=False):
        content_type = ContentType.objects.get_for_model(
            model, for_concrete_model=False)
        _app_label, model_name = content_type.natural_key()

        check_and_create_model_initial_data(model)
        admin_site = admin.site
        if model in admin_site._registry:
            admin_class = admin_site._registry[model]
            if hasattr(admin_class, 'initial_data'):
                admin_initial_data(admin_class)
            else:
                pass


def post_syncdb_initial_data(**kwargs):
    global PERM_FIRST_TIME_SET
    # from django_redis import get_redis_connection
    maintain_model_initial_data(**kwargs)
    if PERM_FIRST_TIME_SET is None:
        # cprint('update permissions. (it shall run merely one time.)', 'green')
        # process_extra_permission()
        # maintain_perms_cache(op='update')
        PERM_FIRST_TIME_SET = False


signals.post_migrate.connect(post_syncdb_initial_data)
