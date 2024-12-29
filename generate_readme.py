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

readme_template = """
<h1 align="center">👋 Добро пожаловать в <strong>{org_name}</strong>!</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Репозиториев-{repo_count}-blue" alt="Repo Count" />
  <img src="https://img.shields.io/badge/Строк_кода-{total_lines}-brightgreen" alt="Total Lines" />
  <img src="https://img.shields.io/badge/Файлов-{total_files}-yellow" alt="Total Files" />
  <img src="https://img.shields.io/badge/Объем_хранилища-{total_storage}MB-purple" alt="Total Storage" />
  <img src="https://img.shields.io/badge/Контрибьюторы-{total_contributors}-orange" alt="Contributors" />
  <img src="https://img.shields.io/badge/Активных_участников-{active_contributors}-red" alt="Active Contributors" />
  <img src="https://img.shields.io/badge/Последняя_активность-{last_activity}-brightgreen" alt="Last Activity" />
</p>

## 🌐 Языки
{languages_section}

<hr/>

## 📂 Репозитории
{repositories_section}
"""

# Словарь с иконками для языков
language_icons = {
    "Python": '<img src="https://img.shields.io/badge/-000?logo=python" alt="Python">',
    # "C#": '<img src="https://img.shields.io/badge/-000?logo=с#" alt="C#">',
    "C#": '<img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMjgiIGhlaWdodD0iMTI4IiB2aWV3Qm94PSIwIDAgMjQgMjQiPjxwYXRoIGZpbGw9ImN1cnJlbnRDb2xvciIgZD0iTTEuMTk0IDcuNTQzdjguOTEzYzAgMS4xMDMuNTg4IDIuMTIyIDEuNTQ0IDIuNjc0bDcuNzE4IDQuNDU2YTMuMDkgMy4wOSAwIDAgMCAzLjA4OCAwbDcuNzE4LTQuNDU2YTMuMDkgMy4wOSAwIDAgMCAxLjU0NC0yLjY3NFY3LjU0M2EzLjA4IDMuMDggMCAwIDAtMS41NDQtMi42NzNMMTMuNTQ0LjQxNGEzLjA5IDMuMDkgMCAwIDAtMy4wODggMEwyLjczOCA0Ljg3YTMuMDkgMy4wOSAwIDAgMC0xLjU0NCAyLjY3M201LjQwMyAyLjkxNHYzLjA4N2EuNzcuNzcgMCAwIDAgLjc3Mi43NzJhLjc3My43NzMgMCAwIDAgLjc3Mi0uNzcyYS43NzMuNzczIDAgMCAxIDEuMzE3LS41NDZhLjc4Ljc4IDAgMCAxIC4yMjYuNTQ2YTIuMzE0IDIuMzE0IDAgMSAxLTQuNjMxIDB2LTMuMDg3YzAtLjYxNS4yNDQtMS4yMDMuNjc5LTEuNjM3YTIuMzEgMi4zMSAwIDAgMSAzLjI3NCAwYy40MzQuNDM0LjY3OCAxLjAyMy42NzggMS42MzdhLjc3Ljc3IDAgMCAxLS4yMjYuNTQ1YS43NjcuNzY3IDAgMCAxLTEuMDkxIDBhLjc3Ljc3IDAgMCAxLS4yMjYtLjU0NWEuNzcuNzcgMCAwIDAtLjc3Mi0uNzcyYS43Ny43NyAwIDAgMC0uNzcyLjc3Mm0xMi4zNSAzLjA4N2EuNzcuNzcgMCAwIDEtLjc3Mi43NzJoLS43NzJ2Ljc3MmEuNzczLjc3MyAwIDAgMS0xLjU0NCAwdi0uNzcyaC0xLjU0NHYuNzcyYS43NzMuNzczIDAgMCAxLTEuMzE3LjU0NmEuNzguNzggMCAwIDEtLjIyNi0uNTQ2di0uNzcySDEyYS43NzEuNzcxIDAgMSAxIDAtMS41NDRoLjc3MnYtMS41NDNIMTJhLjc3Ljc3IDAgMSAxIDAtMS41NDRoLjc3MnYtLjc3MmEuNzczLjc3MyAwIDAgMSAxLjMxNy0uNTQ2YS43OC43OCAwIDAgMSAuMjI2LjU0NnYuNzcyaDEuNTQ0di0uNzcyYS43NzMuNzczIDAgMCAxIDEuNTQ0IDB2Ljc3MmguNzcyYS43NzIuNzcyIDAgMCAxIDAgMS41NDRoLS43NzJ2MS41NDNoLjc3MmEuNzc2Ljc3NiAwIDAgMSAuNzcyLjc3Mm0tMy4wODgtMi4zMTVoLTEuNTQ0djEuNTQzaDEuNTQ0eiIvPjwvc3ZnPg==" alt="C#">',
    "Kotlin": '<img src="https://img.shields.io/badge/-000?logo=kotlin" alt="Kotlin">',
    "Java": '<img src="https://img.shields.io/badge/-000?logo=openjdk" alt="Java">',
    "N/A": '<img src="https://img.shields.io/badge/-000?logo=code&logoColor=gray" alt="Unknown">'
}


# Форматирование таблицы языков
def format_languages_table(_languages: dict) -> str:
    if not _languages:
        return "_Нет данных по языкам_"

    header = "| Язык         | Кол-во байт |\n|--------------|--------|-------------|\n"
    rows = []
    for _lang, _size in _languages.items():
        icon = language_icons.get(lang, language_icons["N/A"])
        rows.append(f"| {_lang} | {icon} | {_size} |")
    return header + "\n".join(rows)


# Форматирование таблицы репозиториев
def format_repos_table(_repos_info: list) -> str:
    if not _repos_info:
        return "_Нет репозиториев_"

    header = "| Репозиторий | Язык (Иконка) | Строк кода | Файлов | Последний коммит | Описание |\n"
    header += "|-------------|---------------|------------|--------|------------------|----------|\n"
    rows = []
    for r in _repos_info:
        icon = language_icons.get(r['language'], language_icons["N/A"])
        row = (
            f"| [{r['name']}]({r['html_url']}) "
            f"| {icon} {r['language']} "
            f"| {r['lines']} "
            f"| {r['files']} "
            f"| {r['last_commit']} "
            f"| {r['description']} |"
        )
        rows.append(row)

    return header + "\n".join(rows)


# Основная логика
repo_count = 0
languages = {}
total_lines = 0
total_files = 0
repos_info = []
total_storage = 0
last_activity = None
all_contributors = set()
active_contributors = set()
doc_coverage = 0

for repo in org.get_repos(type="private"):
    repo_name = repo.name

    # Пропускаем, если нужно
    if repo_name == ".github-private":
        continue

    repo_count += 1
    total_storage += repo.size / 1024  # Перевод размера в MB

    # Обновляем последнюю активность
    if not last_activity or repo.updated_at > last_activity:
        last_activity = repo.updated_at

    # Получение даты последнего коммита
    try:
        last_commit_date = repo.get_commits()[0].commit.committer.date
        last_commit_date = last_commit_date.astimezone(moscow_tz).strftime("%d.%m.%Y")
    except:
        last_commit_date = "Нет данных"

    # Клонируем репо в temp
    with tempfile.TemporaryDirectory() as tmpdirname:
        repo_dir = os.path.join(tmpdirname, repo_name)
        clone_url = repo.clone_url.replace("https://", f"https://{GITHUB_TOKEN}@")

        clone_result = subprocess.run(
            ["git", "clone", "--depth", "1", clone_url, repo_dir],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        if clone_result.returncode != 0:
            continue

        try:
            lines_output = subprocess.run(
                ["cloc", repo_dir, "--json"],
                capture_output=True,
                text=True
            ).stdout
            if lines_output.strip():
                cloc_data = json.loads(lines_output)
                total_lines_repo = cloc_data.get("SUM", {}).get("code", 0)
                total_files_repo = cloc_data.get("SUM", {}).get("nFiles", 0)
            else:
                total_lines_repo = 0
                total_files_repo = 0

            total_lines += total_lines_repo
            total_files += total_files_repo

        except:
            total_lines_repo = 0
            total_files_repo = 0

    # Язык
    primary_lang = repo.language or "N/A"

    # Сбор языков
    repo_langs = repo.get_languages()
    for lang, size in repo_langs.items():
        languages[lang] = languages.get(lang, 0) + size

    # Сбор контрибьюторов
    for contributor in repo.get_contributors():
        all_contributors.add(contributor.login)
        if contributor.contributions > 10:  # Условие "активных участников"
            active_contributors.add(contributor.login)

    # Добавляем описание и дату последнего коммита
    repos_info.append({
        "name": repo_name,
        "html_url": repo.html_url,
        "language": primary_lang,
        "lines": total_lines_repo,
        "files": total_files_repo,
        "description": repo.description or "Описание отсутствует",
        "last_commit": last_commit_date
    })

repos_info = sorted(repos_info, key=lambda r: r['lines'], reverse=True)

# Формируем итоговый Markdown
languages_section = format_languages_table(languages)
repositories_section = format_repos_table(repos_info)

output_text = readme_template.format(
    org_name=ORG_NAME,
    repo_count=repo_count,
    total_lines=total_lines,
    total_files=total_files,
    total_storage=round(total_storage, 2),
    total_contributors=len(all_contributors),
    active_contributors=len(active_contributors),
    last_activity=last_activity.astimezone(moscow_tz).strftime("%d.%m.%Y"),
    languages_section=languages_section,
    repositories_section=repositories_section
)

os.makedirs("profile", exist_ok=True)
output_path = os.path.join("profile", "README.md")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(output_text)

print("README.md обновлён!")
