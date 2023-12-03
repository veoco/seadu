from asyncio import Queue, create_task, gather
from pathlib import Path
from datetime import datetime

from aiohttp import ClientSession
from tqdm.asyncio import tqdm

from .common import Item


class Downloader:
    def __init__(self, server_url: str, token: str, base_dir: Path, multi: int):
        self.server_url = server_url
        self.token = token
        self.base_dir = base_dir
        self.multi = multi

        self.client: ClientSession | None = None
        self.queue: Queue[Item] = Queue()

    async def __aenter__(self):
        self.client = ClientSession(headers={"Authorization": f"Token {self.token}"})
        return self

    async def __aexit__(self, *args):
        await self.client.close()

    async def _get_items(self):
        r = await self.client.get(
            f"{self.server_url}/api/v2.1/via-repo-token/dir/", params={"recursive": 1}
        )
        res = await r.json()
        for obj in res["dirent_list"]:
            if obj["type"] == "dir":
                continue
            path = Path(obj["parent_dir"]) / obj["name"]
            dt = datetime.fromisoformat(obj["mtime"])
            item = Item(path=path, size=obj["size"], mtime=dt)
            self.queue.put_nowait(item)

    async def _get_download_link(self, path: Path) -> str:
        r = await self.client.get(
            f"{self.server_url}/api/v2.1/via-repo-token/download-link/",
            params={"path": str(path)},
        )
        res = await r.text()
        return res.strip('"')

    async def _download(self):
        while True:
            item = await self.queue.get()

            path = self.base_dir / item.path.relative_to("/")
            if not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)

            download_link = await self._get_download_link(item.path)

            async with self.client.get(download_link) as response:
                with open(path, "wb") as f, tqdm(
                    total=item.size,
                    unit="B",
                    unit_scale=True,
                    desc=str(item.path).lstrip("/"),
                    bar_format="{desc:<40} {percentage:3.0f}%|{bar}| {n_fmt:>5}/{total_fmt:>5}",
                ) as pbar:
                    async for chunk in response.content.iter_chunked(65536):
                        f.write(chunk)
                        pbar.update(len(chunk))

            self.queue.task_done()

    async def run(self):
        await self._get_items()

        tasks = []
        for _ in range(self.multi):
            task = create_task(self._download())
            tasks.append(task)

        await self.queue.join()

        for task in tasks:
            task.cancel()
        await gather(*tasks, return_exceptions=True)
