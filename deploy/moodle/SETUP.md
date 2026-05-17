# Moodle Setup

After `docker compose -f services/moodle/docker-compose.yml up -d`, finish the Moodle setup in the browser at the Moodle hostname.

## Required Moodle Web Services Steps

1. Log in as the Moodle admin user configured in `.env`.
2. Go to `Site administration > Server > Web services > Overview`.
3. Enable web services.
4. Enable the REST protocol.
5. Create an external service for this app.
6. Add only the functions required by the app:
   - `core_webservice_get_site_info`
   - `core_course_get_categories`
   - `core_course_create_courses`
   - `core_course_get_contents`
   - `core_completion_get_activities_completion_status`
   - `core_enrol_get_users_courses`
   - `core_user_get_users_by_field`
   - `mod_page_add_instance`
   - `mod_url_add_instance`
7. Create a token for the external service.
8. Put the token in `services/mcp/.env` as `MOODLE_TOKEN`. For local all-in-one development, also put it in the root `.env`.

## Roles

Use Moodle roles as the source of truth.

- Creator users need the capabilities required to create courses and add resources in the target category.
- Student users need enrollment or visibility permissions for the courses they consume.

## Cron

The `moodle-cron` service runs `admin/cli/cron.php` every minute. Keep this service running in production.

## Backups

Back up both the PostgreSQL database and the Moodle data volume. A database backup alone is not sufficient because uploaded files live in `moodledata`.
