# RPG – Report Generator

## Description

Internal Audit data analytics run pre-defined reports at varying times. Also, tables in the Internal Audit database need to be refreshed from time to time to allow being used as the source for Power BI dashboards.

The RPG tool runs these reportsd on a defined schedule. It is designed to operate on a server connected to database servers where, based on a schedule, a certain report is triggered. The result is written to a table in the Internal Audit database.

A separate maintenance module allows to add, delete or modify the definition of

* report job schedules
* server connection information

## Files in this repository

* `.pylintrc` ... Lint configuration to be used for this project
* `README.md` ... this file
* `RPG Maintenance Utility Design Specifications.docx` ... Specifications for the GUI maintenance utility
* `rpgcore.py` ... Provides core functions for the report generator utility
* `rpgmaint.py` ... CLI version of the RPG maintenance utility
* `rpg_ods.ini` ... Operfational data store: This file holding configuration data. This is what *rpgmaint* modifies.
* `rpg_ods.key` ... Encryption key used to encrypt passwords in the configuration file

## The rpgcore module

The `rpgcode` module provides two objects to be used withion RPG operation:

* **RPGLog** ... RPG logging object. It provides all methods provided by the usual Python logging object.
* **RPGConfig** ... Configuration object,.. Provides methods to access the RPG configuration.

## The RPGLog object

Use this object to build logging into your code. It takes care of setting up handlers and formatters. Use the following methods as usual in Python logging:

* critical
* error
* warning
* info
* debug

## The RPGConfig object

Use this object to acces RPG configuration information through the following methods. The object itself takes care of interacting with the configuration file and encrypting passwords.

### Parameter methods

* `get_param` ... Get a parameter value
* `has_param` ... Determine if a parameter exists
* `set_param` ... Set a parameter value

### Job methods

* `delete_job` ... Delete a job from the configuration
* `get_job` ... Get the job details for a given job ID
* `get_job_day_text` ... Get the day text for a given job ID
* `job_is_due` ... Determine if a job is due to run
* `job_exists` ... Determine if a job exists
* `reset_job` ... Reset the last_run attribute of a job
* `run_job` ... Update the last_run attribute of a job to the current time
* `set_job` ... Set the job details for a given job ID

### Server methods

* `delete_server` ... Delete a server from the configuration
* `get_server` ... Get the server details for a given server ID
* `server_exists` ... Determine if a server exists
* `set_server` ... Set the server details for a given server ID

### Utility methods

* `jobs` ... Return the ids of all defined jobs
* `parameters` ... Return all parameters as a dictionary
* `servers` ... Return the ids of all defined servers
* `save` ... Write the current configuration to the file

