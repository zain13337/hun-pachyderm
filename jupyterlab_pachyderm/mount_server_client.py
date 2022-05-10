import os
import subprocess
import time
import platform
from base64 import b64decode

import python_pachyderm
from python_pachyderm.service import health_proto
from tornado.httpclient import AsyncHTTPClient
from tornado import locks

from .pachyderm import MountInterface
from .log import get_logger

lock = locks.Lock()
MOUNT_SERVER_PORT = 9002
PACH_CONFIG = "~/.pachyderm/config.json"


class MountServerClient(MountInterface):
    """Client interface for the pachctl mount-server backend."""

    def __init__(
        self,
        mount_dir: str,
    ):
        self.client = AsyncHTTPClient()
        self.mount_dir = mount_dir
        self.address = f"http://localhost:{MOUNT_SERVER_PORT}"


    def _is_endpoint_valid(self, pachd_address, **kwargs):
        """Returns if a pachd_address points to a valid cluster."""
        get_logger().debug(f"Checking if valid pachd_address: {pachd_address}")
        
        if "server_cas" not in kwargs:
            client = python_pachyderm.Client.new_from_pachd_address(pachd_address)
        else:
            client = python_pachyderm.Client.new_from_pachd_address(
                pachd_address,
                root_certs=b64decode(bytes(kwargs["server_cas"], "utf-8"))
            )

        get_logger().info("Successfully initialized client")
        get_logger().info(client.health_check())
        try:
            res = client.health_check()
            if res.status != health_proto.HealthCheckResponse.ServingStatus.SERVING:
                raise ValueError()
        except Exception:
            return False
        
        return True


    async def _is_mount_server_running(self):
        get_logger().debug("Checking if mount server running...")
        try:
            await self.client.fetch(f"{self.address}/config")
        except Exception as e:
            get_logger().debug(f"Unable to hit server at {self.address}")
            get_logger().debug(e)
            return False
        get_logger().debug(f"Able to hit server at {self.address}")
        return True

    
    def _unmount(self):
        if platform.system() == "Linux":
            subprocess.run(["bash", "-c", f"fusermount -uzq {self.mount_dir}"])
        else:
            subprocess.run(
                ["bash", "-c", f"umount {self.mount_dir}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )


    def _update_config_file(self, pachd_address, **kwargs):
        # Update config file with new pachd_address
        get_logger().debug(f"Updating config file with pachd_address: {pachd_address}")  
        os.makedirs(os.path.expanduser("~/.pachyderm"), exist_ok=True)

        new_config = f'"pachd_address": "{pachd_address}"'
        if "server_cas" in kwargs:
            new_config += f', "server_cas": "{kwargs["server_cas"]}"'

        subprocess.run(
            ["bash", "-c", "pachctl config set context mount-server --overwrite"],
            text=True,
            input=f"{{{new_config}}}",
            env={
                "PACH_CONFIG": os.path.expanduser(PACH_CONFIG)
            }
        )
        subprocess.run(
            ["bash", "-c", "pachctl config set active-context mount-server"],
            env={
                "PACH_CONFIG": os.path.expanduser(PACH_CONFIG)
            }
        )
        get_logger().info(f"Updated config cluster endpoint to {pachd_address}")


    async def _ensure_mount_server(self):
        """
        When we first start up, we might not have auth configured. So just try
        re-launching the mount-server on every command! If the port is already
        bound, it will exit straight away. If it's not, it might start up
        successfully with the updated config.
        """
        # TODO: add --socket and --log-file stdout args
        # TODO: add better error handling        
        if await self._is_mount_server_running():
            return True

        get_logger().info("Starting mount server...")
        async with lock:
            if not await self._is_mount_server_running():                
                self._unmount()
                subprocess.Popen(
                    [
                        "bash", "-c",
                        "set -o pipefail; "
                        +f"pachctl mount-server --mount-dir {self.mount_dir}"
                        +" >> /tmp/pachctl-mount-server.log 2>&1",
                    ],
                    env={
                        "KUBECONFIG": os.path.expanduser('~/.kube/config'),
                        "PACH_CONFIG": os.path.expanduser(PACH_CONFIG),
                    }
                )
                
                tries = 0
                get_logger().debug("Waiting for mount server...")
                while not await self._is_mount_server_running():
                    time.sleep(1)
                    tries += 1

                    if tries == 10:
                        get_logger().debug("Unable to start mount server...")
                        return False

        return True


    async def list(self):
        await self._ensure_mount_server()
        response = await self.client.fetch(f"{self.address}/repos")
        return response.body
        

    async def mount(self, repo, branch, mode, name):
        await self._ensure_mount_server()
        response = await self.client.fetch(
            f"{self.address}/repos/{repo}/{branch}/_mount?name={name}&mode={mode}",
            method="PUT",
            body="{}",
        )
        return response.body

    async def unmount(self, repo, branch, name):
        await self._ensure_mount_server()
        response = await self.client.fetch(
            f"{self.address}/repos/{repo}/{branch}/_unmount?name={name}",
            method="PUT",
            body="{}",
        )
        return response.body

    async def unmount_all(self):
        await self._ensure_mount_server()
        response = await self.client.fetch(
            f"{self.address}/repos/_unmount",
            method="PUT",
            body="{}"
        )
        return response.body

    async def commit(self, repo, branch, name, message):
        await self._ensure_mount_server()
        pass

    async def config(self, request=None):
        if request is not None:
            if not self._is_endpoint_valid(**request):
                return {"cluster_status": "INVALID", **request}

            self._update_config_file(**request)
            self._unmount()
        
        if await self._ensure_mount_server():
            response = await self.client.fetch(f"{self.address}/config")
            return response.body
        
        return {"cluster_status": "INVALID"}

    async def auth_login(self):
        await self._ensure_mount_server()
        response = await self.client.fetch(f"{self.address}/auth/_login", method="PUT", body="{}")
        return response.body

    async def auth_logout(self):
        await self._ensure_mount_server()
        return await self.client.fetch(f"{self.address}/auth/_logout", method="PUT", body="{}")
