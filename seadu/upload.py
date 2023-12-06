from asyncio import Queue, create_task, gather
from pathlib import Path
from io import BufferedReader
from datetime import datetime

from aiohttp import ClientSession
from tqdm.asyncio import tqdm

from .common import Item


class ProgressFileReader(BufferedReader):
    def __init__(self, filename, pbar):
        self.pbar = pbar
        super().__init__(raw=open(filename, "rb"))

    def read(self, size=None):
        chunk = super(ProgressFileReader, self).read(size)
        self.pbar.update(len(chunk))
        return chunk


class Uploader:
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
        for f in self.base_dir.glob("**/*"):
            if f.is_dir():
                continue
            stat = f.stat()
            dt = datetime.fromtimestamp(stat.st_mtime)
            item = Item(path=f, size=stat.st_size, mtime=dt)
            self.queue.put_nowait(item)

    async def _get_upload_link(self) -> str:
        r = await self.client.get(
            f"{self.server_url}/api/v2.1/via-repo-token/upload-link/",
            params={"path": "/"},
        )
        res = await r.text()
        return res.strip('"')

    async def _upload(self):
        while True:
            item = await self.queue.get()

            path = item.path.relative_to(self.base_dir.parent)

            upload_link = await self._get_upload_link()

            with tqdm(
                total=item.size,
                unit="B",
                unit_scale=True,
                desc=str(path),
                bar_format="{desc:<40} {percentage:3.0f}%|{bar}| {n_fmt:>5}/{total_fmt:>5}",
            ) as pbar:
                data = {
                    "file": ProgressFileReader(item.path, pbar),
                    "parent_dir": "/",
                    "relative_path": str(path.parent),
                    "replace": "1",
                }
                r = await self.client.post(upload_link, data=data)

            self.queue.task_done()

    async def run(self):
        await self._get_items()

        tasks = []
        for _ in range(self.multi):
            task = create_task(self._upload())
            tasks.append(task)

        await self.queue.join()

        for task in tasks:
            task.cancel()
        await gather(*tasks, return_exceptions=True)
