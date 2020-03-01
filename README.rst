.. image:: https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg
     :target: https://github.com/pydanny/cookiecutter-django/
     :alt: Built with Cookiecutter Django

.. image:: https://travis-ci.org/valuehack/scholariumat.svg?branch=master
   :target: https://travis-ci.org/valuehack/scholariumat

.. image:: https://coveralls.io/repos/github/valuehack/scholariumat/badge.svg?branch=master
   :target: https://coveralls.io/github/valuehack/scholariumat?branch=master

Setup for MAC OS/Linux
-----
* Create an virtual environment
    * Install venv ``python3 -m pip install --user virtualenv``
    * Create venv ``python3 -m venv .venv``
    * Activate venv ``source .venv/bin/activate``
    * Example: ``.venv/bin/pip install -r requirements``
* Install Requirenments pip install -r requirements.txt``
* Install Cairo and Pago ``brew install cairo`, ``brew install pago``
* Install Django Debugger Toolbar pip install django-debug-toolbar``
* API/Secret keys are managed as environmental variables. There a no required variables but some functionality depends on certain keys. A list variables needed for production can be found in ``app.json``.
* Default settings for local runs are ``config/settings/local.py``. Tests (including Travis) use ``config/settings/test.py`` and production environments use ``config/settings/production.py``.

Database Setup
------
* Create a database dump on your server ``pg_dump dbname > outfile``
* Restore dump ``psql dbname < infile``
* Create accessible postgres database with same name (or at location specified in the ``DATABASE_URL`` environmental variable) and run ``python manage.py migrate``

Running Tests
-------------
Tests are handled by django: ``python manage.py test``

Compiling CSS/JS files
-------------------
This project uses Semantic UI. See their `documentation <https://semantic-ui.com/introduction/getting-started.html>`_ for modifications. 

Coding Style
------------
* PEP8 with a line length requirement of 120 instead of 80
* Best practices concerning Django as described in `'Two Scoops of Django' <https://www.twoscoopspress.com/products/two-scoops-of-django-1-11>`_

Production Environment
----------------------
* Build for deployment on `Heroku <https://www.heroku.com/>`_
* Uploaded files are handled by `Amazon S3 <https://aws.amazon.com/s3/>`_
* Emails are managed by `Sendgrid <https://sendgrid.com/>`_
* Redis is used for caching and concurrency 

License
-------
:License: MIT
