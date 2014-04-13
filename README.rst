Olho Neles
==========

Tool to monitor Brazilian legislators expenses while in the exercise of their mandates.


Install
-------

#. Clone the repository::

        git clone https://github.com/olhoneles/olhoneles.git

#. Create a *virtualenv*::

        cd olhoneles
        virtualenv .

#. Install dependencies::

    make setup

#. Create your database::

    make data

#. Run it::

    make run

#. If you would like to override some settings.py variables, like SECRET_KEY, DATABASES, ALLOWED_HOSTS, please create the ``olhoneles/local.config`` file.


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

Join us at the `dev-mailing list <http://listas.olhoneles.org/cgi-bin/mailman/listinfo/montanha-dev>`_ and at
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
