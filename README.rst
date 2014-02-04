Olho Neles
==========

A simple software to allow easier watching of the activities of the legislators
from the brazilian State of Minas Gerais.


Install
-------

#. Clone the repository::

        git clone https://github.com/olhoneles/olhoneles.git

#. Create a *virtualenv*::

        cd olhoneles
        virtualenv .

#. Install dependencies::

    pip install -r requirements.txt

#. Create your ``settings.py``::

    cp olhoneles/settings.py.sample olhoneles/settings.py

#. Define a ``SECRET_KEY``. You can use this `generator <http://www.miniwebtool.com/django-secret-key-generator/>`_.

#. Create your database::

    python manage.py syncdb --migrate

#. Run it::

    python manage.py runserver


Collecting the data
-------------------

After setting up, you can collect one of the supported legislative houses
(cmbh, almg, cmsp, senado) by using the collect command like this:

    python manage.py collect <house>

You can add ``debug`` after the name of the house to get a more verbose
output. Note that the collection process happens in a transaction and that
the expenses are not added to the main Expense table while the collection
is running, so you will not see partial data in the site while collecting.


Contribute
----------

Join us at the `dev-mailing list <http://listas.olhoneles.org/cgi-bin/mailman/subscribe/montanha-dev>`_ and at
`#olhoneles <irc://irc.freenode.net:6667/olhoneles>`_ on Freenode.

Fork the repository and send your pull-requests.


License
-------

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
