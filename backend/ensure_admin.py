os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = 'yourlegacy45@gmail.com'
email = 'yourlegacy45@gmail.com'
password = 'Yourlegacy@456'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password, role='admin')
    print(f"Superuser {username} created successfully.")
else:
    user = User.objects.get(username=username)
    user.set_password(password)
    user.role = 'admin'
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print(f"Superuser {username} updated successfully.")
