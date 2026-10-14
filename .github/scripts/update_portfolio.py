"""Atualiza a seção de portfólio do README a partir dos seus repositórios.

Entra no portfólio todo repositório que:
  - tem o tópico `portfolio`;
  - tem um site cadastrado no campo "Website" (homepage);
  - não é fork nem está arquivado.

A categoria vem de um destes tópicos: automotivo, saude, esporte, negocios, pessoal.
O nome e a descrição vêm da descrição do repo, no formato "Nome: o que é".
Se não houver ":", o nome do repo é usado como nome.
"""
import json
import os
import re
import sys
import urllib.request

USER = os.environ.get("GH_USER", "AknoLeonel")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
MIN_PROJECTS = int(os.environ.get("MIN_PROJECTS", "10"))
README = "README.md"

CATEGORIES = [
    ("automotivo", "🚗 Automotivo"),
    ("saude", "🩺 Saúde & Bem-estar"),
    ("esporte", "⚽ Esporte & Eventos"),
    ("negocios", "💼 Negócios & Instituições"),
    ("pessoal", "🧪 Projetos pessoais"),
]
BUTTON = "https://img.shields.io/badge/▶_ACESSAR-{color}?style=flat-square&labelColor=0D1117"


def fetch_repos():
    repos, page = [], 1
    while True:
        url = f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}&type=owner"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        if TOKEN:
            req.add_header("Authorization", f"Bearer {TOKEN}")
        with urllib.request.urlopen(req) as r:
            batch = json.load(r)
        if not batch:
            return repos
        repos += batch
        page += 1


def pretty(name):
    return re.sub(r"[-_]+", " ", name).strip().title()


def split_description(repo):
    desc = (repo.get("description") or "").strip()
    if ":" in desc:
        name, what = desc.split(":", 1)
        return name.strip(), what.strip()
    return pretty(repo["name"]), desc


def build(projects):
    blocks, first = [], True
    for key, label in CATEGORIES:
        items = [p for p in projects if p["cat"] == key]
        if not items:
            continue
        color = "FF00E4" if key == "pessoal" else "00F5FF"
        plural = "site" if len(items) == 1 else "sites"
        rows = "\n".join(
            f"| **{p['name']}** | {p['what']} | {p['stack']} | [![]({BUTTON.format(color=color)})]({p['url']}) |"
            for p in sorted(items, key=lambda p: p["name"].lower())
        )
        blocks.append(
            f"<details{' open' if first else ''}>\n<summary><b>{label}</b> · {len(items)} {plural}</summary>\n<br>\n\n"
            "| Projeto | O que é | Stack | |\n|:--|:--|:--|:--:|\n"
            f"{rows}\n\n</details>"
        )
        first = False
    return "\n\n".join(blocks)


def main():
    projects = []
    for r in fetch_repos():
        topics = r.get("topics") or []
        homepage = (r.get("homepage") or "").strip()
        if r.get("fork") or r.get("archived") or "portfolio" not in topics or not homepage:
            continue
        cat = next((k for k, _ in CATEGORIES if k in topics), "pessoal")
        name, what = split_description(r)
        if not homepage.startswith("http"):
            homepage = "https://" + homepage
        projects.append({"name": name, "what": what or "—", "stack": r.get("language") or "—",
                         "cat": cat, "url": homepage})

    print(f"{len(projects)} projetos com o tópico 'portfolio'.")
    if len(projects) < MIN_PROJECTS:
        print(f"Menos de {MIN_PROJECTS} projetos marcados; README mantido como está.")
        return 0

    text = open(README, encoding="utf-8").read()
    new = re.sub(r"(<!-- PORTFOLIO:START -->\n).*?(\n<!-- PORTFOLIO:END -->)",
                 lambda m: m.group(1) + build(projects) + m.group(2), text, flags=re.S)
    n = len(projects)
    new = re.sub(r"PORTFÓLIO-\d+%20sites", f"PORTFÓLIO-{n}%20sites", new)
    new = re.sub(r"lines=\d+\+sites", f"lines={n}+sites", new)
    if new != text:
        open(README, "w", encoding="utf-8").write(new)
        print("README atualizado.")
    else:
        print("Nada mudou.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
