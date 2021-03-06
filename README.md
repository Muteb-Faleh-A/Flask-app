
http://18.222.4.38.xip.io/

Ud-FSND-LinuxServerConfiguration
Udacity Full Stack Web Developer Nanodegree Project : Linux Server Configuration

Project Description
Project Specification
IP address and SSH port
Public IP : http://18.222.4.38/
SSH port : 2200
Summary of software installed and configuration changes made
Update all currently installed packages
One of the most important and simplest ways to ensure your system is secure is to keep your software up to date with new releases
when setting up a new machine, you can be pretty safe in just accepting that the system is always making the best decisions for you
sudo apt update     # update available package lists
sudo apt upgrade    # upgrade installed packages
sudo apt autoremove # automatically remove packages that are no longer required
Create a New User grader and give grader sudo
sudo adduser grader # create a new user named grader
# grader password is 'udacity'
# use the usermod command to add the user to the sudo group
# https://www.digitalocean.com/community/tutorials/how-to-create-a-sudo-user-on-ubuntu-quickstart
sudo usermod -aG sudo grader
Change the SSH port from 22 to 2200.
sudo nano /etc/ssh/sshd_config  # change port 22 to 2200
sudo service ssh restart        # restart ssh service
Create an SSH key pair for grader using the ssh-keygen tool
# local machine
ssh-keygen 
# Enter file in which to save the key (/home/bcko/.ssh/id_rsa): grader
# empty passphrase
sudo mkdir /home/grader/.ssh
sudo chown grader:grader /home/grader/.ssh # changing ownership of .ssh to grader
sudo chmod 700 /home/grader/.ssh           # change folder permission
sudo cp /home/ubuntu/.ssh/authorized_keys /home/grader/.ssh/
sudo chmod 644 /home/grader/.ssh/authorized_keys
ssh grader@18.216.240.252 -p 2200 -i grader
Configure the Uncomplicated Firewall (UFW) to only allow incoming connections for SSH (port 2200), HTTP (port 80), and NTP (port 123).
Warning: When changing the SSH port, make sure that the firewall is open for port 2200 first, so that you don't lock yourself out of the server.
When you change the SSH port, the Lightsail instance will no longer be accessible through the web app 'Connect using SSH' button. The button assumes the default port is being used.
sudo ufw status                 # check ufw status 
sudo ufw default deny incoming  # initially block all incoming requests
sudo ufw default allow outgoing # default rule for outgoing connections
sudo ufw allow 2200/tcp         # allow SSH on port 2200
sudo ufw allow www              # allow HTTP on port 80
sudo ufw allow ntp              # allow NTP on port 123
sudo ufw enable                 # enable firewall
sudo ufw status                 # check ufw status
Disable root
sudo nano /etc/ssh/sshd_config  # open sshd_config
# change PermitRootLogin to no
sudo service ssh restart        # restart ssh service
Configure the local timezone to UTC.
# https://www.digitalocean.com/community/tutorials/how-to-set-up-time-synchronization-on-ubuntu-16-04
sudo timedatectl set-timezone UTC
Install Apache and mod_wsgi for python3
sudo apt install apache2                  # install apache
sudo apt install libapache2-mod-wsgi-py3  # install python3 mod_wsgi
Install and configure PostgreSQL
sudo apt install postgresql                    # install postgreSQL
sudo nano /etc/postgresql/9.5/main/pg_hba.conf # no remote connections to the database
# Create a new database user named catalog that has limited permissions to your catalog application database.
sudo -u postgres createuser -P catalog

Clone and setup your Item Catalog project from the Github repository
sudo apt install git # Install git

sudo mkdir /var/www/catalog # create catalog folder
sudo chown -R grader:grader catalog
cd /var/www/catalog
sudo git clone https://github.com/Muteb-Faleh-A/Flask-app.git
create .wsgi file
nano project.wsgi
# from project import app as application
configure Apache to handle requests using the WSGI module
cd /etc/apache2/sites-enabled
sudo cp 000-default.conf catalog.conf
sudo nano catalog.conf
# http://18.222.4.38/
<VirtualHost *:80>
        # The ServerName directive sets the request scheme, hostname and port that
        # the server uses to identify itself. This is used when creating
        # redirection URLs. In the context of virtual hosts, the ServerName
        # specifies what hostname must appear in the request's Host: header to
        # match this virtual host. For the default virtual host (this file) this
        # value is not decisive as it is used as a last resort host regardless.
        # However, you must set it for any further virtual host explicitly.
        ServerName catalog

        WSGIScriptAlias / /var/www/Ud-FSND-ItemCatalogApp-PythonFlask/project.wsgi
        <Directory /var/www/Ud-FSND-ItemCatalogApp-PythonFlask>
                WSGIProcessGroup Ud-FSND-ItemCatalogApp-PythonFlask
                WSGIApplicationGroup %{GLOBAL}
                Order deny,allow
                Allow from all
        </Directory>

        # Available loglevels: trace8, ..., trace1, debug, info, notice, warn,
        # error, crit, alert, emerg.
        # It is also possible to configure the loglevel for particular
        # modules, e.g.
        #LogLevel info ssl:warn

        ErrorLog ${APACHE_LOG_DIR}/error.log
        CustomLog ${APACHE_LOG_DIR}/access.log combined

        # For most configuration files from conf-available/, which are
        # enabled or disabled at a global level, it is possible to
        # include a line for only one particular virtual host. For example the
        # following line enables the CGI configuration for this host only
        # after it has been globally disabled with "a2disconf".
        #Include conf-available/serve-cgi-bin.conf
</VirtualHost>

# vim: syntax=apache ts=4 sw=4 sts=4 sr noet

Install Flask and dependencies
sudo apt install python3-pip
sudo pip3 install --upgrade pip
sudo pip3 install Flask
sudo pip3 install httplib2
sudo pip3 install requests
sudo pip3 install oauth2client
sudo pip3 install sqlalchemy
List of any third-party resources you made use of to complete this project
Shell Commands
Getting Started with Amazon Lightsail
Set up SSH for your Linux/Unix-based Lightsail instances
How To Create a Sudo User on Ubuntu
http://flask.pocoo.org/docs/0.12/deploying/#deployment
http://flask.pocoo.org/docs/0.12/deploying/mod_wsgi/
