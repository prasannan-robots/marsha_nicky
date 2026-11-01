"""Persist the bot's memory as a JSON file in a GitHub repository."""

import json
import os

from github import Github, GithubException


class github_store:
    def __init__(self, file_path=None, repo=None, branch=None, token=None):
        # The old version ignored file_path when one was passed.
        self.file_path = file_path or os.getenv("MEMORY_PATH", "memory.json")
        self.github_object = Github(token or os.getenv("GITHUB_TOKEN"))
        self.repository = self.github_object.get_repo(repo or os.getenv("MEMORY_REPO", "marsha-nicky/my_knowledge"))
        self.branch = branch or os.getenv("MEMORY_BRANCH") or self.repository.default_branch

    def pull_data(self) -> dict:
        try:
            contents = self.repository.get_contents(self.file_path, ref=self.branch)
        except GithubException as error:
            if error.status == 404:
                return {}
            raise
        return json.loads(contents.decoded_content.decode() or "{}")

    def push(self, data: dict, message="Update chat memory") -> None:
        content = json.dumps(data, ensure_ascii=False, indent=1)
        try:
            existing = self.repository.get_contents(self.file_path, ref=self.branch)
            self.repository.update_file(existing.path, message, content, existing.sha, branch=self.branch)
        except GithubException as error:
            if error.status != 404:
                raise
            self.repository.create_file(self.file_path, message, content, branch=self.branch)
