#!/usr/bin/env python3
from github_client import GitHubClient

c = GitHubClient()
r = c.get_repo('google', 'chromium')
if r.success:
    print(f"google/chromium: 成功 - Stars: {r.data.get('stargazers_count')}")
else:
    print(f"google/chromium: 失败 - {r.error}")

r = c.get_repo('facebook', 'react')
if r.success:
    print(f"facebook/react: 成功 - Stars: {r.data.get('stargazers_count')}")
else:
    print(f"facebook/react: 失败 - {r.error}")
