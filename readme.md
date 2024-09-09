# JIRA Ticket Utility Tool

## Overview

The **JIRA Ticket Utility Tool** is a command-line interface (CLI) that allows you to interact with JIRA from your terminal. You can create, edit, retrieve, list, and run queries on JIRA tickets using this tool. It provides various output formats (table, JSON, CSV) and supports complex JQL queries.

## Features

- **Create JIRA tickets** with descriptions, priority, and optional linkage to epics.
- **Edit JIRA tickets** by updating specific fields.
- **List JIRA tickets** from a project with custom filters and flexible output formats.
- **Run custom JQL queries** to retrieve tickets that match specific criteria.
- **Add comments** to JIRA tickets.
- **List all available JIRA projects**.

## Installation

1. Clone the repository:

    ```bash
    git clone <repository-url>
    ```

2. Navigate into the project directory:

    ```bash
    cd jirafa
    ```

3. Install the dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Configuration

The tool requires JIRA credentials to interact with the JIRA API. You can provide this information through:

1. **Environment variables**:
   - `JIRA_URL`
   - `JIRA_USERNAME`
   - `JIRA_API_TOKEN`
   
2. **TOML configuration file** (`jirafa.toml`):
   
   Example `jirafa.toml` file:

    ```toml
    JIRA_URL = "https://your-domain.atlassian.net"
    JIRA_USERNAME = "your-email@example.com"
    JIRA_API_TOKEN = "your-api-token"
    JIRA_PROJECT_KEY = "PROJECT_KEY"
    ```

## Usage

### 1. List tickets in a project

```bash
python jirafa.py list <project_key> --fields summary,status,key --filter status:Done --output table
```

### 2. Create a new ticket

```bash
python jirafa.py create <module_name> <description_file> --priority High --epic_key EPIC-123 --project_key PROJECT-123
```

### 3. Edit a ticket field

```bash
python jirafa.py edit <issue_key> <field_name> <new_value>
```

### 4. Run a JQL query

```bash
python jirafa.py jql "project = PROJECT123 AND status = 'To Do'" --fields summary,status,assignee --output json
```

### 5. Add a comment to a ticket

```bash
python jirafa.py comment <issue_key> "This is a comment."
```

### 6. List all JIRA projects

```bash
python jirafa.py projects
```

## Command Overview

- `list`: List tickets in a JIRA project.
- `create`: Create a new JIRA ticket.
- `edit`: Edit a field in an existing JIRA ticket.
- `retrieve`: Retrieve specific fields from a JIRA ticket.
- `comment`: Add a comment to a JIRA ticket.
- `projects`: List all available JIRA projects.
- `jql`: Run a custom JQL query and list matching tickets.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Troubleshooting

- Ensure that your JIRA credentials (URL, username, and API token) are correctly set in the environment or in the `jirafa.toml` file.
- If you encounter issues with API access, verify that your JIRA account has the correct permissions to interact with the JIRA API.

---

**Contributions** are welcome! Feel free to open an issue or submit a pull request if you have ideas for improvements or new features.
