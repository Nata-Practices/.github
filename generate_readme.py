import os
import subprocess
import tempfile
import json
from github import Github
from shutil import which
import sys

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
  <img src="https://img.shields.io/badge/Строк кода-{total_lines}-brightgreen?style=for-the-badge" alt="Total Lines" />
  <img src="https://img.shields.io/badge/Файлов-{total_files}-yellow?style=for-the-badge" alt="Total Files" />
</p>

## 🌐 Языки
{languages_section}

<hr/>

## 📊 Общая статистика
- **Репозиториев**: {repo_count}
- **Всего строк кода**: {total_lines}
- **Всего файлов**: {total_files}

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

    header = "| Репозиторий | Язык | Строк кода | Файлов |\n|-------------|------|------------|--------|\n"
    rows = []
    for r in repos_info:
        row = (
            f"| [{r['name']}]({r['html_url']}) "
            f"| {r['language']} "
            f"| {r['lines']} "
            f"| {r['files']} |"
        )
        rows.append(row)

    return header + "\n".join(rows)

repo_count = 0
languages = {}
total_lines = 0
total_files = 0
repos_info = []

for repo in org.get_repos():
    repo_name = repo.name
    
    # Пропускаем, если нужно
    if repo_name == ".github-private":
        continue
    
    repo_count += 1
    
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

    repos_info.append({
        "name": repo_name,
        "html_url": repo.html_url,
        "language": primary_lang,
        "lines": total_lines_repo,
        "files": total_files_repo
    })

# Формируем итоговый Markdown
languages_section = format_languages_table(languages)
repositories_section = format_repos_table(repos_info)

output_text = readme_template.format(
    org_name=ORG_NAME,
    repo_count=repo_count,
    total_lines=total_lines,
    total_files=total_files,
    languages_section=languages_section,
    repositories_section=repositories_section
)

os.makedirs("profile", exist_ok=True)
output_path = os.path.join("profile", "README.md")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(output_text)

print("README.md обновлён!")
