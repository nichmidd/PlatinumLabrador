# Client Experience Monitoring

## Install base requirements

Add the Microsoft repository and then install the ODBC driver

    apt install curl apt-transport-https
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
    curl https://packages.microsoft.com/config/debian/9/prod.list > /etc/apt/sources.list.d/mssql-release.list
    apt update
    ACCEPT_EULA=Y apt install msodbcsql17

## Install python3 dependancies

pip3 install -r requirements.txt

## Tweek config.json to suit

Update this bit

## PROFIT
