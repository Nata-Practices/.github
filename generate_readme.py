import os
import subprocess
import tempfile
import json
from github import Github
from shutil import which
import sys
from datetime import datetime
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
  <img src="https://img.shields.io/badge/Репозиториев-{repo_count}-blue?style=for-the-badge" alt="Repo Count" />
  <img src="https://img.shields.io/badge/Строк_кода-{total_lines}-brightgreen?style=for-the-badge" alt="Total Lines" />
  <img src="https://img.shields.io/badge/Файлов-{total_files}-yellow?style=for-the-badge" alt="Total Files" />
  <img src="https://img.shields.io/badge/Объем_хранилища-{total_storage}MB-purple?style=for-the-badge" alt="Total Storage" />
  <img src="https://img.shields.io/badge/Контрибьюторы-{total_contributors}-orange?style=for-the-badge" alt="Contributors" />
  <img src="https://img.shields.io/badge/Активных_участников-{active_contributors}-red?style=for-the-badge" alt="Active Contributors" />
  <img src="https://img.shields.io/badge/Последняя_активность-{last_activity}-brightgreen?style=for-the-badge" alt="Last Activity" />
</p>

## 🌐 Языки
{languages_section}

<hr/>

## 📂 Репозитории
{repositories_section}
"""

def format_languages_table(languages: dict) -> str:
    if not languages:
        return "_Нет данных по языкам_"
    
    header = "| Язык | Кол-во байт |\n|------|------------|\n"
    rows = []
    for lang, size in languages.items():
        rows.append(f"| {lang} | {size} |")
    return header + "\n".join(rows)

def format_repos_table(repos_info: list) -> str:
    if not repos_info:
        return "_Нет репозиториев_"

    header = "| Репозиторий | Язык | Строк кода | Файлов | Последний коммит | Описание |\n"
    header += "|-------------|------|------------|--------|------------------|----------|\n"
    rows = []
    for r in repos_info:
        row = (
            f"| [{r['name']}]({r['html_url']}) "
            f"| {r['language']} "
            f"| {r['lines']} "
            f"| {r['files']} "
            f"| {r['last_commit']} "
            f"| {r['description']} |"
        )
        rows.append(row)

    return header + "\n".join(rows)

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

            # Уровень документации (README.md)
            if os.path.exists(os.path.join(repo_dir, "README.md")):
                doc_coverage += 1

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
        "last_commit": repo.pushed_at.astimezone(moscow_tz).strftime("%d.%m.%Y")
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
