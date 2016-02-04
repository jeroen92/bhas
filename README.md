# BGP Hijack Alert System
BHAS is a passive BGP control-plane hijack detection system. Our paper will be published at https://homepages.staff.os3.nl/~delaat/rp/2015-2016/p66/report.pdf

### Usage
Make sure you use PIP to install *ipwhois*, *netaddr*, *peewee* and *psycopg2*.
Monitored prefixes are expected to be in input.csv. Logging can be adjusted in settings.py. Currently only PostgreSQL is supported because of its cidr datatype.
For the first use, put CIDR notated prefix information in input.csv and then run *./init.py -i* to initialize the database. This process could take some time depending on the amount of monitored prefixes and will query prefix information from [RIPEstat](https://stat.ripe.net). When completed, run *./init.py < testdata.json* where *testdata.json* is [ExaBGP](https://github.com/Exa-Networks/exabgp) JSON output, or bootstrap BHAS by hooking it to ExaBGP. See *exabgp.conf* for and example ExaBGP configuration.

For more information, launch bhas with *--help* to see all available flags and arguments.

### Issues
Use the Github issue tracker or contact *jeroen92* or *bamterborch*.

### License
See the LICENSE file, located in the root of the git repository for licensing information.
