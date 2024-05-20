__all__ = [
    "get_settings",
]

import abc
import warnings
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path
from ssl import SSLContext
from typing import Annotated, Final, Generic, Literal, NotRequired, Self, TypedDict, TypeVar

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, HttpUrl, PostgresDsn, RedisDsn, computed_field, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


ConnType = TypeVar("ConnType")
"""Type for `CONN_STR` in classes inherited from generic `DBConnection`."""


class DBConnection(BaseModel, Generic[ConnType], abc.ABC):
    """
    This abstract base model class represents a generic database connection.

    It is designed to be inherited by subclasses that represent specific database connections.

    Subclasses must implement the `_assemble_conn_str_value` method to generate the necessary connection string
    representation for a specific database type.

    Attributes:
        USERNAME (str | None): The username for the database connection.
        PASSWORD (str | None): The password for the database connection.
        HOST (str | None): The host for the database connection.
        PORT (str | None): The port for the database connection.
        DATABASE (str | None): The specific database to connect to.
        CONN_STR (Annotated[str, ConnType]): The connection string, assembled from the other properties.
    """

    USERNAME: str | None = None
    PASSWORD: str | None = None
    HOST: str | None = None
    PORT: int | None = None
    DATABASE: str | None = None

    @computed_field  # type: ignore[misc]
    @property
    def CONN_STR(self: Self) -> Annotated[str, ConnType]:  # noqa: N802 # Keep field naming style
        """
        The connection string, assembled from the other properties.

        This attribute is computed by calling the `_assemble_conn_str_value` method.

        Returns:
            The connection string, assembled from the other properties.
        """
        return str(self._assemble_conn_str_value())

    @abc.abstractmethod
    def _assemble_conn_str_value(self: Self) -> ConnType:
        """
        Abstract method that subclasses must implement to generate a connection string representation.

        Arguments:
            self (Self): A reference to the instance of a subclass that this method will be called on.

        Returns:
            ConnType: A connection string that can be directly used by the specific type of database client
                to create a connection with the database.
        """
        ...


class OpenSearchConnectionDict(TypedDict, total=False):
    """
    This `TypedDict` subclass represents the dictionary of connection parameters needed for an OpenSearch connection.

    It is used in the `CONN_DICT` attribute of an `OpenSearchNoCertConnection` instance after being processed in
    `assemble_conn_dict` method.

    This dict establishes details about hosts, authentication, scheme, port, and SSL context, which all will be used to
    configure and establish the OpenSearch connection.
    """

    hosts: Sequence[str]
    http_auth: tuple[str, str] | None
    scheme: Literal["http", "https"]
    port: str

    ssl_context: NotRequired[SSLContext]
    timeout: NotRequired[int]
    max_retries: NotRequired[int]
    retry_on_timeout: NotRequired[bool]


class OpenSearchNoCertConnection(DBConnection[AnyHttpUrl]):
    """
    Represents an OpenSearch connection without requiring SSL certification.

    Attributes:
        SCHEME (Literal["http", "https"]): The scheme for this connection, either "http" or "https".
        USERNAME (str): The username for the OpenSearch service.
        PASSWORD (str): The password for the OpenSearch service.
        HOST (str): The host of the OpenSearch service.
        PORT (int): The port of the OpenSearch service.
        TTL (int): [Optional] The duration after which the connection times out. Default is 60.
        MAX_RETRIES (int): [Optional] The maximum number of times the request to the connection can be retried.
            Default is 10.
        RETRY_ON_TIMEOUT (bool): [Optional] If true, retries occur on timed-out connections. Default is True.
        CONN_DICT (OpenSearchConnectionDict): After being processed in `assemble_conn_dict`, this dict contains
                                                details about host, authentication, connectivity, and SSL context.

        CONN_STR (str): The connection string for the OpenSearch service, assembled from,
                                        assembled from the other properties.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    SCHEME: Literal["http", "https"]
    USERNAME: str
    PASSWORD: str
    HOST: str
    PORT: int

    TTL: int = 60
    MAX_RETRIES: int = 10
    RETRY_ON_TIMEOUT: bool = True

    @computed_field  # type: ignore[misc]
    @property
    def CONN_DICT(self: Self) -> OpenSearchConnectionDict:  # noqa: N802 # Keep field naming style
        """
        Returns dict with OpenSearch connection parameters,
        including host, scheme, port, authentication, and SSL context.

        Warns:
            ImportWarning: When opensearch-py is not installed, therefore the ssl_context can't be added.

        Returns:
            OpenSearchConnectionDict: The connection dictionary.
        """
        conn_dict = OpenSearchConnectionDict(
            hosts=(self.HOST,),
            http_auth=(self.USERNAME, self.PASSWORD) if self.USERNAME else None,
            scheme=self.SCHEME,
            port=str(self.PORT),
            timeout=self.TTL,
            max_retries=self.MAX_RETRIES,
            retry_on_timeout=self.RETRY_ON_TIMEOUT,
        )

        import ssl

        try:
            from opensearchpy.connection import create_ssl_context
        except ImportError:
            msg = "Can't add SSL context to OpenSearch Connection Dict. Make sure that opensearch-py is installed."
            warnings.warn(msg, ImportWarning, stacklevel=1)
            return conn_dict

        ssl_context = create_ssl_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        conn_dict["ssl_context"] = ssl_context
        return conn_dict

    def _assemble_conn_str_value(self: Self) -> AnyHttpUrl:
        """
        Assembles a connection string representation for an OpenSearch connection.

        Arguments:
            self (Self): A reference to the instance of `OpenSearchNoCertConnection` that this method will be called on.

        Returns:
            AnyHttpUrl: A Pydantic Http URL model (`AnyHttpUrl`) that represents the connection string.
        """
        return AnyHttpUrl.build(
            scheme=self.SCHEME,
            username=self.USERNAME,
            password=self.PASSWORD,
            host=self.HOST,
            port=self.PORT,
        )


class PostgresConnection(DBConnection[PostgresDsn]):
    """
    Represents a connection to a Postgres database.

    Attributes:
        USERNAME (str): The username for the Postgres database.
        PASSWORD (str): The password for the Postgres database.
        HOST (str): The host of the Postgres database.
        PORT (int): [Optional] The port of the Postgres database. Default is 5432.
        DATABASE (str): The name of the Postgres database.

        CONN_STR (str): The connection string for the Postgres database, assembled from the
                                       other properties.
    """

    USERNAME: str
    PASSWORD: str
    HOST: str
    PORT: int = 5432
    DATABASE: str

    def _assemble_conn_str_value(self: Self) -> PostgresDsn:
        """
        Assembles a connection string representation for a Postgres database connection.

        Arguments:
            self (Self): A reference to the instance of PostgresConnection that this method will be called on.

        Returns:
            PostgresDsn: A Pydantic Postgres DSN model that represents the connection string.
        """
        return PostgresDsn.build(
            scheme="postgresql",
            username=self.USERNAME,
            password=self.PASSWORD,
            host=self.HOST,
            port=self.PORT,
            path=self.DATABASE or "",
        )


class RedisConnection(DBConnection[RedisDsn]):
    """
    Represents a Redis database connection string.

    Attributes:
        PASSWORD (str): The password for the Redis database.
        HOST (str): The host of the Redis database.
        PORT (int): [Optional] The port for the Redis database. Default is 6379.
        DATABASE (str): [Optional] The database index for the Redis database. Default is "0".
        USE_SSL (bool): [Optional] If true, the Redis service is assumed to use SSL. Default is True.

        CONN_STR (str): The connection string for the Redis service, assembled from the other properties.
    """

    PASSWORD: str | None = None
    HOST: str
    PORT: int = 6379
    DATABASE: str = "0"

    USE_SSL: bool = True

    def _assemble_conn_str_value(self: Self) -> RedisDsn:
        """
        Assembles a connection string representation for a Redis database connection.

        Arguments:
            self (Self): A reference to the instance of RedisConnection that this method will be called on.

        Returns:
            RedisDsn: A Pydantic Redis DSN model that represents the connection string.
        """
        scheme = "rediss" if self.USE_SSL else "redis"
        return RedisDsn.build(
            scheme=scheme,
            password=self.PASSWORD,
            host=self.HOST.split("://")[-1],
            port=self.PORT,
            path=self.DATABASE or "",
        )


class User(BaseModel):
    EMAIL: EmailStr
    PASSWORD: str


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).parent.parent / ".env", env_nested_delimiter="__")
    POSTGRES: PostgresConnection
    SUPERUSER: User


@lru_cache
def get_settings() -> Config:
    return Config()  # type: ignore[call-arg] # args added automatically by pydantic
