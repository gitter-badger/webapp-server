{# vim: set ft=jinja: -#}
# README

Welcome aboard!

## Files

The `www` directory is shared with your group, everything else is yours.

`README.md` is this file.

The funny message comes from `~/.bash_profile`.

Feel free to adapt the git configuration in `~/.gitconfig`.

## MySQL

Connect to MySQL (hint: \`echo \$MYSQL_PASSWORD\`):

    $ mysql --user $MYSQL_USERNAME --host $MYSQL_HOST --password $MYSQL_DATABASE

You may also see how it's currently done in `index.php`.


## PHP

Composer and Laravel are installed for your convenience.

    $ composer --help
    $ laravel --help


## Laravel tutorial

This is from the [Laravel 5.1 documentation](http://laravel.com/docs/5.1).

### Creating a new project

Here we are creating a project called `blog`

    $ cd www
    $ laravel new blog
    $ chmod -R 0777 blog/storage
    $ chmod 0777 blog/bootstrap/cache


### Nginx (_engine-X_)

You only have to fix the path into the nginx configuration file to have your
application showing up on port 80. The file is `www/config/nginx.conf`

    #root /var/www/public;
    root /var/www/blog/public;

And restart the servers:

    $ sudo sv restart nginx


#### Logs

The server logs are put there in `/var/www/logs`.

The error log will be useful.

    $ tail /var/www/logs/error.log

### Configuring the database connection

We are gonna read the database configuration from the environment. See
[12factors](http://12factor.net/config).

Modify `blog/config/database.php` as such:

    // ...
    'connections' => [
        // ...
        'mysql' => [
            'driver' => 'mysql',
            'host' => env('MYSQL_HOST', env('DB_HOST', 'localhost')),
            'database' => env('MYSQL_DATABASE', env('DB_DATABASE', 'forge')),
            'username' => env('MYSQL_USERNAME', env('DB_USERNAME', 'forge')),
            'password' => env('MYSQL_PASSOWRD', env('DB_PASSWORD', '')),
            'charset' => 'utf8mb4',
            'collation' => 'utf8mb4_unicode_ci',
            'prefix' => '',
            'strict' => false
        ],
        // ...
    ],
    // ...

`env('MYSQL_HOST') (or `$_SERVER['MYSQL_HOST']`) is the environment variable
containing the host for the MySQL connection. It's much more flexible than
`.env` files. Keep the `.env` file for you local setup.

What is `utf8mb4`? See: https://mathiasbynens.be/notes/mysql-utf8mb4


## Initializing the models

The models are defined through
[migrations](http://laravel.com/docs/5.1/migrations) which enable rollbacks.
You should always use them. We will instantiate the default model which creates
two tables do deal with users and their password.

The default model was set for utf8 and not utf8mb4, so we have to tweak it a
little bit. Open `blog/database/migrations/2014_10_12_000000_create_users_table.php`

    //$table->string('email')->unique();
    $table->string('email', 191)->unique();

Now, we are ready to run the migrations:

    $ php blog/artistan migrate
    Migration table created successfully.
    Migrated: 2014_10_12_00000_create_users_table
    Migrated: 2014_10_12_10000_create_password_resets_table

Et voilà!

    echo "SHOW TABLES" | mysql -u $MYSQL_USERNAME -h $MYSQL_HOST -p $MYSQL_DATABASE
    Enter password:
    Tables_in_<GROUPNAME>
    migrations
    password_resets
    users

{% include 'README-footer.md' -%}
