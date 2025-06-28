import json
import os
import subprocess
import sys
import tempfile
from shutil import which

from github import Github
from pytz import timezone

moscow_tz = timezone("Europe/Moscow")

if not which("cloc"):
    sys.exit("cloc не установлен или не найден в PATH")

GITHUB_TOKEN = os.getenv('TKN')
if not GITHUB_TOKEN:
    sys.exit("Не задана переменная окружения TKN")

ORG_NAME = "Nata-Practices"
g = Github(GITHUB_TOKEN)
org = g.get_organization(ORG_NAME)

readme_template = """<h1 align="center">👋 Добро пожаловать в <strong>{org_name}</strong>!</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Репозиториев-{repo_count}-blue" alt="Repo Count" />
  <img src="https://img.shields.io/badge/Строк_кода-{total_lines}-brightgreen" alt="Total Lines" />
  <img src="https://img.shields.io/badge/Файлов-{total_files}-yellow" alt="Total Files" />
  <img src="https://img.shields.io/badge/Объем_хранилища-{total_storage}MB-purple" alt="Total Storage" />
  <img src="https://img.shields.io/badge/Контрибьюторы-{total_contributors}-orange" alt="Contributors" />
  <img src="https://img.shields.io/badge/Активных_участников-{active_contributors}-red" alt="Active Contributors" />
  <img src="https://img.shields.io/badge/Последняя_активность-{last_activity}-brightgreen" alt="Last Activity" />
</p>

{repositories_section}
"""

# Словарь с иконками для языков
language_icons = {
    "Python": '<img src="https://cdn.simpleicons.org/python?viewbox=auto" height="20" alt="Python">',
    "C#": '<img src="https://img.shields.io/badge/C%23-0?color=9b4993" height="20" alt="C#">',
    "Kotlin": '<img src="https://cdn.simpleicons.org/kotlin?viewbox=auto" height="20" alt="Kotlin">',
    "Java": '<img src="https://cdn.simpleicons.org/openjdk?viewbox=auto" height="20" alt="Java">',
    "Prolog": '<img src="https://starbeamrainbowlabs.com/images/logos/swi-prolog.svg" height="20" alt="Prolog">',
    "Lua": '<img src="https://cdn.simpleicons.org/lua?viewbox=auto" height="20" alt="Lua">',
    "N/A": '<img src="https://cdn.simpleicons.org/c#?viewbox=auto" height="20" alt="Unknown">'
}

def format_repos_table(_repos_info: list) -> str:
    if not _repos_info:
        return "_Нет репозиториев_"
    header = (
        "| Репозиторий | Язык | Строк кода | Файлов | Последний коммит | Описание |\n"
        "|-------------|------|------------|--------|------------------|----------|"
    )
    rows = []
    for r in _repos_info:
        icon = language_icons.get(r['language'], language_icons["N/A"])
        rows.append(
            f"| [{r['name']}]({r['html_url']}) "
            f"| {icon} "
            f"| {r['lines']} "
            f"| {r['files']} "
            f"| {r['last_commit']} "
            f"| {r['description']} |"
        )
    return header + "\n" + "\n".join(rows)


# Сбор статистики
repo_count = 0
total_lines = 0
total_files = 0
total_storage = 0
last_activity = None
all_contributors = set()
active_contributors = set()
repos_info = []

for repo in org.get_repos(type="all"):
    name = repo.name
    if name.startswith(".github"):
        continue

    repo_count += 1
    total_storage += repo.size / 1024  # KB → MB

    if not last_activity or repo.updated_at > last_activity:
        last_activity = repo.updated_at

    try:
        date = repo.get_commits()[0].commit.committer.date
        last_commit = date.astimezone(moscow_tz).strftime("%d.%m.%Y")
    except:
        last_commit = "Нет данных"

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, name)
        url = repo.clone_url.replace("https://", f"https://{GITHUB_TOKEN}@")
        if subprocess.run(["git","clone","--depth","1",url,path],
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode != 0:
            continue

        try:
            out = subprocess.run(
                ["cloc", path, "--json",
                 "--exclude-dir=.venv,__pycache__,.idea,.gradle,build",
                 "--exclude-ext=gradle,pro,json,md,gitignore,cache,props,targets,bat,properties,editorconfig,Up2Date,props"],
                capture_output=True, text=True
            ).stdout
            data = json.loads(out) if out.strip() else {}
            lines = data.get("SUM", {}).get("code", 0)
            files = data.get("SUM", {}).get("nFiles", 0)
        except:
            lines = files = 0

    total_lines += lines
    total_files += files

    # Язык и контрибьюторы
    lang = repo.language or "N/A"
    for l, sz in repo.get_languages().items():
        pass  # можно накопить, если нужно

    for contrib in repo.get_contributors():
        all_contributors.add(contrib.login)
        if contrib.contributions > 10:
            active_contributors.add(contrib.login)

    repos_info.append({
        "name": name,
        "html_url": repo.html_url,
        "language": lang,
        "lines": lines,
        "files": files,
        "description": repo.description or "Описание отсутствует",
        "last_commit": last_commit
    })

repos_info = sorted(repos_info, key=lambda r: r['lines'], reverse=True)
repositories_section = format_repos_table(repos_info)

if last_activity:
    last_activity_str = last_activity.astimezone(moscow_tz).strftime("%d.%m.%Y")
else:
    last_activity_str = "Нет данных"

output = readme_template.format(
    org_name=ORG_NAME,
    repo_count=repo_count,
    total_lines=total_lines,
    total_files=total_files,
    total_storage=round(total_storage, 2),
    total_contributors=len(all_contributors),
    active_contributors=len(active_contributors),
    last_activity=last_activity_str,
    repositories_section=repositories_section
)

os.makedirs("profile", exist_ok=True)
with open("profile/README.md", "w", encoding="utf-8") as f:
    f.write(output)

print("README.md обновлён!")
