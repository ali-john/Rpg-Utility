"""rpgmaint - RPG Maintenance Utility"""

# pylint: disable=global-statement,protected-access,missing-function-docstring
# pylint: disable=unused-argument,logging-not-lazy

# IMPORTS

import sys
from argparse import ArgumentParser, Namespace, _SubParsersAction
from fnmatch import fnmatch

from rpgcore import RPGConfig, RPGLog, PARAMETER_SECTION

# ===== CONSTANTS =============================================================

# Other constants
VERSION = "0.3.1"


# ===== GLOBALS ===============================================================

# args: Namespace  # Command line arguments
rpg = RPGConfig()  # Configuration settings
log = RPGLog("maint")  # Log file

# ===== FUNCTIONS =============================================================


def do_param_delete(args: Namespace) -> int:
    if not rpg.has_param(args.key):
        log.error(f"Key '{args.key}' does not exist")
        return sys._getframe().f_lineno
    rpg.remove_option(PARAMETER_SECTION, args.key)
    rpg.save()
    log.info(f"{args.key}: deleted")
    return 0


def do_param_list(args: Namespace) -> int:
    key_pattern = args.key if args.key else ""
    for key in rpg.parameters():
        if fnmatch(key, key_pattern + "*"):
            value = rpg.get_param(key, decrypt=False)
            log.info(f"{key.ljust(25, '.')}: {value}")
    return 0


def do_param_set(args: Namespace) -> int:
    rpg.set_param(
        args.key,
        args.value,
        encrypt=args.encrypt or "password" in args.key.lower(),
    )
    log.info(f"{args.key} = {args.value}")
    return 0


def do_job_add(args: Namespace) -> int:
    # The namespace contains the parameters 'id' and 'day'
    job_id = args.id.upper()
    if rpg.job_exists(job_id):
        log.error(f"Job '{job_id}' already exists")
        return sys._getframe().f_lineno
    try:
        rpg.set_job(job_id, args.day)
    except ValueError as err:
        log.error(str(err))
        return sys._getframe().f_lineno
    _, _, _, next_run = rpg.get_job(job_id)
    next_run = next_run.strftime("%Y-%m-%d %H:%M")
    log.info(
        f"Job '{job_id}' scheduled for every {rpg.get_job_day_text(job_id)}. "
        f"Next run: {next_run}"
    )
    return 0


def do_job_change(args: Namespace) -> int:
    job_id = args.id.upper()
    if not rpg.job_exists(job_id):
        log.error(f"Job '{job_id}' does not exist")
        return sys._getframe().f_lineno
    try:
        rpg.set_job(job_id, args.day)
    except ValueError as err:
        log.error(str(err))
        return sys._getframe().f_lineno
    log.info(f"Job '{job_id}' updated")
    return 0


def do_job_delete(args: Namespace) -> int:
    job_id = args.id.upper()
    if not rpg.job_exists(job_id):
        log.error(f"Job '{job_id}' does not exist")
        return sys._getframe().f_lineno
    rpg.delete_job(job_id)
    log.info(f"Job '{job_id}' deleted")
    return 0


def do_job_list(args: Namespace) -> int:
    name_pattern = args.id if args.id else ""
    log.info(
        "JOBID"
        + " | "
        + "LAST RUN".ljust(16)
        + " | "
        + "NEXT RUN".ljust(16)
        + " | "
        + "FREQUENCY"
    )
    for job_id in rpg.jobs():
        if fnmatch(job_id, name_pattern + "*"):
            _, _, last_run, next_run = rpg.get_job(job_id)
            freq = "Every " + rpg.get_job_day_text(job_id)
            last_run = last_run.strftime("%Y-%m-%d %H:%M") if last_run else "Never"
            next_run = next_run.strftime("%Y-%m-%d %H:%M")
            log.info(f"{job_id} | {last_run:16s} | {next_run:16s} | {freq}")
    return 0


def do_server_add(args: Namespace) -> int:
    server_name = args.name.upper()
    if rpg.server_exists(server_name):
        log.error(f"Server '{server_name}' already exists")
        return sys._getframe().f_lineno
    # Add the server configuration
    server_type = "oracle" if args.oracle else "mssql" if args.mssql else "api"
    rpg.set_server(
        server_id=server_name,
        address=args.address,
        port=args.port,
        user=args.user,
        password=args.password,
        server_type=server_type,
    )
    log.info(f"Server '{server_name}' added")
    return 0


def do_server_change(args: Namespace) -> int:
    server_name = args.name.upper()
    if not rpg.server_exists(server_name):
        log.error(f"Server '{server_name}' does not exist")
        return sys._getframe().f_lineno
    # Update the server configuration
    server_change = {}
    if args.address:
        server_change["address"] = args.address
    if args.port:
        server_change["port"] = args.port
    if args.user:
        server_change["user"] = args.user
    if args.password:
        server_change["password"] = args.password
    if args.oracle:
        server_change["type"] = "oracle"
    elif args.mssql:
        server_change["type"] = "mssql"
    elif args.api:
        server_change["type"] = "api"
    rpg.set_server(server_name, **server_change)
    log.info(f"Server '{server_name}' updated")
    return 0


def do_server_delete(args: Namespace) -> int:
    server_name = args.name.upper()
    if not rpg.server_exists(server_name):
        log.error(f"Server '{server_name}' does not exist")
        return sys._getframe().f_lineno
    rpg.delete_server(server_name)
    log.info(f"Server '{server_name}' deleted")
    return 0


def do_server_list(args: Namespace) -> int:
    name_pattern = args.name if args.name else ""
    log.info("SERVER".ljust(10) + " | " + "ADDRESS".center(35) + " | TYPE   | USER")
    for server_name in rpg.servers():
        if fnmatch(server_name, name_pattern + "*"):
            line = f"{server_name:10s} | "
            try:
                (hostname, port, username, _, server_type) = rpg.get_server(server_name)
                line += f"{hostname:>30s}:{port:4d} | {server_type:6} | {username}"
            except KeyError as e:
                line += f"(decryption error)"
            log.info(line)
    return 0


def init_argparse() -> ArgumentParser:
    """Initialize the ArgumentParser object

    Returns:
        ArgumentParser: The ArgumentParser object
    """
    # pylint: disable=too-many-locals,too-many-statements

    parser = ArgumentParser(
        prog="rpgmaint",
        description="RPG Maintenance Utility",
        epilog="",
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {VERSION}"
    )
    subparsers = parser.add_subparsers(
        required=True,
        title="Subsystems",
        description="Select one of the following RPG susbsystems to manage",
        help="RPG Subsystem",
    )

    # ----- Command: Configuration Parameter Management ------------------------
    parser_param = subparsers.add_parser(
        "param", aliases=["p"], help="Configuration Parameters"
    )
    subparseres_config = parser_param.add_subparsers(
        required=True,
        title="Parameter Subcommands",
        description="Use one of the following subcommands to manage the RPG parameters",
        help="Action",
    )
    # ----- Subcommand: param set
    parser_param_add = subparseres_config.add_parser(
        "set", aliases=["s"], help="Set a configuration parameter"
    )
    parser_param_add.add_argument("key", metavar="KEY", help="Parameter key")
    parser_param_add.add_argument("value", metavar="VALUE", help="Parameter value")
    parser_param_add.add_argument(
        "-y", "--encrypt", action="store_true", help="Encrypt the value"
    )
    parser_param_add.set_defaults(func=do_param_set)
    # ----- Subcommand: param delete
    parser_param_delete = subparseres_config.add_parser(
        "delete", aliases=["d"], help="Delete a configuration parameter"
    )
    parser_param_delete.add_argument("key", metavar="KEY", help="Parameter key")
    parser_param_delete.set_defaults(func=do_param_delete)
    # ----- Subcommand: param list
    parser_param_list = subparseres_config.add_parser(
        "list", aliases=["l"], help="List all configuration parameters"
    )
    parser_param_list.add_argument(
        "key",
        metavar="KEY",
        nargs="?",
        default="*",
        help="Parameter key (wildcards allowed)",
    )
    parser_param_list.set_defaults(func=do_param_list)

    # ----- Command: Job Management --------------------------------------------
    parser_job = subparsers.add_parser("job", aliases=["j"], help="Job Scheduling")
    subparsers_job = parser_job.add_subparsers(
        required=True,
        dest="job_command",
        title="Job Subcmmands",
        description="Use one of the following subcommands to manage the scheduled jobs",
        help="Action",
    )
    # ----- Subcommand: job add
    parser_job_add = subparsers_job.add_parser(
        "add",
        aliases=["a"],
        help="Add a new scheduled job",
        epilog="For the acceptable syntax of the DAY parameter, see "
        + "https://en.wikipedia.org/wiki/Cron#Cron_expression",
    )
    parser_job_add.add_argument(
        "id", metavar="ID", help="Job ID (identifies the query to run)"
    )
    parser_job_add.add_argument(
        "day", metavar="DAY", help="Day(s) of the week or month to run the job"
    )
    parser_job_add.set_defaults(func=do_job_add)
    # ----- Subcommand: job change
    parser_job_change = subparsers_job.add_parser(
        "change",
        aliases=["c"],
        help="Change an existing scheduled job",
        epilog="For the acceptable syntax of the DAY parameter, see "
        + "https://en.wikipedia.org/wiki/Cron#Cron_expression",
    )
    parser_job_change.add_argument(
        "id", metavar="ID", help="Job ID (identifies the query to run)"
    )
    parser_job_change.add_argument(
        "day", metavar="DAY", help="Day(s) of the week or month to run the job"
    )
    parser_job_change.set_defaults(func=do_job_change)
    # ----- Subcommand: job delete
    parser_job_delete = subparsers_job.add_parser(
        "delete", aliases=["d"], help="Delete an existing scheduled job"
    )
    parser_job_delete.add_argument("id", metavar="ID", help="Job ID")
    parser_job_delete.set_defaults(func=do_job_delete)
    # ----- Subcommand: job list
    parser_job_list = subparsers_job.add_parser(
        "list",
        aliases=["l"],
        help="List all scheduled jobs",
        epilog="By default, all jobs are listed. Use an ID pattern to filter the list.",
    )
    parser_job_list.add_argument(
        "id",
        nargs="?",
        default="*",
        metavar="ID",
        help="Job ID pattern (wildcard allowed)",
    )
    parser_job_list.set_defaults(func=do_job_list)

    # ----- Command: Server Connections ----------------------------------------
    parser_server = subparsers.add_parser(
        "server", aliases=["s"], help="Server Connnections"
    )
    subparsers_server = parser_server.add_subparsers(
        required=True,
        title="Server Subcommands",
        description="Use one of the following subcommands to manage server connection definitions",
        help="Action",
    )
    # ----- Subcommand: server add
    parser_server_add = subparsers_server.add_parser(
        "add", aliases=["a"], help="Add a new server connection"
    )
    parser_server_add.add_argument(
        "name", metavar="NAME", help="Server connection name"
    )
    parser_server_add.add_argument(
        "-a",
        "--address",
        required=True,
        metavar="ADDRESS",
        help="Server address or hostname",
    )
    parser_server_add.add_argument(
        "-p",
        "--port",
        required=True,
        type=int,
        metavar="PORT",
        help="Server port number",
    )
    parser_server_add.add_argument(
        "-u",
        "--user",
        required=True,
        metavar="USERNAME",
        help="Username to be used when logging on to the server",
    )
    parser_server_add.add_argument(
        "-w",
        "--password",
        required=True,
        metavar="PASSWORD",
        help="Password to be used when logging on to the server",
    )
    server_type_mutex = parser_server_add.add_mutually_exclusive_group(required=True)
    server_type_mutex.add_argument(
        "-o", "--oracle", action="store_true", help="Use the Oracle connection protocol"
    )
    server_type_mutex.add_argument(
        "-m", "--mssql", action="store_true", help="Use the MS-SQL connection protocol"
    )
    server_type_mutex.add_argument(
        "-A", "--api", action="store_true", help="Indicates an API connection"
    )
    parser_server_add.set_defaults(func=do_server_add)
    # ----- Subcommand: server change
    parser_server_change = subparsers_server.add_parser(
        "change", aliases=["c"], help="Change an existing server connection"
    )
    parser_server_change.add_argument(
        "name", metavar="NAME", help="Server connection name"
    )
    parser_server_change.add_argument(
        "-a",
        "--address",
        metavar="ADDRESS",
        help="Server address or hostname",
    )
    parser_server_change.add_argument(
        "-p",
        "--port",
        type=int,
        metavar="PORT",
        help="Server port number",
    )
    parser_server_change.add_argument(
        "-u",
        "--user",
        metavar="USERNAME",
        help="Username for the server connection",
    )
    parser_server_change.add_argument(
        "-w",
        "--password",
        metavar="PASSWORD",
        help="Password for the server connection",
    )
    server_type_mutex = parser_server_change.add_mutually_exclusive_group()
    server_type_mutex.add_argument(
        "-o", "--oracle", action="store_true", help="Use the Oracle connection protocol"
    )
    server_type_mutex.add_argument(
        "-m", "--mssql", action="store_true", help="Use the MS-SQL connection protocol"
    )
    server_type_mutex.add_argument(
        "-A", "--api", action="store_true", help="Indicates an API connection"
    )
    parser_server_change.set_defaults(func=do_server_change)
    # ----- Subcommand: server delete
    parser_server_delete = subparsers_server.add_parser(
        "delete", aliases=["d"], help="Delete an existing server connection"
    )
    parser_server_delete.add_argument(
        "name", metavar="NAME", help="Server connection name"
    )
    parser_server_delete.set_defaults(func=do_server_delete)
    # ----- Subcommand: server list
    parser_server_list = subparsers_server.add_parser(
        "list",
        aliases=["l"],
        help="List all server connections",
        epilog="By default, all servers are listed. Use an ID pattern to filter the list.",
    )
    parser_server_list.add_argument(
        "name",
        nargs="?",
        default="*",
        metavar="NAME",
        help="Server connection name pattern (wildcard allowed)",
    )
    parser_server_list.set_defaults(func=do_server_list)

    return parser


# ===== MAINLINE EXECUTION ====================================================


def main():
    """Entry Point"""

    log_level = rpg.get_param("log_level")
    if log_level.lower() in ["debug", "info", "warning", "error", "critical"]:
        log.set_level(log_level)
    else:
        log.error(f"Invalid log_level specified in configuration: '{log_level}'")
        log.error('Valid values are "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"')

    # Parse the command line arguments
    parser = init_argparse()
    # If command line is empty, show usage and exit
    if len(sys.argv) == 1:
        parser.print_help()
        # Print help messages of all subparsers
        for action in parser._actions:
            if isinstance(action, _SubParsersAction):
                for key, value in action.choices.items():
                    if len(key) > 1:
                        print("\n" + value.format_help())
        sys.exit(sys._getframe().f_lineno)
    args = parser.parse_args()  # Parse the command line arguments
    rc = args.func(args)  # Execute the selected function
    sys.exit(rc)


if __name__ == "__main__":
    main()
