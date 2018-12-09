.. image:: https://drive.google.com/uc?id=0B58q9z1XmLXIUDdDMXpoZFEyZDQ
Source code for https://scholarium.at/

.. image:: https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg
     :target: https://github.com/pydanny/cookiecutter-django/
     :alt: Built with Cookiecutter Django

.. image:: https://travis-ci.org/valuehack/scholariumat.svg?branch=master
   :target: https://travis-ci.org/valuehack/scholariumat

.. image:: https://coveralls.io/repos/github/valuehack/scholariumat/badge.svg?branch=master
   :target: https://coveralls.io/github/valuehack/scholariumat?branch=master

Setup
-----
* This project runs on Python >= 3.6 (and Django >= 2.0)
* Requirements for local virtual environments can be found in requirement/local.txt. Install with ``pip install -r requirements/local.txt``
* API/Secret keys are managed as environmental variables. There a no required variables but some functionality depends on certain keys. A list variables needed for production can be found in ``app.json``.
* Create accessible postgres database with same name (or at location specified in the ``DATABASE_URL`` environmental variable) and run ``python manage.py migrate``
* Default settings for local runs are ``config/settings/local.py``. Tests (including Travis) use ``config/settings/test.py`` and production environments use ``config/settings/production.py``.

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
