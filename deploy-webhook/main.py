import os
import logging
from typing import Optional

import docker
import docker.types
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Deploy Webhook")
security = HTTPBearer()

DEPLOY_SECRET = os.environ["DEPLOY_SECRET"]
KNOWN_SERVICES = [
    s.strip()
    for s in os.environ.get(
        "KNOWN_SERVICES", "llm-manager,image-server,tts-server,gaming-dashboard"
    ).split(",")
    if s.strip()
]


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != DEPLOY_SECRET:
        raise HTTPException(status_code=401, detail="Invalid token")


class DeployRequest(BaseModel):
    service: Optional[str] = None  # None = all known services


@app.get("/health")
async def health():
    return {"status": "ok", "known_services": KNOWN_SERVICES}


@app.post("/deploy")
async def deploy(
    req: DeployRequest,
    bg: BackgroundTasks,
    _=Depends(verify_token),
):
    services = [req.service] if req.service else KNOWN_SERVICES
    invalid = [s for s in services if s not in KNOWN_SERVICES]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unknown services: {invalid}")
    bg.add_task(do_deploy, services)
    return {"status": "deploying", "services": services}


def do_deploy(services: list[str]):
    client = docker.from_env()
    for name in services:
        try:
            redeploy(client, name)
        except Exception as e:
            logger.error(f"{name}: deploy failed — {e}")


def redeploy(client: docker.DockerClient, name: str):
    logger.info(f"[{name}] starting redeploy")

    try:
        container = client.containers.get(name)
    except docker.errors.NotFound:
        logger.warning(f"[{name}] container not found, skipping")
        return

    attrs = container.attrs
    image_ref = attrs["Config"]["Image"]
    env = attrs["Config"].get("Env") or []
    labels = attrs["Config"].get("Labels") or {}
    networks = attrs.get("NetworkSettings", {}).get("Networks", {})
    hc_raw = attrs["HostConfig"]

    # Pull new image
    logger.info(f"[{name}] pulling {image_ref}")
    client.images.pull(image_ref)

    # Build DeviceRequests (GPU reservations)
    device_requests = [
        docker.types.DeviceRequest(
            driver=dr.get("Driver", ""),
            count=dr.get("Count", 0),
            device_ids=dr.get("DeviceIDs"),
            capabilities=dr.get("Capabilities"),
        )
        for dr in (hc_raw.get("DeviceRequests") or [])
    ]

    host_config = client.api.create_host_config(
        restart_policy=hc_raw.get("RestartPolicy"),
        binds=hc_raw.get("Binds") or [],
        port_bindings=hc_raw.get("PortBindings") or {},
        device_requests=device_requests or None,
        network_mode=hc_raw.get("NetworkMode"),
    )

    # Stop and remove old container
    logger.info(f"[{name}] stopping")
    container.stop(timeout=30)
    container.remove()

    # Recreate
    logger.info(f"[{name}] recreating")
    response = client.api.create_container(
        image=image_ref,
        name=name,
        environment=env,
        labels=labels,
        host_config=host_config,
    )
    cid = response["Id"]

    # Reconnect to non-default networks
    network_mode = hc_raw.get("NetworkMode", "")
    for net_name in networks:
        if net_name not in ("bridge", network_mode):
            try:
                client.api.connect_container_to_network(cid, net_name)
            except Exception as e:
                logger.warning(f"[{name}] network {net_name}: {e}")

    client.api.start(cid)
    logger.info(f"[{name}] redeployed successfully")
