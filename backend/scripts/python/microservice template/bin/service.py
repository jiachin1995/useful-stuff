# -*- coding: utf-8 -*-

import os
import signal
import atexit

from click import group, option
from grpc_tools import protoc  # type: ignore

from myservice.config import logger
from myservice import MyService, MyService2, MyService3


PID_FILE = os.path.join(os.path.dirname(__file__), "myservice.pid")
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))

if "PYTEST_CURRENT_TEST" in os.environ:
    del os.environ["PYTEST_CURRENT_TEST"]


def del_pid_file():
    if os.path.exists(PID_FILE):
        logger.info(f"!!!Remove {PID_FILE}")
        os.remove(PID_FILE)


def generate_grpc(source_path: str):
    from myservice.config import BASE_DIR

    logger.info(f"Generating gRPC code to {BASE_DIR} from {source_path}")
    for file in ["my_proto1.proto", "my_proto2.proto", "my_proto3.proto", "my_proto4.proto"]:
        cmd = [
            "grpc_tools.protoc",
            f'--proto_path={os.path.join(source_path, "proto")}',
            f"--python_out={BASE_DIR}",
            f"--grpc_python_out={BASE_DIR}",
            file,
        ]
        if protoc.main(cmd):
            logger.error(f"Failed to generate gRPC code, {file}")


@group()
def cli():
    pass


@cli.command()  # type: ignore
@option("--source_path", "-s", default=ROOT_DIR)
def gen_grpc(source_path):
    generate_grpc(source_path)


@cli.command()  # type: ignore
def start():
    from myservice.config import DEBUG

    logger.info("STARTING myservice ...\n")

    with open(PID_FILE, "wt+") as f:
        logger.info("Write master pid %s" % os.getpid())
        f.write(str(os.getpid()) + "\n")

    # update gRPC code
    generate_grpc(ROOT_DIR)

    update_counter = os.environ.get("UPDATE_COUNTER", "0") == "1"
    collect_data = os.environ.get("COLLECT_DATA", "0") == "1"
    clean_data = os.environ.get("CLEAN_DATA", "0") == "1"

    if DEBUG:
        from myservice.config import NOTIFIER, QUERY_CONFIG

        logger.debug(f"Tasks: update_counter {update_counter}, collect_data {collect_data}, clean_data {clean_data}")
        logger.debug(f"Notifier setting: {str(NOTIFIER)}")
        logger.debug(f"Query setting: {str(QUERY_CONFIG)}")
        # logger.debug(f'SQLAlchemy dashboard: {SQLALCHEMY_CONFIG["dashboard_link"].format(**SQLALCHEMY_CONFIG)}')
        # logger.debug(f'SQLAlchemy gateway: {SQLALCHEMY_CONFIG["gateway_link"].format(**SQLALCHEMY_CONFIG)}')

    services = tuple()
    if update_counter:
        services += (MyService3(),)
    if collect_data:
        services += (MyService(),)
    if clean_data:
        services += (MyService2(),)
    for srv in services:
        srv.process_tasks()

    logger.info("\nmyservice STOPED.")


@cli.command()  # type: ignore
def stop():
    # GracefulServerStopper
    if not os.path.exists(PID_FILE):
        logger.warning(f"PID file does not exist: {PID_FILE}")
        return

    with open(PID_FILE, "rt") as f:
        pid = f.readline().strip()
        logger.info(f"Read master pid {pid}")
        pid = int(pid)
        os.kill(pid, signal.SIGHUP)

    atexit.register(del_pid_file)
    return


if __name__ == "__main__":
    cli()  # type: ignore
