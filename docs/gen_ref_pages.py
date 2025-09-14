"""Generate the code reference pages."""

from pathlib import Path

import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()

# Find all Python files in the source tree
for path in sorted(Path("src").rglob("*.py")):
    module_path = path.relative_to("src").with_suffix("")
    doc_path = path.relative_to("src").with_suffix(".md")
    full_doc_path = Path("api-reference", doc_path)

    parts = tuple(module_path.parts)

    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1] == "__main__":
        continue

    nav[parts] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = ".".join(parts)
        fd.write(f"---\ntitle: {parts[-1]}\n---\n\n")
        fd.write(f"::: {ident}")

    mkdocs_gen_files.set_edit_path(full_doc_path, path)

# Also generate docs for the CLI app
cli_path = Path("app/cli.py")
if cli_path.exists():
    cli_doc_path = Path("api-reference/cli.md")
    nav[("CLI",)] = "cli.md"
    
    with mkdocs_gen_files.open(cli_doc_path, "w") as fd:
        fd.write("---\ntitle: CLI\n---\n\n")
        fd.write("::: app.cli")
    
    mkdocs_gen_files.set_edit_path(cli_doc_path, cli_path)

with mkdocs_gen_files.open("api-reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
