import pymysql
pymysql.install_as_MySQLdb()

# Bypassing the strict Django version check for older XAMPP MariaDB (10.4)
import django
from django.db.backends.base.base import BaseDatabaseWrapper
BaseDatabaseWrapper.check_database_version_supported = lambda self: None

from django.db.backends.mysql.features import DatabaseFeatures
DatabaseFeatures.can_return_columns_from_insert = False
