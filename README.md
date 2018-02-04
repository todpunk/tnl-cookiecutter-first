# tnl-cookiecutter-first
The TodAndLorna.com My First Cookie Cutter Template

Current Status: Fiddling, not ready

A generic project template for postgresql db with python-backed web dev the TnL way!  Tod Hansmann wrote this for his use because this is how he works, but if you like it, great!

This should give you everything you need to access a database with a JSON API you can login against and get a token for.  The user will be `siteadmin` with password `ChangeMe!` which you should definitely change of course.

## Set things up 

Create the database using your favorite method using the following commands as a basis for what you're doing.  If you just run these as a db superuser these will work from the commandline assuming you're in the {{cookiecutter.app_name}} root.

```
createdb {{cookiecutter.dbname}}
createdb {{cookiecutter.testdbname}}
createuser {{cookiecutter.dbuser}}
psql -d {{cookiecutter.dbname}} -c "alter user {{cookiecutter.dbuser}} with encrypted password '{{cookiecutter.dbpass}}'"
psql -d {{cookiecutter.dbname}} -c "grant all privileges on database {{cookiecutter.dbname}} to user '{{cookiecutter.dbuser}}'"
psql -d {{cookiecutter.dbname}} -c "grant all privileges on database {{cookiecutter.testdbname}} to user '{{cookiecutter.dbuser}}'"
psql -d {{cookiecutter.dbname}} -a -f {{cookiecutter.app_name}}-appsrv/db/schema.sql
psql -d {{cookiecutter.testdbname}} -a -f {{cookiecutter.app_name}}-appsrv/db/schema.sql
psql -d {{cookiecutter.dbname}} -c "insert into users (username, email, password, salt) values ('siteadmin', 'fake@example.com', '', '')"
```

In the appsrv directory, if you haven't already got pyramid and the other bits, do a `pip -r requirements.txt` and then `pserve --reload development.ini` which will get the API server running on 6543 or http://localhost:6543/app/ should get that running.

Frontend dev will be different of course. You should then go into the static directory and do an `npm install` and `npm build`, and if you want to run the react server thing, `npm start` and you can start cracking on whatever!

Yay!