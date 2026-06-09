# -*- coding: utf-8 -*-
import atexit
import itertools
import signal
import sys
from functools import wraps
from time import sleep, time
from typing import Callable, Dict, Iterable, Optional, Union

import click
from click import argument, option, pass_context
from kubernetes import client, config

wrapup_functors_ = []
global_flags_ = dict(stop=False)


def warpup_(*_, **kwargs) -> None:
    if global_flags_["stop"] or not wrapup_functors_:
        return
    global_flags_["stop"] = True
    for functor in wrapup_functors_:
        try:
            functor()
        except Exception as e:
            print(f"{functor.__name__}: {type(e)} {str(e)}")
    if not kwargs.get("no_exit_", False):
        sys.exit(0)


signal.signal(signal.SIGINT, warpup_)  # type: ignore
signal.signal(signal.SIGTERM, warpup_)  # type: ignore
atexit.register(warpup_, no_exit_=True)  # type: ignore


class K8sClient(object):
    @staticmethod
    def handle_api_exception(*args_, **kwargs_):
        def handle_api_exception_(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except client.ApiException as e:
                    if kwargs.get("print_err", True):
                        func_input = ",".join(
                            map(
                                str,
                                itertools.chain(
                                    args, (f"{k}={v}" for k, v in kwargs.items())
                                ),
                            )
                        )
                        click.echo(
                            f"{func.__name__}({func_input}): {type(e)}, {str(e)}",
                            err=True,
                        )
                    if kwargs.get("raise_exc"):
                        raise
                return kwargs_.get("default_return", None)

            return wrapper

        if kwargs_:
            return handle_api_exception_
        else:
            return handle_api_exception_(args_[0])

    @staticmethod
    def get_context_info(
        context: Optional[Union[str, Callable]] = None
    ) -> Optional[Dict]:
        ctx_list, active_ctx = config.list_kube_config_contexts()
        if not context:
            return active_ctx or {}
        for ctx in ctx_list:
            if callable(context):
                if context(ctx["name"]):
                    return ctx
            elif context == ctx["name"]:
                return ctx

    def __init__(
        self, context: Optional[str] = None, namespace: Optional[str] = None
    ) -> None:
        if context:
            try:
                config.load_kube_config(context=context)
                if not namespace and (ctx := self.get_context_info(context)):
                    namespace = ctx["context"].get("namespace")
            except config.ConfigException:
                config.load_kube_config()
                if ctx := self.get_context_info(lambda x: context in x):
                    context = ctx["name"]
                    config.load_kube_config(context=context)
                    if not namespace:
                        namespace = ctx["context"].get("namespace")
                else:
                    raise
        else:
            try:
                config.load_kube_config()
            except config.ConfigException:
                config.load_incluster_config()
            active_ctx = self.get_context_info()
            if not active_ctx:
                raise config.ConfigException("Default kubeconfig not found.")
            context = active_ctx["name"]
            if not namespace:
                namespace = active_ctx["context"].get("namespace")

        if not namespace:
            raise config.ConfigException(
                f"No default namespace is configured for {context=}."
            )

        self.context = context
        self.namespace = namespace
        self.core = client.CoreV1Api()
        # self.batch = client.BatchV1Api()
        self.custom = client.CustomObjectsApi()

    @handle_api_exception
    def get_pvc(self, name, **kwargs) -> Optional[client.V1PersistentVolumeClaim]:
        return self.core.read_namespaced_persistent_volume_claim(
            name=name, namespace=self.namespace
        )

    @handle_api_exception
    def delete_pvc(self, name) -> Optional[client.V1PersistentVolumeClaim]:
        return self.core.delete_namespaced_persistent_volume_claim(
            name=name, namespace=self.namespace
        )

    @handle_api_exception
    def create_pvc_from_volume_snapshot(
        self, name, snapshot_name, storage_class, storage_size, access_modes
    ) -> Optional[client.V1PersistentVolumeClaim]:
        pvc = client.V1PersistentVolumeClaim(
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1PersistentVolumeClaimSpec(
                access_modes=access_modes,
                resources=client.V1ResourceRequirements(
                    requests={"storage": storage_size}
                ),
                storage_class_name=storage_class,
                data_source=client.V1TypedLocalObjectReference(
                    api_group="snapshot.storage.k8s.io",
                    kind="VolumeSnapshot",
                    name=snapshot_name,
                ),
            ),
        )

        return self.core.create_namespaced_persistent_volume_claim(
            namespace=self.namespace, body=pvc
        )

    @handle_api_exception
    def get_volume_snapshot(self, name: str, **__) -> Optional[Dict]:
        resp = self.custom.get_namespaced_custom_object(
            group="snapshot.storage.k8s.io",
            version="v1",
            namespace=self.namespace,
            plural="volumesnapshots",
            name=name,
        )
        return resp

    @handle_api_exception
    def create_volume_snapshot(
        self, name: str, pvc_name: str, snapshot_class_name: str
    ) -> Optional[Dict]:
        body = {
            "apiVersion": "snapshot.storage.k8s.io/v1",
            "kind": "VolumeSnapshot",
            "metadata": {"name": name, "namespace": self.namespace},
            "spec": {
                "source": {"persistentVolumeClaimName": pvc_name},
                "volumeSnapshotClassName": snapshot_class_name,
            },
        }
        resp = self.custom.create_namespaced_custom_object(
            group="snapshot.storage.k8s.io",
            version="v1",
            namespace=self.namespace,
            plural="volumesnapshots",
            body=body,
        )

        return resp

    @handle_api_exception
    def delete_volume_snapshot(self, name: str) -> Optional[Dict]:
        resp = self.custom.delete_namespaced_custom_object(
            group="snapshot.storage.k8s.io",
            version="v1",
            namespace=self.namespace,
            plural="volumesnapshots",
            name=name,
        )
        return resp

    @handle_api_exception
    def get_pod(self, name) -> Optional[client.V1Pod]:
        return self.core.read_namespaced_pod(name, self.namespace)

    @handle_api_exception
    def delete_pod(self, name) -> Optional[client.V1Pod]:
        return self.core.delete_namespaced_pod(name, self.namespace)

    @handle_api_exception
    def create_pod_to_claim_pvc(self, pvc_name, **kwargs) -> Optional[client.V1Pod]:
        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(
                name=kwargs.get("name") or kwargs.get("pod_name"),
                generate_name=f"{pvc_name}-claimer-",
                annotations={"sidecar.istio.io/inject": "false"},
            ),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name="python-container",
                        image="python:3.12-slim",
                        command=["sleep", "infinity"],
                        volume_mounts=[
                            client.V1VolumeMount(
                                name="data-volume", mount_path="/usr/data"
                            )
                        ],
                    )
                ],
                volumes=[
                    client.V1Volume(
                        name="data-volume",
                        persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                            claim_name=pvc_name
                        ),
                    )
                ],
            ),
        )

        resp = self.core.create_namespaced_pod(namespace=self.namespace, body=pod)
        return resp

    @staticmethod
    def pod_ready(pod: Optional[client.V1Pod]) -> Optional[bool]:
        if pod:
            if pod.status.phase == "Running" and not pod.metadata.deletion_timestamp:
                for condition in pod.status.conditions or []:
                    if condition.type == "Ready" and condition.status == "True":
                        return True
            return False

    @handle_api_exception(default_return=[])
    def get_pods(
        self, pod_filter: Optional[Callable] = None, **kwargs
    ) -> Iterable[client.V1Pod]:
        pods = self.core.list_namespaced_pod(namespace=self.namespace, **kwargs).items
        if callable(pod_filter):
            return (pod for pod in filter(pod_filter, pods))
        return pods

    @handle_api_exception
    def get_volume_snapshot_class(self, name: str) -> Optional[Dict]:
        resp = self.custom.get_cluster_custom_object(
            group="snapshot.storage.k8s.io",
            version="v1",
            plural="volumesnapshotclasses",
            name=name,
        )
        return resp


@click.group()
@option("--context", default=None, help="K8s context")
@option("--namespace", default=None, help="K8s namespace")
@pass_context
def cli(ctx, **kwargs):
    """CLI tool to manage K8S resources."""
    ctx.ensure_object(dict)
    if ctx.invoked_subcommand and "-h" not in sys.argv and "--help" not in sys.argv:
        ctx.obj["k8s"] = k8s = K8sClient(
            **{k: v for k, v in kwargs.items() if k in ("context", "namespace")}
        )
        click.echo(f"Using k8s config: context={k8s.context}, namespace={k8s.namespace}")


@cli.command()
@argument("name")
@argument("pvc")
@argument("snapshot_class")
@option(
    "--wait",
    default=False,
    is_flag=True,
    help="Wait for snapshot to become ready for use",
)
@pass_context
def create_volume_snapshot(ctx, name, pvc, snapshot_class, **kwargs):
    """
    Create a volume snapshot of a persistent volume claim.

    Arguments:\n
        NAME                Destination VolumeSnapshot object's name.\n
        PVC                 Source PersistentVolumeClaim object's name.\n
        SNAPSHOT_CLASS      VolumeSnapshotClass object's name.\n
    """
    k8s = ctx.obj["k8s"]
    if pvc_obj := k8s.get_pvc(pvc):
        if pvc_obj.status.phase != "Bound":
            click.echo(f"=> PVC {pvc} is not yet bounded to any PV.")
            sys.exit(1)
    else:
        click.echo(f"=> PVC {pvc} does not exist.", err=True)
        sys.exit(1)
    resp = k8s.create_volume_snapshot(name, pvc, snapshot_class)
    if resp:
        click.echo(f"=> Created volume snapshot {name} from PVC {pvc}.")
    else:
        click.echo(
            f"=> Failed to create volume snapshot {name} from PVC {pvc}.", err=True
        )
        sys.exit(1)
    if kwargs["wait"]:
        last_ts = time()
        while not global_flags_["stop"] and not (
            resp := k8s.get_volume_snapshot(name) or {}
        ).get("status", {}).get("readyToUse", False):
            if not resp:
                click.echo(f"=> Fatal error with volume snapshot {name}", err=True)
                sys.exit(1)
            click.echo(
                f"=> Waiting for the snapshot {name} getting ready ... {int(time() - last_ts)}s elapsed\r",
                nl=False,
            )
            sleep(1)
        click.echo()
        click.echo(f"=> Done. Volume snapshot {name} is ready to use.")


def resolve_pvc_conflict_(
    k8s: K8sClient,
    new_pvc: client.V1PersistentVolumeClaim,
    override: Optional[bool] = None,
    **kwargs,
) -> bool:
    if new_pvc:
        pvc_name = new_pvc.metadata.name
        if override:
            if new_pvc.status.phase == "Bound":
                field_selector = "status.phase!=Succeeded,status.phase!=Failed"
                dest_pvc_node = (new_pvc.metadata.annotations or {}).get(
                    "volume.kubernetes.io/selected-node"
                )
                if dest_pvc_node:
                    field_selector += f",spec.nodeName=={dest_pvc_node}"
                for pod in k8s.get_pods(field_selector=field_selector):
                    for volume in pod.spec.volumes or []:
                        if (
                            volume.persistent_volume_claim
                            and volume.persistent_volume_claim.claim_name == pvc_name
                        ):
                            click.echo(
                                f"=> PVC '{pvc_name}' is currently in use by Pod '{pod.metadata.name}'.",
                                err=True,
                            )
                            return False
            if k8s.delete_pvc(pvc_name):
                last_ts = time()
                while not global_flags_["stop"]:
                    click.echo(
                        f"=> Deleting old PVC {pvc_name}  ... {int(time() - last_ts)}s elapsed\r",
                        nl=False,
                    )
                    sleep(1)
                    if not k8s.get_pvc(pvc_name, print_err=False):
                        click.echo(f"=> Old PVC {pvc_name} deleted.")
                        return True
            else:
                click.echo(f"=> Failed to delete old PVC {pvc_name}.", err=True)
                return False
        else:
            click.echo(
                f"=> PVC {pvc_name} already exists. {kwargs.get('usage_hint_', '')}".strip(),
                err=True,
            )
            return False
    else:
        return True
    return False


@cli.command()
@argument("snapshot")
@argument("storage_class")
@option(
    "--name",
    default=None,
    help="Name of the resulting PVC. The name of the snapshot's source PVC will be used by default.",
)
@option(
    "--storage_size",
    default=None,
    help="Request storage size of the resulting PVC, e.g. 8Gi. The snapshot's size will be used by default.",
)
@option(
    "--access_modes",
    default=["ReadWriteOnce"],
    show_default=True,
    help="Comma-separated list of access modes.",
    callback=lambda ctx, param, value: (
        [v.strip() for v in value.split(",")] if value else []
    ),
    type=list,
)
@option(
    "--override",
    default=False,
    is_flag=True,
    help="Override the existing PVC with the same name.",
)
@option(
    "--claim", default=False, is_flag=True, help="Claim an accordant persistent volume."
)
@pass_context
def restore_persistent_volume_claim(ctx, snapshot, storage_class, **kwargs):
    """
    Restore a PVC from a volume snapshot.

    Arguments:\n
        SNAPSHOT            Source VolumeSnapshot object's name.\n
        STORAGE_CLASS       Storage class name of the resulting PVC.\n
    """
    k8s = ctx.obj["k8s"]
    snapshot_info = k8s.get_volume_snapshot(snapshot)
    if not snapshot_info:
        click.echo(f"=> Snapshot {snapshot} not found", err=True)
        sys.exit(1)
    if not snapshot_info.get("status", {}).get("readyToUse", False):
        click.echo(f"=> Snapshot {snapshot} is not ready to use", err=True)
        sys.exit(1)

    source_pvc_name = snapshot_info["spec"]["source"]["persistentVolumeClaimName"]
    dest_pvc_name = kwargs["name"] or source_pvc_name
    dest_pvc = k8s.get_pvc(dest_pvc_name, print_err=False)
    if not resolve_pvc_conflict_(
        k8s,
        new_pvc=dest_pvc,
        override=kwargs["override"],
        usage_hint_="Please rerun and either specify --override flag or provide a unique name with --name option.",
    ):
        sys.exit(1)

    dest_pvc = k8s.create_pvc_from_volume_snapshot(
        name=dest_pvc_name,
        snapshot_name=snapshot,
        storage_class=storage_class,
        storage_size=kwargs["storage_size"] or snapshot_info["status"]["restoreSize"],
        access_modes=kwargs["access_modes"],
    )
    if not dest_pvc:
        click.echo(
            f"=> Failed to restore PVC {dest_pvc_name} from snapshot {snapshot}.",
            err=True,
        )
        sys.exit(1)
    click.echo(f"=> OK. Restored PVC {dest_pvc_name} from snapshot {snapshot}.")

    if kwargs["claim"]:
        pod = k8s.create_pod_to_claim_pvc(pvc_name=dest_pvc_name)
        if not pod:
            click.echo(f"=> Failed to claim PVC {dest_pvc_name}", err=True)
            sys.exit(1)

        claim_pod_name = pod.metadata.name

        def delete_claim_pod():
            k8s_ = K8sClient(context=k8s.context, namespace=k8s.namespace)
            if not k8s_.delete_pod(claim_pod_name):
                click.echo(
                    f"=> Failed to delete temporary pod {claim_pod_name}", err=True
                )

        wrapup_functors_.append(delete_claim_pod)

        last_ts = time()
        while not global_flags_["stop"] and not k8s.pod_ready(
            k8s.get_pod(claim_pod_name)
        ):
            click.echo(
                f"=> Claiming PVC {dest_pvc_name}  ... {int(time() - last_ts)}s elapsed\r",
                nl=False,
            )
            sleep(1)
        click.echo()
        if (
            dest_pvc := k8s.get_pvc(dest_pvc_name)
        ) and dest_pvc.status.phase == "Bound":
            click.echo(
                f"=> OK. PVC {dest_pvc_name} is successfully claimed with new PV {dest_pvc.spec.volume_name}"
            )
        else:
            click.echo(f"=> Failed to claim PVC {dest_pvc_name}.", err=True)
            sys.exit(1)


@cli.command()
@argument("source_pvc")
@argument("dest_pvc")
@option(
    "--storage_size",
    default=None,
    help="New storage size for the destination PVC, e.g. 8Gi.",
)
@option(
    "--storage_class",
    default=None,
    help="New storage class for the destination PVC.",
)
@option(
    "--snapshot_class",
    default="csi-aws-vsc",
    show_default=True,
    help="VolumeSnapshotClass object's name used to create the intermediary snapshot.",
)
@option(
    "--override",
    default=False,
    is_flag=True,
    help="Override the destination PVC if already exists.",
)
@pass_context
def copy_pvc(ctx, source_pvc, dest_pvc, **kwargs):
    """
    Copy PVC by restoring destination PVC via an intermediary snapshot created from source PVC.

    Arguments:\n
        SOURCE_PVC      Source PVC name.\n
        DEST_PVC        Destination PVC name.\n
    """
    k8s = ctx.obj["k8s"]
    source_pvc = source_pvc.lower()
    dest_pvc = dest_pvc.lower()

    source_pvc_obj = k8s.get_pvc(source_pvc)
    if not source_pvc_obj:
        click.echo(f"=> Source PVC {source_pvc} does not exist.")
        sys.exit(1)

    updatable_fields = ("storage_size", "storage_class")
    old_data = dict(
        storage_size=source_pvc_obj.spec.resources.requests.get("storage", None),
        storage_class=source_pvc_obj.spec.storage_class_name,
        access_modes=source_pvc_obj.spec.access_modes,
    )
    override_hint_ = (
        "Please rerun and either specify --override flag or provide a unique DEST_PVC."
    )
    if source_pvc == dest_pvc:
        if not any((kwargs[f] and kwargs[f] != old_data[f] for f in updatable_fields)):
            click.echo(f"=> No change for the PVC {source_pvc}.")
            sys.exit(0)
        if not kwargs["override"]:
            click.echo(f"=> PVC {source_pvc} exists. {override_hint_}")
            sys.exit(0)

    if not k8s.get_volume_snapshot_class(kwargs["snapshot_class"]):
        click.echo(
            f"=> VolumeSnapshotClass {kwargs['snapshot_class']} does not exist. "
            f"You might want to specify another one via --snapshot_class option",
            err=True,
        )
        sys.exit(1)

    snapshot_name = f"{source_pvc}-{str(time()).replace('.', '-')}"

    def delete_intermediary_snapshot():
        k8s_ = K8sClient(context=k8s.context, namespace=k8s.namespace)
        if not k8s_.delete_volume_snapshot(snapshot_name):
            click.echo(
                f"=> Failed to delete the intermediary volume snapshot {snapshot_name}",
                err=True,
            )

    if source_pvc != dest_pvc:
        wrapup_functors_.append(delete_intermediary_snapshot)

        dest_pvc_obj = k8s.get_pvc(dest_pvc, print_err=False)
        if not resolve_pvc_conflict_(
            k8s,
            new_pvc=dest_pvc_obj,
            override=kwargs["override"],
            usage_hint_=override_hint_,
        ):
            sys.exit(1)

    ctx.invoke(
        create_volume_snapshot,
        name=snapshot_name,
        pvc=source_pvc,
        snapshot_class=kwargs["snapshot_class"],
        wait=True,
    )

    try:
        ctx.invoke(
            restore_persistent_volume_claim,
            name=dest_pvc,
            snapshot=snapshot_name,
            storage_class=kwargs["storage_class"]
            or source_pvc_obj.spec.storage_class_name,
            storage_size=kwargs["storage_size"],
            access_modes=source_pvc_obj.spec.access_modes,
            override=kwargs["override"],
            claim=True,
        )
    except:
        if source_pvc == dest_pvc:
            click.echo(
                f"=> Failed to update PVC {source_pvc}. "
                f"Volume snapshot {snapshot_name} is reserved for manual inspections."
            )
            if not k8s.get_pvc(source_pvc, print_err=False):
                click.echo(f"=> Try to restore PVC {source_pvc} ...")
                try:
                    ctx.invoke(
                        restore_persistent_volume_claim,
                        name=source_pvc,
                        snapshot=snapshot_name,
                        storage_class=old_data["storage_class"],
                        storage_size=old_data["storage_size"],
                        access_modes=old_data["access_modes"],
                        override=False,
                        claim=True,
                    )
                except:
                    click.echo(f"=> Failed to restore PVC {source_pvc}.", err=True)
        raise

    if source_pvc == dest_pvc:
        wrapup_functors_.append(delete_intermediary_snapshot)
        click.echo(f"=> Done update PVC {source_pvc}.")
    else:
        click.echo(f"=> Done copy: PVC {source_pvc} -> PVC {dest_pvc}.")


if __name__ == "__main__":
    cli()
