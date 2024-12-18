# Generated by Django 4.2.4 on 2024-11-20 20:35

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('movies', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('accounts', '0001_initial'),
        ('community', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='liked_posts',
            field=models.ManyToManyField(blank=True, help_text='좋아요한 게시글 목록', related_name='liked_posts_by_users', to='community.post'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='liked_reviews',
            field=models.ManyToManyField(blank=True, help_text='좋아요한 리뷰 목록', related_name='liked_by_users', to='community.review'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='watched_movies',
            field=models.ManyToManyField(blank=True, help_text='사용자가 이미 본 영화 목록', related_name='watched_movies_by_users', to='movies.movie', verbose_name='본 영화 목록'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['user', '-created_at'], name='accounts_no_user_id_b37b35_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['is_read'], name='accounts_no_is_read_d448a6_idx'),
        ),
    ]
