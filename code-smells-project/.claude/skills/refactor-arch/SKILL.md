---
name: refactor-arch
description: Refactor the architecture of the project MVC to improve performance, maintainability, and scalability independently of stack technology.
---

# Refactor Architecture

summary: Refactor the architecture of the project to improve performance, maintainability, and scalability independently of stack technology.
general: Save all output reports in the `/docs` folder of the project.

## Phase 1: Detect tecnology stack and architecture
- Detect the technology stack used in the project (e.g., programming languages, frameworks, libraries, databases, etc.).

### Input
- Project source code and configuration files.

### Output (Sample)
- [project_analises_tpl](./templates/project_analysis.txt)


## Phase 2: Detect code smells and architecture issues antipatterns
- Detect code smells and architecture issues antipatterns in the project.
- Order findings by severity level (Critical, High, Medium, Low) based on the [issues_severity_ref](./references/issues_severity.md).
- Identify minimal of 5 code smells and architecture issues antipatterns in the project.
- Detect deprecated APIs if aplicable. 

### Input
- Project source code and configuration files.
- [issues_severity_ref](./references/issues_severity.md)

### Output (Sample)
- [project_issues_tpl_report](./templates/project_issues.txt)

- Present the findings in a structured format, including the severity level, description, and location of each issue.
- Ask the user to confirm to proceed to phase 3 (Refactor the architecture) or to stop the process.

## Phase 3: Refactor the architecture
- Refactor the project fixing the detected code smells and architecture issues antipatterns.
- Refactor the project to adopt **MVC (Model-View-Controller)** architecture pattern, ensuring a clear separation of concerns between the Model, View, and Controller components.
- Validate the refactored code to ensure that project functionallity is preserved and that the project still run.
- Update the `README.md` and `AGENTS.md` files to reflect the new architecture and any changes made during the refactoring process.

### Output (Sample of the refactored code report)
- [project_refactored_tpl_report](./templates/project_refactored.txt)
