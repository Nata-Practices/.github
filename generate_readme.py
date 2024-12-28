import os
import subprocess
import tempfile
import json
from github import Github
from shutil import which
import sys

if not which("cloc"):
    sys.exit(1)

GITHUB_TOKEN = os.getenv('TKN')
if not GITHUB_TOKEN:
    sys.exit(1)

ORG_NAME = "Nata-Practices"

g = Github(GITHUB_TOKEN)
org = g.get_organization(ORG_NAME)

readme_template = """
## 📊 Общая статистика
- **Репозиториев**: {repo_count}
- **Языков**:
{languages}
- **Всего строк кода**: {total_lines}
- **Всего файлов**: {total_files}

## 📂 Репозитории
{repositories}
"""

repo_count = 0
languages = {}
repositories = []
total_lines = 0
total_files = 0

for repo in org.get_repos():
    repo_count += 1
    repo_name = repo.name
    
    if repo_name == ".github-private":
        continue
        
    with tempfile.TemporaryDirectory() as tmpdirname:
        repo_dir = os.path.join(tmpdirname, repo_name)
        repo_clone_url = repo.clone_url.replace("https://", f"https://{GITHUB_TOKEN}@")
        clone_result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_clone_url, repo_dir],
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

        except Exception as e:
            total_lines_repo = 0
            total_files_repo = 0

    langs = repo.get_languages()
    for lang, size in langs.items():
        languages[lang] = languages.get(lang, 0) + size

    repositories.append(
        f"- [{repo.name}]({repo.html_url}) "
        f"({repo.language}): {total_lines_repo} строк кода, {total_files_repo} файлов"
    )

languages_summary = "\n".join([f"  - {lang}: {size} байт" for lang, size in languages.items()])
repositories_summary = "\n".join(repositories)

output_path = os.path.join("profile", "README.md")
os.makedirs("profile", exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    f.write(readme_template.format(
        repo_count=repo_count,
        languages=languages_summary,
        repositories=repositories_summary,
        total_lines=total_lines,
        total_files=total_files
    ))

print(f"README.md обновлён!")
