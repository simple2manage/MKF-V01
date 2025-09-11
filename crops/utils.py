from django.db import connection

def reset_cropplanrow_id():
    with connection.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE crops_cropplanrow RESTART IDENTITY CASCADE;")
