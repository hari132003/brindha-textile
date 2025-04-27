#!/bin/bash

# Update and install necessary dependencies
apt-get update && apt-get install -y unixodbc-dev curl

# Add Microsoft repository for ODBC driver
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update

# Install ODBC Driver 17
ACCEPT_EULA=Y apt-get install -y msodbcsql17
