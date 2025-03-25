""" RPG Class definitions"""

# ----- IMPORTS ---------------------------------------------------------------

import logging
import re
from configparser import ConfigParser
from datetime import datetime
from pathlib import Path

import colorama as co
from croniter import croniter
from cryptography.fernet import Fernet, InvalidToken

# ----- CONSTANTS -------------------------------------------------------------

CONFIG_FILE = Path("rpg_ods.ini")  # Configuration file path
FERNET_PREFIX = "gAAAAAB"  # Prefix for encrypted values
KEY_FILE = Path("rpg_ods.key")  # Encryption key file path

# Regular expressions for day of the month and weekday parts of the cron string
# Reference 1: https://en.wikipedia.org/wiki/Cron#Cron_expression
# Reference 2: https://www.baeldung.com/cron-expressions
DAY_OF_MONTH_REGEX = r"\*|(?:[0-9]+W?|L|L-[0-9])(?:,(?:[0-9]+|L|L-[0-9]))*"
WEEKDAY_REGEX = (
    r"\*|"
    r"(?:[0-7]L|[0-7]#[1-5]|MON|TUE|WED|THU|FRI|SAT|SUN)"
    + r"(?:,(?:[0-7]L|[0-7]#[1-5]|MON|TUE|WED|THU|FRI|SAT|SUN))*"
)

PARAMETER_SECTION = "CONFIG"  # Configuration section name
JOB_PREFIX = "JOB:"  # Job section prefix
SERVER_PREFIX = "SERVER:"  # Server section prefix

LOG_FILE_PATH = Path("rpg.log")
LOG_FORMAT = "{asctime:s} {name:s} {levelname:>7s} {message:s}"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

COLOR_HIGH = co.Style.RESET_ALL + co.Style.BRIGHT + co.Fore.WHITE
COLOR_RESET = co.Style.RESET_ALL

# ----- CLASSES ---------------------------------------------------------------


class LogFormatter(logging.Formatter):
    """Custom log formatter class
    Formats log messages with a timestamp and log level
    """

    def __init__(self, fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT, style="{") -> None:
        """Initialize the log formatter

        Args:
            fmt (str): The log message format
            datefmt (str): The date format
            style (str): The format style
        """
        super().__init__(fmt, datefmt, style)  # type: ignore

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record

        Args:
            record (logging.LogRecord): The log record
        """
        record.asctime = self.formatTime(record, self.datefmt)
        return super().format(record)


class StreamHandler(logging.StreamHandler):
    """Custom stream handler class
    Displays messages in different colours based on severity
    """

    # Colour map for log levels
    color_map = {
        logging.DEBUG: co.Style.RESET_ALL + co.Style.BRIGHT + co.Fore.BLUE,
        logging.INFO: co.Style.RESET_ALL + co.Style.BRIGHT + co.Fore.GREEN,
        logging.WARNING: co.Style.RESET_ALL + co.Style.BRIGHT + co.Fore.YELLOW,
        logging.ERROR: co.Style.RESET_ALL + co.Style.BRIGHT + co.Fore.RED,
        logging.CRITICAL: co.Style.RESET_ALL
        + co.Style.BRIGHT
        + co.Fore.YELLOW
        + co.Back.RED,
    }

    def __init__(self):
        super().__init__()
        self.setLevel(logging.DEBUG)
        self.setFormatter(LogFormatter())
        co.init(convert=True)

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record

        Args:
            record (logging.LogRecord): The log record
        """
        color = self.color_map.get(record.levelno, COLOR_HIGH)
        try:
            message = self.format(record)
            print(color + message + COLOR_RESET)
        except Exception:  # pylint: disable=broad-exception-caught
            self.handleError(record)


class RPGLog(logging.Logger):
    """RPG Logger Class"""

    def __init__(self, name: str = "RPG", level: int = logging.DEBUG):
        """Initialize the RPG Logger

        Args:
            name (str): The logger name. Default is "RPG".
            level (int): The logging level. Default is logging.DEBUG.
        """

        super().__init__(name)
        self.setLevel(level)

        console_format = LogFormatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT, style="{")
        console_handler = StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(console_format)
        self.addHandler(console_handler)

        file_format = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT, style="{")
        file_handler = logging.FileHandler(
            filename=LOG_FILE_PATH, mode="a", encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_format)
        self.addHandler(file_handler)

        # TODO: Add an SMTP handler for email notifications of errors and crits
        # Reference: https://docs.python.org/3/library/logging.handlers.html#smtphandler

    def set_level(self, level: str) -> None:
        """Set the logging level

        Args:
            level (str): The logging level. 'debug', 'info', 'warning', 'error',
                or 'critical'.
        """
        level = getattr(logging, level.upper())
        self.setLevel(level)
        for handler in self.handlers:
            handler.setLevel(level)


# -----------------------------------------------------------------------------


class RPGConfig(ConfigParser):
    """RPG Configuration Class"""

    __cipher: Fernet
    log = RPGLog()

    def __init__(self):
        super().__init__()
        if CONFIG_FILE.exists():
            self.log.debug(f"Reading configuration from {CONFIG_FILE.name}")
            self.read(CONFIG_FILE, encoding="utf-8")

        # Create PARAMETER_SECTION if it does not exist
        if PARAMETER_SECTION not in self.sections():
            self.add_section(PARAMETER_SECTION)
            self.save()

        # Read the encryption key if it exists, or create a new one
        if KEY_FILE.exists():
            with open(KEY_FILE, "r", encoding="utf-8") as keyfile:
                key = keyfile.read()
                self.__cipher = Fernet(key.encode())
        else:
            # Generate a new key and save it to the file
            self.__cipher = Fernet(key := Fernet.generate_key())
            key = key.decode()
            with open(KEY_FILE, "w", encoding="utf-8") as keyfile:
                keyfile.write(key)
            self.log.info(f"Generated new encryption key in {KEY_FILE.name}")

        # Count jobs and servers
        job_count = len([s for s in self.sections() if s.startswith(JOB_PREFIX)])
        server_count = len([s for s in self.sections() if s.startswith(SERVER_PREFIX)])
        self.log.debug(
            f"Configuration contains {job_count} jobs and {server_count} servers"
        )

    def __str__(self) -> str:
        return f"RPGConfig({CONFIG_FILE.name})"

    # ----- Private Methods ---------------------------------------------------

    def __decrypt(self, value: str) -> str:
        """Decrypt a value if it is encrypted"""
        try:
            decrypted_value = self.__cipher.decrypt(value.encode()).decode()
        except InvalidToken as e:
            raise KeyError("Token cannot be decrypted with this key") from e
        return decrypted_value

    def __encrypt(self, value: str) -> str:
        """Encrypt a value"""
        return self.__cipher.encrypt(value.encode()).decode()

    # ----- Parameter Functions ------------------------------------------------

    def get_param(self, param: str, decrypt: bool = True) -> str:
        """Get a parameter value

        Args:
            param (str): The parameter name
            decrypt (bool): Decrypt the value? Default is True.

        Returns:
            str: The parameter value. Blank if it does not exist.
        """
        value = self.get(PARAMETER_SECTION, param, fallback="")
        if value.startswith(FERNET_PREFIX):
            value = self.__decrypt(value) if decrypt else "<encrypted>"
        return value

    def has_param(self, param: str) -> bool:
        """Determine if a parameter exists

        Args:
            param (str): The parameter name

        Returns:
            bool: True if the parameter exists
        """
        return self.has_option(PARAMETER_SECTION, param)

    def set_param(self, param: str, value: str, encrypt: bool = False) -> None:
        """Set a parameter value

        Args:
            param (str): The parameter name
            value (str): The parameter value
            encrypt (bool): Encrypt the value? Default is False.

        Note:
            The new value is automatically encrypted if the old value already is encrypted.
        """
        # Test if the previous vaslue is encrypted
        try:
            prev_value = self[PARAMETER_SECTION][param]
        except KeyError:
            prev_value = ""

        # Encrypt the value, if necessary
        if encrypt or prev_value.startswith(FERNET_PREFIX):
            value = self.__encrypt(value)
        self[PARAMETER_SECTION][param] = value
        self.save()

    # ----- Job Functions -----------------------------------------------------

    def delete_job(self, job_id: str) -> None:
        """Delete a job from the configuration

        Args:
            id (str): The job ID

        Raises:
            KeyError: If the job ID does not exist
        """
        job_id = job_id.upper()
        if not self.has_section(JOB_PREFIX + job_id):
            raise KeyError(f"Job ID '{job_id}' does not exist")
        self.remove_section(JOB_PREFIX + job_id)
        self.save()

    def get_job(self, job_id: str) -> tuple[bool, str, datetime, datetime]:
        """Get the job details for a given job ID

        Args:
            id (str): The job ID

        Returns:
            tuple: The job details as a tuple
                (is_due, day, last_run, next_run)

        Raises:
            KeyError: If the job ID does not exist
        """
        job_id = job_id.upper()
        if not self.has_section(JOB_PREFIX + job_id):
            raise KeyError(f"Job ID '{job_id}' does not exist")
        job = self[JOB_PREFIX + job_id]
        cron = job["cron"]
        # Split the cron expression into its components
        # (minute, hour, day, month, day of week)
        _, _, cron_day, _, cron_dow = cron.split()

        now = datetime.now()
        cron_iter = croniter(cron, now, hash_id=job_id)
        next_run = cron_iter.get_next(datetime)
        prev_run = cron_iter.get_prev(datetime)
        if last_run := job.get("last_run", None):
            last_run = datetime.strptime(last_run, "%Y-%m-%d %H:%M:%S")
            is_due = last_run < prev_run
        else:
            last_run = datetime.min
            is_due = True
        return is_due, cron_day if cron_day != "*" else cron_dow, last_run, next_run

    def get_job_day_text(self, job_id: str) -> str:
        """Get the day text for a given job ID

        Args:
            id (str): The job ID

        Returns:
            str: The day text
        """
        job_id = job_id.upper()
        if not self.has_section(JOB_PREFIX + job_id):
            raise KeyError(f"Job ID '{job_id}' does not exist")
        job = self[JOB_PREFIX + job_id]
        cron = job["cron"]
        # Split the cron expression into its components
        # (minute, hour, day, month, day of week)
        _, _, cron_day, _, cron_dow = cron.split()
        if cron_day not in {"*", "?"}:
            return day_of_month_to_text(cron_day)
        return weekday_to_text(cron_dow)

    def job_is_due(self, job_id: str) -> bool:
        """Determine if a job is due to run

        Args:
            id (str): The job ID

        Returns:
            bool: True if the job is due to run
        """
        job_id = job_id.upper()
        if not self.has_section(JOB_PREFIX + job_id):
            raise KeyError(f"Job ID '{job_id}' does not exist")
        return self.get_job(job_id)[0]

    def job_exists(self, job_id: str) -> bool:
        """Determine if a job exists

        Args:
            id (str): The job ID

        Returns:
            bool: True if the job exists
        """
        return self.has_section(JOB_PREFIX + job_id.upper())

    def reset_job(self, job_id: str) -> None:
        """Reset the last_run attribute of a job so that it is due to run
        at the next scheduled time

        Args:
            id (str): The job ID

        Raises:
            KeyError: If the job ID does not exist
        """
        job_id = job_id.upper()
        if not self.has_section(JOB_PREFIX + job_id):
            raise KeyError(f"Job ID '{job_id}' does not exist")
        self[JOB_PREFIX + job_id]["last_run"] = ""
        self.save()

    def run_job(self, job_id: str) -> int:
        """Update the last_run attribute of a job to the current time

        Args:
            id (str): The job ID

        Returns:
            int: The return code from the job execution

        Raises:
            KeyError: If the job ID does not exist
        """
        job_id = job_id.upper()
        if not self.has_section(JOB_PREFIX + job_id):
            raise KeyError(f"Job ID '{job_id}' does not exist")

        # TODO: Execute the job here
        now = datetime.now()
        self.set(JOB_PREFIX + job_id, "last_run", now.strftime("%Y-%m-%d %H:%M:%S"))
        self.save()
        return 0

    def set_job(self, job_id: str, day: str):
        """Set the job details for a given job ID

        Args:
            id (str): The job ID
            day (str): The day of the week to run the job

        Raises:
            ValueError: If the day specification is invalid
        """
        job_id = job_id.upper()
        if not self.has_section(JOB_PREFIX + job_id):
            self.add_section(JOB_PREFIX + job_id)

        day_of_month = day if re.fullmatch(DAY_OF_MONTH_REGEX, day) else "*"
        day_of_week = day if re.fullmatch(WEEKDAY_REGEX, day) else "*"
        cron = " ".join(["H", "H", day_of_month, "*", day_of_week])

        # Test via croniter if the cron string is valid
        now = datetime.now()
        try:
            _ = croniter(cron, now, hash_id=job_id)
        except ValueError as e:
            raise ValueError(f"Invalid day specification: {e}") from e

        self[JOB_PREFIX + job_id]["cron"] = cron
        self.save()

    # ----- Server Functions --------------------------------------------------

    def delete_server(self, job_id: str) -> None:
        """Delete a server from the configuration

        Args:
            id (str): The server ID

        Raises:
            KeyError: If the server ID does not exist
        """
        job_id = job_id.upper()
        if not self.has_section(SERVER_PREFIX + job_id):
            raise KeyError(f"Server ID '{job_id}' does not exist")
        self.remove_section(SERVER_PREFIX + job_id)
        self.save()

    def get_server(self, job_id: str) -> tuple[str, int, str, str, str]:
        """Get the server details for a given server ID

        Args:
            id (str): The server ID

        Returns:
            tuple[str, int, str, str, str]: The server details as a tuple
                (hostname, port, username, password, type)

        Raises:
            KeyError: If the server ID does not exist
        """
        job_id = job_id.upper()
        if not self.has_section(SERVER_PREFIX + job_id):
            raise KeyError(f"Server ID '{job_id}' does not exist")
        server = self[SERVER_PREFIX + job_id]
        return (
            server["address"],
            server.getint("port"),
            server["user"],
            self.__decrypt(server["password"]),
            server["type"].lower(),
        )

    def server_exists(self, job_id: str) -> bool:
        """Determine if a server exists

        Args:
            id (str): The server ID

        Returns:
            bool: True if the server exists
        """
        return self.has_section(SERVER_PREFIX + job_id.upper())

    def set_server(
        self,
        server_id: str,
        address: str | None = None,
        port: int | None = None,
        user: str | None = None,
        password: str | None = None,
        server_type: str | None = None,
    ) -> None:
        """Set the server details for a given server ID

        Args:
            id (str): The server ID
            address (str): The server address
            port (int): The server port
            user (str): The server username
            password (str): The server password
            server_type (str): The server type ("oracle", "mysql", or "api")
        """
        server_id = server_id.upper()
        if not self.has_section(SERVER_PREFIX + server_id):
            self.add_section(SERVER_PREFIX + server_id)

        server = self[SERVER_PREFIX + server_id]
        if address is not None:
            server["address"] = address
        if port is not None:
            server["port"] = str(port)
        if user is not None:
            server["user"] = user
        if password is not None:
            server["password"] = self.__encrypt(password)
        if server_type is not None:
            server["type"] = server_type.lower()
        self.save()

    # ----- Utility Functions -------------------------------------------------

    def jobs(self) -> list[str]:
        """Return the ids of all defined jobs"""
        result = []
        for section in self.sections():
            if section.startswith(JOB_PREFIX):
                job_id = section[len(JOB_PREFIX) :]
                result.append(job_id)
        return sorted(result)

    def parameters(self) -> list[str]:
        """Return all parameters as a dictionary"""
        return sorted(self[PARAMETER_SECTION])

    def servers(self) -> list[str]:
        """Return the ids of all defined servers"""
        result = []
        for section in self.sections():
            if section.startswith(SERVER_PREFIX):
                server_id = section[len(SERVER_PREFIX) :]
                result.append(server_id)
        return sorted(result)

    def save(self) -> None:
        """Write the current configuration to the file"""
        with open(CONFIG_FILE, "w", encoding="utf-8") as configfile:
            self.write(configfile)
        self.log.debug(f"Saved configuration to {CONFIG_FILE.name}")


# ----- MODULE LEVEL FUNCTIONS ------------------------------------------------


def day_of_month_to_text(day_of_month: str) -> str:
    """Convert a day expression to text

    Args:
        day (str): The day expression

    Returns:
        str: The text representation
    """
    if day_of_month in {"?", "*"}:
        return "day"
    if day_of_month == "L":
        return "Last day"
    if day_of_month.startswith("L"):
        return day_of_month[1:] + " day before last"
    if day_of_month.endswith("W"):
        return day_of_month[:-1] + "th weekday"
    if "," in day_of_month:
        return "Every " + ", ".join(day_of_month.split(","))
    if day_of_month.isdigit():
        if day_of_month.endswith("1") and day_of_month != "11":
            return day_of_month + "st"
        if day_of_month.endswith("2") and day_of_month != "12":
            return day_of_month + "nd"
        if day_of_month.endswith("3") and day_of_month != "13":
            return day_of_month + "rd"
        return day_of_month + "th"
    return f"¿{day_of_month}?"


def weekday_to_text(weekday: str) -> str:
    """Convert a weekday expression to text

    Args:
        weekday (str): The weekday expression

    Returns:
        str: The text representation
    """
    if "," in weekday:
        return ", ".join([weekday_to_text(d) for d in weekday.split(",")])
    if weekday in {"?", "*"}:
        return "weekday"
    if "#" in weekday:
        weekday_split = weekday.split("#")
        text = weekday_split[1]
        if text == "1":
            text += "st"
        elif text == "2":
            text += "nd"
        elif text == "3":
            text += "rd"
        else:
            text += "th"
        text += " " + weekday_to_text(weekday_split[0])
        text += " of the month"
        return text
    if weekday.endswith("L"):
        return "Last " + weekday_to_text(weekday[:-1]) + " of the month"
    WEEKDAY_MAP = {  # pylint: disable=invalid-name
        "MON": "Mon",
        "TUE": "Tue",
        "WED": "Wed",
        "THU": "Thu",
        "FRI": "Fri",
        "SAT": "Sat",
        "SUN": "Sun",
        "0": "Sun",
        "1": "Mon",
        "2": "Tue",
        "3": "Wed",
        "4": "Thu",
        "5": "Fri",
        "6": "Sat",
    }
    if weekday.upper() in WEEKDAY_MAP:
        return WEEKDAY_MAP[weekday.upper()]
    return f"¿{weekday}?"


# MAINLINE ENTRY POINT =========================================================
co.init(autoreset=True)
