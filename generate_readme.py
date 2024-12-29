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

# Иконки для языков (для удобства в таблице)
language_icons = {
    "Python": '<img src="https://cdn.simpleicons.org/python?viewbox=auto" height="20" alt="Python">',
    "C#": '<img src="https://img.shields.io/badge/C%23-0?color=9b4993" height="20" alt="C#">',
    "Kotlin": '<img src="https://cdn.simpleicons.org/kotlin?viewbox=auto" height="20" alt="Kotlin">',
    "Java": '<img src="https://cdn.simpleicons.org/openjdk?viewbox=auto" height="20" alt="Java">',
    "N/A": '<img src="https://cdn.simpleicons.org/c#?viewbox=auto" height="20" alt="Unknown">'
}


def format_languages_table(code_lines_per_language: dict, bytes_per_language: dict) -> str:
    """
    Строит таблицу на основе строк кода (code_lines_per_language) и байтов (bytes_per_language).
    """
    if not code_lines_per_language:
        return "_Нет данных по языкам_"

    total_lines_local = sum(code_lines_per_language.values())
    # Сортируем языки по убыванию строк кода
    sorted_languages = sorted(
        code_lines_per_language.items(),
        key=lambda x: x[1],
        reverse=True
    )

    header = "| № | Язык | Процент использования | Кол-во байт |\n"
    header += "|---|------|-----------------------|-------------|\n"

    rows = []
    for rank, (lang, loc) in enumerate(sorted_languages, start=1):
        icon = language_icons.get(lang, language_icons["N/A"])
        # Считаем процент только по строкам кода
        percent = (loc / total_lines_local) * 100
        # байты берем из GitHub API (если вдруг там не было этого языка, будет 0)
        byte_size = bytes_per_language.get(lang, 0)
        rows.append(
            f"| {rank} | {icon} | {percent:.2f}% | {byte_size} |"
        )

    return header + "\n".join(rows)


def format_repos_table(repos_info: list) -> str:
    """
    Формируем сводную таблицу по репозиториям.
    """
    if not repos_info:
        return "_Нет репозиториев_"

    header = "| Репозиторий | Язык | Строк кода | Файлов | Последний коммит | Описание |\n"
    header += "|-------------|------|------------|--------|------------------|----------|\n"
    rows = []
    for r in repos_info:
        icon = language_icons.get(r['language'], language_icons["N/A"])
        row = (
            f"| [{r['name']}]({r['html_url']}) "
            f"| {icon} "
            f"| {r['lines']} "
            f"| {r['files']} "
            f"| {r['last_commit']} "
            f"| {r['description']} |"
        )
        rows.append(row)

    return header + "\n".join(rows)


# ---------------------------------------------
# Основная логика
# ---------------------------------------------

repo_count = 0
total_lines = 0       # Общее число строк кода (сумма по всем репо)
total_files = 0       # Общее число файлов (сумма по всем репо)
total_storage = 0     # Суммарный объём в MB
last_activity = None
all_contributors = set()
active_contributors = set()

# Для статистики по языкам:
code_lines_per_language = {}  # Здесь аккумулируем строки (cloc)
bytes_per_language = {}       # Здесь аккумулируем байты (get_languages)

repos_info = []

for repo in org.get_repos(type="private"):
    repo_name = repo.name

    # Пропустим, если это служебное
    if repo_name == ".github-private":
        continue

    repo_count += 1
    # GitHub даёт размер репо в Kb (repo.size). Переведём в MB:
    total_storage += repo.size / 1024

    # Следим за последней активностью
    if not last_activity or repo.updated_at > last_activity:
        last_activity = repo.updated_at

    # Получаем дату последнего коммита (если есть)
    try:
        last_commit_date = repo.get_commits()[0].commit.committer.date
        last_commit_date = last_commit_date.astimezone(moscow_tz).strftime("%d.%m.%Y")
    except:
        last_commit_date = "Нет данных"

    # Клонируем репозиторий в temp-папку и прогоняем через cloc
    with tempfile.TemporaryDirectory() as tmpdirname:
        repo_dir = os.path.join(tmpdirname, repo_name)
        clone_url = repo.clone_url.replace("https://", f"https://{GITHUB_TOKEN}@")

        clone_result = subprocess.run(
            ["git", "clone", "--depth", "1", clone_url, repo_dir],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        if clone_result.returncode != 0:
            # Если не получилось склонировать — пропустим
            continue

        try:
            lines_output = subprocess.run(
                ["cloc", repo_dir, "--json", "--exclude-dir=.venv,__pycache__,.idea"],
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

            # Увеличиваем глобальные счётчики
            total_lines += total_lines_repo
            total_files += total_files_repo

            # Добавляем строки кода по языкам
            # (в cloc_data обычно есть ключи "header", "SUM" — их пропускаем)
            for lang_name, lang_stats in cloc_data.items():
                if lang_name in ("header", "SUM"):
                    continue
                code_count = lang_stats.get("code", 0)
                if code_count > 0:
                    code_lines_per_language[lang_name] = (
                        code_lines_per_language.get(lang_name, 0) + code_count
                    )

        except:
            # Если что-то упало при анализе — просто пропустим
            total_lines_repo = 0
            total_files_repo = 0

    # Для таблицы репозиториев: язык берем из repo.language
    primary_lang = repo.language or "N/A"

    # Сбор «байтов» по языкам из GitHub (repo.get_languages())
    repo_langs = repo.get_languages()  # { "Python": <bytes>, "C#": <bytes>, ...}
    for lang, size in repo_langs.items():
        bytes_per_language[lang] = bytes_per_language.get(lang, 0) + size

    # Сбор контрибьюторов (для подсчёта их количества)
    for contributor in repo.get_contributors():
        all_contributors.add(contributor.login)
        if contributor.contributions > 10:
            active_contributors.add(contributor.login)

    # Добавляем запись о репозитории
    repos_info.append({
        "name": repo_name,
        "html_url": repo.html_url,
        "language": primary_lang,
        "lines": total_lines_repo,
        "files": total_files_repo,
        "description": repo.description or "Описание отсутствует",
        "last_commit": last_commit_date
    })

# Сортируем репозитории по убыванию строк кода
repos_info.sort(key=lambda r: r['lines'], reverse=True)

# Формируем готовые части для README.md
languages_section = format_languages_table(code_lines_per_language, bytes_per_language)
repositories_section = format_repos_table(repos_info)

# Формируем итоговый Markdown, подставляем статистику
if last_activity:
    last_activity_str = last_activity.astimezone(moscow_tz).strftime("%d.%m.%Y")
else:
    last_activity_str = "Нет данных"

output_text = readme_template.format(
    org_name=ORG_NAME,
    repo_count=repo_count,
    total_lines=total_lines,
    total_files=total_files,
    total_storage=round(total_storage, 2),
    total_contributors=len(all_contributors),
    active_contributors=len(active_contributors),
    last_activity=last_activity_str,
    languages_section=languages_section,
    repositories_section=repositories_section
)

os.makedirs("profile", exist_ok=True)
output_path = os.path.join("profile", "README.md")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(output_text)

print("README.md обновлён!")
