# Generated by Django 4.2 on 2023-05-10 09:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("recommend", "0017_rename_movie_logo_song_song_logo"),
    ]

    operations = [
        migrations.RenameField(
            model_name="mylist",
            old_name="movie",
            new_name="song",
        ),
        migrations.RenameField(
            model_name="myrating",
            old_name="movie",
            new_name="song",
        ),
    ]
