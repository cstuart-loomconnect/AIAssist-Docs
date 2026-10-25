"""Writes the generated pages of the documentation site into documentation/.

Everything that can be worked out from the AIAssist package repository is generated here, so it
cannot go stale:
  documentation/_stats.md            the numbers on the Home page
  documentation/changelog.md         merged pull requests from git
  documentation/codebase-health.md   checks worked out from the source
  documentation/reference/           Apex, data model, Lightning web components, permission sets

The package source lives in a separate repo (AIAssist). Point this script at a clone of it:
  python3 scripts/generate.py ../AIAssist
or set AIASSIST_PATH. With no argument it looks for ./aiassist (where CI checks it out), then
../AIAssist. Use a clone with full history (and the master branch checked out) for a
complete changelog. AIASSIST_BRANCH (default master) sets the branch named in links and text.
Uses only the Python standard library (plus git).
"""
import os
import re
import sys
import subprocess
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

DOCS_ROOT = Path(__file__).resolve().parents[1]
DOCS = DOCS_ROOT / "documentation"


def find_package_repo():
    candidates = [sys.argv[1] if len(sys.argv) > 1 else None, os.environ.get("AIASSIST_PATH"), DOCS_ROOT / "aiassist", DOCS_ROOT.parent / "AIAssist"]
    for candidate in filter(None, candidates):
        path = Path(candidate).resolve()
        if (path / "force-app/main/default").is_dir():
            return path
    sys.exit("Could not find the AIAssist repo. Pass its path: python3 scripts/generate.py ../AIAssist")


ROOT = find_package_repo()
SOURCE = ROOT / "force-app/main/default"
GITHUB = "https://github.com/cstuart-loomconnect/AIAssist"
BRANCH = os.environ.get("AIASSIST_BRANCH", "master")
NS = {"m": "http://soap.sforce.com/2006/04/metadata"}


# ---------- Small helpers ----------

def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def write(relative_path, text):
    path = DOCS / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def xml_text(root, tag):
    element = root.find(f"m:{tag}", NS)
    return element.text.strip() if element is not None and element.text else ""


def table(headings, rows):
    lines = ["| " + " | ".join(headings) + " |", "|" + "---|" * len(headings)]
    lines += ["| " + " | ".join(str(cell).replace("\n", " ").replace("|", "\\|") for cell in row) + " |" for row in rows]
    return "\n".join(lines)


def short(api_name):
    return re.sub(r"__(c|mdt|e)$", "", api_name)


# ---------- Apex ----------

def read_apex():
    """Every non-test Apex class: header description, sharing, line count and its public methods."""
    classes = {}
    folder = SOURCE / "classes"
    for file in sorted(folder.glob("*.cls")):
        name = file.stem
        if name.endswith("Test") or name == "AIAssistTestDataFactory":
            continue
        text = file.read_text(encoding="utf-8")
        declaration = re.search(r"^(?:@\w+(?:\([^)]*\))?\s+)*(global|public)\s+((?:with|without|inherited) sharing\s+)?(virtual\s+|abstract\s+)?(class|interface|enum)\s+" + name, text, re.M)
        description = re.search(r"Description:\s*(.+?)(?:\n\s*\n|\nStep 1)", text, re.S)
        classes[name] = {
            "name": name,
            "kind": declaration.group(4) if declaration else "class",
            "sharing": (declaration.group(2) or "").strip() if declaration else "",
            "lines": text.count("\n") + 1,
            "description": " ".join(description.group(1).split()) if description else "",
            "methods": apex_methods(text, is_interface=bool(declaration and declaration.group(4) == "interface")),
            "path": f"force-app/main/default/classes/{file.name}",
            "test": test_info(name),
        }
    return classes


def apex_methods(text, is_interface):
    """Public and global methods declared directly on the class, with the // comment above each."""
    pattern = re.compile(r"^    (?:(?:public|global)\s+)" + ("?" if is_interface else "") + r"((?:static\s+|override\s+|virtual\s+)*)([\w<>,.\[\]\s]+?)\s+(\w+)\((.*?)\)\s*[{;]")
    lines = text.splitlines()
    methods = []
    for index, line in enumerate(lines):
        match = pattern.match(line)
        if not match or match.group(2).strip() in ("return", "new", "else"):
            continue
        comment = []
        above = index - 1
        while above >= 0 and lines[above].startswith("    //"):
            comment.insert(0, lines[above].strip()[2:].strip())
            above -= 1
        methods.append({
            "static": "static" in match.group(1),
            "returns": " ".join(match.group(2).split()),
            "name": match.group(3),
            "params": " ".join(match.group(4).split()),
            "comment": " ".join(comment),
        })
    return methods


def test_info(name):
    file = SOURCE / "classes" / f"{name}Test.cls"
    if not file.exists():
        return None
    count = len(re.findall(r"(?i)@istest(?:\([^)]*\))?\s*(?:private\s+|public\s+)?static\s+void", file.read_text(encoding="utf-8")))
    return {"name": f"{name}Test", "methods": count}


# Which sidebar page each class belongs to. First rule that matches wins; anything left is Foundation.
APEX_AREAS = [
    ("Messaging pipeline", "messaging-pipeline", lambda n: n.startswith(("AIMessage", "AIExecutionStep")) or n in ("AIConversationLockService", "AIConversationMessageService", "AIMessagingDataService")),
    ("Agent and providers", "agent-and-providers", lambda n: n.startswith(("AIAgentManager", "AIProvider", "IAIProvider", "AIAnthropic", "AIOpenAi"))),
    ("Chat window API", "chat-window-api", lambda n: n.startswith("AIChat") or n in ("AIConversationShareService", "AIConversationVisibilityService")),
    ("Data sources", "data-sources", lambda n: n.startswith(("AIDataSource", "IAIDataSource", "AISoql"))),
    ("Workflow actions", "workflow-actions", lambda n: n.startswith(("AIWorkflowAction", "IAIWorkflowAction"))),
    ("Prompt templates", "prompt-templates", lambda n: n in ("AIPromptTemplateService", "AIPromptMergeFieldService")),
    ("PII protection", "pii-protection", lambda n: n.startswith("AIPii") and not n.startswith(("AIPiiRegistryController", "AIPiiRegistryDataStructure", "AIPiiRegistryEditor", "AIPiiRegistryCoverage", "AIPiiRegistryMasking"))),
    ("Usage and policies", "usage-and-policies", lambda n: n.startswith("AIUsage")),
    ("Admin tabs", "admin-tabs", lambda n: n.endswith(("Controller", "EditorService", "DataStructure", "TryItService", "CheckService", "TestService", "AssignmentService", "CoverageService")) or n.startswith(("AITools", "AIModels", "AIPolicies", "AIPromptTemplates", "AIAgentWizard", "AIAssistSettingsController"))),
    ("Logging and scheduled jobs", "logging-and-jobs", lambda n: n.startswith("AIPlatformLog") or n.endswith("Batch") or n == "AIMaintenanceScheduler"),
    ("Trigger handlers", "trigger-handlers", lambda n: n.endswith("TriggerHandler")),
]


def apex_area(name):
    for title, slug, matches in APEX_AREAS:
        if matches(name):
            return title, slug
    return "Foundation", "foundation"


def class_history(path):
    rows = []
    for line in git("log", "-3", "--no-merges", "--date=short", "--format=%ad|%h|%s", "--", path).splitlines():
        date, sha, subject = line.split("|", 2)
        rows.append([date, f"[`{sha}`]({GITHUB}/commit/{sha})", subject])
    return rows


def class_section(c):
    facts = [c["kind"]] + ([c["sharing"]] if c["sharing"] else []) + [f"{c['lines']} lines", f"[source]({GITHUB}/blob/{BRANCH}/{c['path']})"]
    out = [f"## {c['name']}", "", "`" + "` · `".join(facts[:2 if c["sharing"] else 1]) + "` · " + " · ".join(facts[2 if c["sharing"] else 1:]), ""]
    if c["description"]:
        out += [c["description"], ""]
    if c["methods"]:
        rows = [[f"`{m['name']}({m['params']})`", f"`{m['returns']}`", (("static — " if m["static"] else "") + m["comment"]).strip(" —")] for m in c["methods"]]
        out += [table(["Method", "Returns", "What it does"], rows), ""]
    if c["test"]:
        out += [f"**Tests:** `{c['test']['name']}` — {c['test']['methods']} test methods.", ""]
    history = class_history(c["path"])
    if history:
        out += ['??? info "Recent changes"', ""]
        out += ["    " + line for line in table(["Date", "Commit", "Change"], history).splitlines()]
        out += ["", f"    [Full history on GitHub]({GITHUB}/commits/{BRANCH}/{c['path']})", ""]
    return "\n".join(out)


def write_apex_reference(classes):
    areas = defaultdict(list)
    for c in classes.values():
        areas[apex_area(c["name"])].append(c)
    index_rows = []
    for (title, slug), members in sorted(areas.items(), key=lambda a: [t for t, _, _ in APEX_AREAS + [("Foundation", "", None)]].index(a[0][0])):
        write(f"reference/apex/{slug}.md", f"# {title}\n\nGenerated from the Apex source. {len(members)} classes.\n\n" + "\n".join(class_section(c) for c in members))
        index_rows.append([f"[{title}]({slug}.md)", len(members), ", ".join(f"`{c['name']}`" for c in members[:4]) + (" …" if len(members) > 4 else "")])
    write("reference/apex/index.md", "# Apex\n\nPublic and global methods, generated from the source and its comments.\n\n" + table(["Area", "Classes", "Includes"], index_rows))
    return {slug: title for title, slug, _ in APEX_AREAS + [("Foundation", "foundation", None)]}


# ---------- Objects ----------

SUMMARY = {
    "AIAgent__c": "An assistant a user can chat with: persona, access mode, conversation limits and retention, tied to a model and a prompt template.",
    "AIModelConfiguration__c": "A connection to an AI provider: named credential, model identifier, temperature and output limits.",
    "AIPromptTemplate__c": "The system prompt an agent answers with, including merge fields. Can be tried with Try It.",
    "AIPromptTestMessage__c": "A saved test message used to try a prompt template.",
    "AIDataSource__c": "A tool that lets the model read Salesforce data, such as a SOQL template or an Apex class.",
    "AIWorkflowAction__c": "A tool that lets the user do something, such as an Apex action or a Screen Flow.",
    "AIAgentDataSource__c": "Junction: which data sources an agent may call.",
    "AIAgentWorkflowAction__c": "Junction: which workflow actions an agent may suggest.",
    "AIAgentAssignment__c": "Grants a user access to an agent when its access mode is Assigned Users Only.",
    "AIConversation__c": "One chat between a user and an agent. Private to its owner unless shared.",
    "AIConversationMessage__c": "A single message in a conversation, user or assistant, with status, tokens and any suggested action.",
    "AIFeedback__c": "Thumbs up or down, with comments, on an assistant message.",
    "AITermsAcknowledgment__c": "Records that a user accepted the AI terms.",
    "AIUsagePolicy__c": "Limits applied to the users the policy is assigned to.",
    "AIUsagePolicyAssignment__c": "Assigns a usage policy to a user.",
    "AIUsage__c": "What one user has used today: one row per user.",
    "AIPIIRegistry__c": "An object whose fields are scanned and classified for PII.",
    "AIPIIFieldMetadata__c": "The PII classification of one field on a registered object.",
    "AIPIIMapping__c": "The pseudonym mapping for a conversation.",
    "AIPIIMaskingRecord__c": "A record of what was masked in a message.",
    "AIPiiComplianceGroup__mdt": "A compliance grouping for PII field types.",
    "AIPiiDataMaskingRule__mdt": "How a kind of PII is masked.",
    "AIPiiFieldType__mdt": "A kind of PII and how it is recognised.",
    "AIAssistSettings__c": "Org-wide behaviour settings (hierarchy custom setting).",
    "AIAssistUISettings__c": "Chat window appearance and wording settings (hierarchy custom setting).",
    "AIChatCommand__mdt": "A slash command available in the chat composer.",
    "AIPlatformLog__c": "A log entry written by the platform log manager.",
    "AIPlatformLogEvent__e": "Platform event used to write log entries even when a transaction rolls back.",
}

# Diagram groups: title and the objects drawn in each.
ERD_GROUPS = [
    ("Agents and tools", ["AIAgent__c", "AIModelConfiguration__c", "AIPromptTemplate__c", "AIDataSource__c", "AIWorkflowAction__c", "AIAgentAssignment__c", "AIAgentDataSource__c", "AIAgentWorkflowAction__c"]),
    ("Conversations", ["AIConversation__c", "AIConversationMessage__c", "AIFeedback__c", "AITermsAcknowledgment__c", "AIAgent__c", "AIPromptTemplate__c", "AIModelConfiguration__c", "AIWorkflowAction__c"]),
    ("Prompt templates", ["AIPromptTemplate__c", "AIPromptTestMessage__c", "AIAgent__c"]),
    ("PII registry", ["AIPIIRegistry__c", "AIPIIFieldMetadata__c", "AIPIIMapping__c", "AIPIIMaskingRecord__c", "AIConversation__c", "AIConversationMessage__c"]),
    ("Usage", ["AIUsagePolicy__c", "AIUsagePolicyAssignment__c", "AIUsage__c"]),
]


def read_objects():
    objects = {}
    folder = SOURCE / "objects"
    for directory in sorted(folder.iterdir()):
        meta_file = directory / f"{directory.name}.object-meta.xml"
        if not meta_file.exists():
            continue
        meta = ET.parse(meta_file).getroot()
        fields = []
        for field_file in sorted((directory / "fields").glob("*.field-meta.xml")):
            f = ET.parse(field_file).getroot()
            field_type = xml_text(f, "type")
            fields.append({
                "name": field_file.name.replace(".field-meta.xml", ""),
                "label": xml_text(f, "label"),
                "type": field_type,
                "required": xml_text(f, "required") == "true" or field_type == "MasterDetail",
                "unique": xml_text(f, "unique") == "true",
                "external_id": xml_text(f, "externalId") == "true",
                "reference": xml_text(f, "referenceTo"),
                "values": [v.text for v in f.findall(".//m:valueSetDefinition/m:value/m:fullName", NS)],
                "description": " ".join(xml_text(f, "description").split()),
            })
        name = directory.name
        objects[name] = {
            "name": name,
            "label": xml_text(meta, "label"),
            "kind": "Custom metadata type" if name.endswith("__mdt") else "Platform event" if name.endswith("__e") else "Custom object",
            "sharing": xml_text(meta, "sharingModel"),
            "description": SUMMARY.get(name) or " ".join(xml_text(meta, "description").split()),
            "fields": fields,
            "validation_rules": sorted(p.name.replace(".validationRule-meta.xml", "") for p in (directory / "validationRules").glob("*.xml")) if (directory / "validationRules").exists() else [],
            "list_views": sorted(p.name.replace(".listView-meta.xml", "") for p in (directory / "listViews").glob("*.xml")) if (directory / "listViews").exists() else [],
        }
    return objects


def erd(names, objects):
    names = [n for n in names if n in objects]
    links = [(o["name"], f) for n in names for o in [objects[n]] for f in o["fields"] if f["reference"] and (f["reference"] in names or f["reference"] == "User")]
    drawn = {n for n, f in links} | {f["reference"] for n, f in links}
    lines = ["erDiagram"]
    for child, f in links:
        arrow = "||--o{" if f["type"] == "MasterDetail" else "|o..o{"
        lines.append(f'    {short(f["reference"])} {arrow} {short(child)} : "{short(f["name"])}"')
    for name in names:
        if name not in drawn:
            continue
        keys = [f for f in objects[name]["fields"] if f["reference"] or f["required"] or f["unique"] or f["external_id"]][:6]
        lines.append(f"    {short(name)} {{")
        lines += [f"        string {short(f['name'])}{' FK' if f['reference'] else ' UK' if f['unique'] or f['external_id'] else ''}" for f in keys] or ["        string Name"]
        lines.append("    }")
    return "```mermaid\n" + "\n".join(lines) + "\n```"


def write_data_model(objects):
    out = ["# Data model", "",
           f"The package defines {len(objects)} objects, settings, metadata types and events. Each has its own page with every field, generated from the metadata on each build.", "",
           "## Relationships", "", "Solid lines are master-detail, dotted lines are lookups. Only the key fields of each object are drawn; see the object's page for all of them.", ""]
    for title, names in ERD_GROUPS:
        out += [f"### {title}", "", erd(names, objects), ""]
    out += ["## All objects", ""]
    rows = [[f"[{o['label']}](objects/{o['name']}.md)", f"`{o['name']}`", o["kind"], o["sharing"] or "—", len(o["fields"]), o["description"]] for o in objects.values()]
    out.append(table(["Object", "API name", "Kind", "Sharing", "Fields", "Purpose"], rows))
    write("reference/data-model.md", "\n".join(out))

    for o in objects.values():
        page = [f"# {o['label']}", "", f"`{o['name']}` · {o['kind']}" + (f" · sharing: {o['sharing']}" if o["sharing"] else ""), "", o["description"], ""]
        field_rows = []
        for f in o["fields"]:
            notes = [x for x in ["required" if f["required"] else "", "unique" if f["unique"] else "", "external ID" if f["external_id"] else "", ("values: " + ", ".join(f["values"])) if f["values"] else "", f["description"]] if x]
            field_rows.append([f["label"], f"`{f['name']}`", f["type"] + (f" → `{short(f['reference'])}`" if f["reference"] else ""), " · ".join(notes)])
        page += ["## Fields", "", table(["Field", "API name", "Type", "Notes"], field_rows), ""]
        if o["validation_rules"]:
            page += ["## Validation rules", ""] + [f"- `{r}`" for r in o["validation_rules"]] + [""]
        if o["list_views"]:
            page += ["## List views", ""] + [f"- {v}" for v in o["list_views"]] + [""]
        write(f"reference/objects/{o['name']}.md", "\n".join(page))


# ---------- Lightning web components ----------

LWC_FAMILIES = [
    ("Chat window", ("aiAssistChat", "aiChat")),
    ("Agent Wizard", ("aiAgentWizard",)),
    ("AI Models", ("aiModels",)),
    ("Prompt Templates", ("aiPromptTemplates",)),
    ("AI Tools", ("aiTools",)),
    ("AI Policies", ("aiPolicies",)),
    ("AI PII Registry", ("aiPiiRegistry",)),
    ("Settings", ("aiAssistSettings",)),
]


def write_lwc():
    folder = SOURCE / "lwc"
    bundles = sorted(d.name for d in folder.iterdir() if d.is_dir() and not d.name.startswith("__"))
    out = ["# Lightning Web Components", "", f"{len(bundles)} components, grouped by the screen they belong to. Generated from the component source.", ""]
    for title, prefixes in LWC_FAMILIES:
        members = [b for b in bundles if b.startswith(prefixes)]
        rows = []
        for name in members:
            js = (folder / name / f"{name}.js").read_text(encoding="utf-8") if (folder / name / f"{name}.js").exists() else ""
            properties = sorted(set(re.findall(r"@api\s+(?:get\s+|set\s+)?(\w+)", js)))
            apex = sorted(set(f"{c}.{m}" for c, m in re.findall(r"@salesforce/apex/(\w+)\.(\w+)", js)))
            rows.append([f"`{name}`", ", ".join(f"`{p}`" for p in properties) or "—", ", ".join(f"`{a}`" for a in apex) or "—"])
        out += [f"## {title}", "", f"{len(members)} components.", "", table(["Component", "Public properties", "Apex methods called"], rows), ""]
    write("reference/lwc.md", "\n".join(out))
    return len(bundles)


# ---------- Permission sets ----------

def write_permission_sets():
    out = ["# Permission sets", "", "Generated from the permission set metadata.", ""]
    for file in sorted((SOURCE / "permissionsets").glob("*.xml")):
        root = ET.parse(file).getroot()
        name = file.name.replace(".permissionset-meta.xml", "")
        out += [f"## {xml_text(root, 'label') or name}", "", f"`{name}`", ""]
        if xml_text(root, "description"):
            out += [" ".join(xml_text(root, "description").split()), ""]
        yes = lambda p, tag: "✓" if xml_text(p, tag) == "true" else ""
        rows = [[f"`{xml_text(p, 'object')}`", yes(p, "allowCreate"), yes(p, "allowRead"), yes(p, "allowEdit"), yes(p, "allowDelete"), yes(p, "viewAllRecords"), yes(p, "modifyAllRecords")] for p in root.findall("m:objectPermissions", NS)]
        out += [table(["Object", "Create", "Read", "Edit", "Delete", "View all", "Modify all"], rows), ""]
        custom = [xml_text(p, "name") for p in root.findall("m:customPermissions", NS) if xml_text(p, "enabled") == "true"]
        classes = [xml_text(p, "apexClass") for p in root.findall("m:classAccesses", NS) if xml_text(p, "enabled") == "true"]
        tabs = [xml_text(p, "tab") for p in root.findall("m:tabSettings", NS) if xml_text(p, "visibility") == "Visible"]
        if custom:
            out += ["**Custom permissions:** " + ", ".join(f"`{c}`" for c in custom), ""]
        out += [f"**Apex classes:** {len(classes)} · **Visible tabs:** {len(tabs)} · **Field permissions:** {len(root.findall('m:fieldPermissions', NS))}", ""]
        if tabs:
            out += ['??? info "Visible tabs"', ""] + [f"    - `{t}`" for t in tabs] + [""]
    write("reference/permission-sets.md", "\n".join(out))


# ---------- Changelog ----------

TYPE_ORDER = ["feat", "fix", "perf", "refactor", "review", "style", "test", "docs", "build", "ci", "chore"]
TYPE_NAMES = {"feat": "features", "fix": "fixes", "perf": "performance", "refactor": "refactors", "review": "review", "style": "style", "test": "tests", "docs": "docs", "build": "build", "ci": "ci", "chore": "chores"}


def write_changelog():
    merges = []
    for line in git("log", "--first-parent", "--merges", "--date=short", "--format=%H|%ad|%s").splitlines():
        sha, date, subject = line.split("|", 2)
        match = re.match(r"Merge pull request #(\d+) from [^/]+/(.+)", subject)
        if match:
            merges.append((sha, date, match.group(1), match.group(2)))
    totals = defaultdict(int)
    months = defaultdict(list)
    for sha, date, number, branch in merges:
        commits = []
        for line in git("log", "--no-merges", "--format=%h|%an|%s", f"{sha}^1..{sha}^2").splitlines():
            short_sha, author, subject = line.split("|", 2)
            kind = re.match(r"^(\w+)(?:\([^)]*\))?!?:\s*(.*)", subject)
            kind_name, text = (kind.group(1).lower(), kind.group(2)) if kind and kind.group(1).lower() in TYPE_ORDER else ("chore", subject)
            totals[kind_name] += 1
            commits.append((kind_name, text, short_sha, author))
        commits.sort(key=lambda c: TYPE_ORDER.index(c[0]))
        months[date[:7]].append((date, number, branch, commits))
    summary = " · ".join(f"**{totals[t]}** {TYPE_NAMES[t]}" for t in TYPE_ORDER if totals[t])
    out = ["# Changelog", "", f"Every change merged into `{BRANCH}`, newest first, rebuilt from git on every deploy. Commit titles follow `type: subject`, so they are grouped by type inside each pull request.", "", summary, ""]
    month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    for month in sorted(months, reverse=True):
        out += [f"## {month_names[int(month[5:]) - 1]} {month[:4]}", ""]
        for date, number, branch, commits in months[month]:
            out += [f"### [#{number}]({GITHUB}/pull/{number}) · {branch} <small>{date}</small>", ""]
            for kind, text, sha, author in commits:
                out.append(f'- <span class="badge badge-{kind}">{TYPE_NAMES[kind]}</span> {text} · [`{sha}`]({GITHUB}/commit/{sha}) <small>{author}</small>')
            out.append("")
    write("changelog.md", "\n".join(out))
    return len(merges)


# ---------- Codebase health ----------

def workflow_triggers(file):
    """Returns (active triggers, switched-off triggers) read from the `on:` block of a workflow file."""
    active, off, inside = [], [], False
    for line in file.read_text(encoding="utf-8").splitlines():
        if re.match(r"^on:", line):
            inside = True
            continue
        if inside and re.match(r"^\S", line):
            break
        if inside:
            match = re.match(r"^  (#\s)?([a-z_]+):", line)
            if match:
                (off if match.group(1) else active).append(match.group(2))
    return active, off


def write_health(classes):
    all_class_names = {f.stem for f in (SOURCE / "classes").glob("*.cls")}
    needs_test = [c for c in classes.values() if c["kind"] == "class" and not c["name"].endswith(("DataStructure", "Exception", "TestStub"))]
    tested = [c for c in needs_test if c["test"]]
    test_methods = sum(c["test"]["methods"] for c in tested)
    lwc_folder = SOURCE / "lwc"
    bundles = sorted(d.name for d in lwc_folder.iterdir() if d.is_dir() and not d.name.startswith("__"))
    with_jest = [b for b in bundles if (lwc_folder / b / "__tests__").exists()]
    violations = [f"Apex class `{n}` does not start with AI or IAI" for n in sorted(all_class_names) if not n.startswith(("AI", "IAI"))]
    violations += [f"Component `{b}` does not start with ai" for b in bundles if not b.startswith("ai")]
    workflows = []
    for file in sorted((ROOT / ".github/workflows").glob("*.yml")):
        active, off = workflow_triggers(file)
        workflows.append((file.name, active, off))
    switched_off = [w for w in workflows if w[2]]
    known = DOCS / "runbooks/known-issues.md"
    open_issues = len(re.findall(r"^\| \[\d+\] \|.*\| Open[^|]*\|\s*$", known.read_text(encoding="utf-8"), re.M)) if known.exists() else 0

    icon = lambda ok: "✅" if ok else "❌"
    checks = [
        ["Apex classes with a test class", f"{len(tested)} of {len(needs_test)} that need one ({test_methods} test methods)", icon(len(tested) == len(needs_test))],
        ["LWC components with Jest tests", f"{len(with_jest)} of {len(bundles)}", icon(len(with_jest) == len(bundles))],
        ["Naming conventions", f"{len(violations)} violation(s)", icon(not violations)],
        ["CI workflows with triggers switched off", f"{len(switched_off)} of {len(workflows)}", icon(not switched_off)],
        ["Open known issues", str(open_issues), "✅" if not open_issues else "⚠️"],
    ]
    out = ["# Codebase health", "", f"Checks worked out from the source on every build. Use this page to see what still stands between `{BRANCH}` and \"bulletproof\".", "", table(["Check", "Result", ""], checks), "",
           "## CI workflows", "", table(["Workflow", "Triggers on", "Switched off"], [[f"`{n}`", ", ".join(a) or "—", ", ".join(o) or "—"] for n, a, o in workflows]), "",
           "## Naming violations", ""]
    out += [f"- {v}" for v in violations] or ["None."]
    sharing_counts = defaultdict(list)
    for c in classes.values():
        sharing_counts[c["sharing"] or "not declared"].append(c["name"])
    out += ["", "## Sharing declarations", "", table(["Declaration", "Classes"], [[k, len(v)] for k, v in sorted(sharing_counts.items())]), ""]
    if sharing_counts.get("not declared"):
        out += ["Classes with no sharing declaration: " + ", ".join(f"`{n}`" for n in sharing_counts["not declared"]), ""]
    largest = sorted(classes.values(), key=lambda c: -c["lines"])[:10]
    out += ["## Largest classes", "", table(["Class", "Lines"], [[f"`{c['name']}`", c["lines"]] for c in largest]), "",
            "## Components without Jest tests", "", f"{len(bundles) - len(with_jest)} of {len(bundles)} components have no Jest test.", ""]
    write("codebase-health.md", "\n".join(out))


# ---------- Home page numbers ----------

def write_stats(classes, object_count, lwc_count, pull_requests):
    test_classes = len(list((SOURCE / "classes").glob("*Test.cls")))
    labels = len(ET.parse(SOURCE / "labels/CustomLabels.labels-meta.xml").getroot().findall("m:labels", NS))
    sha, date, subject = git("log", "-1", "--date=short", "--format=%h|%ad|%s").split("|", 2)
    cards = [(len(classes), f"Apex classes, plus {test_classes} test classes"), (lwc_count, "Lightning Web Components"), (object_count, "Objects, settings, metadata types and events"), (pull_requests, "Pull requests merged")]
    out = ['<div class="grid cards" markdown>', ""]
    for number, text in cards:
        out += [f"- **{number}**{{ .stat }}", f"    {text}", ""]
    out += ["</div>", "", f'<p class="built-from">Built from <code>{sha}</code> on {date}: {subject} · {labels} custom labels</p>']
    write("_stats.md", "\n".join(out))


def main():
    classes = read_apex()
    objects = read_objects()
    write_apex_reference(classes)
    write_data_model(objects)
    lwc_count = write_lwc()
    write_permission_sets()
    pull_requests = write_changelog()
    write_health(classes)
    write_stats(classes, len(objects), lwc_count, pull_requests)
    print(f"{len(classes)} Apex classes, {len(objects)} objects, {lwc_count} components, {pull_requests} pull requests")


if __name__ == "__main__":
    main()
