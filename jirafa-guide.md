# Jirafa Documentation

## Overview

Jirafa is a command-line interface (CLI) tool for interacting with JIRA using the JIRA REST API. It allows users to perform operations like creating tickets, editing ticket fields, listing tickets, and running custom JQL queries, all from the command line.

The tool is written in Python and uses the `Click` library to build the CLI. It also utilizes the `JIRA` library to interact with the JIRA API.

## Features

- **Load configuration**: Load JIRA configuration (credentials, project key) from a TOML file or environment variables.
- **Create JIRA tickets**: Create tickets with a description, priority, and optional linkage to epics.
- **Edit JIRA tickets**: Edit specific fields in existing JIRA tickets.
- **List tickets**: List tickets from a JIRA project with flexible filtering and output formatting (table, CSV, JSON).
- **Run JQL queries**: Run arbitrary JQL queries and output the results in different formats.
- **Add comments**: Add comments to existing JIRA tickets.
- **List projects**: Retrieve and display all JIRA projects.

## Functions

### 1. `load_config(config_file)`

This function loads the configuration data from a TOML file (default: `jirafa.toml`), which contains the JIRA credentials and other settings.

- **Arguments**:
  - `config_file`: Path to the TOML file (default: `jirafa.toml`).
- **Returns**: A dictionary with configuration data.

### 2. `get_jira_client(config)`

This function creates and returns an authenticated JIRA client using credentials from the configuration file or environment variables.

- **Arguments**:
  - `config`: Dictionary containing the JIRA URL, username, and API token.
- **Returns**: Authenticated JIRA client object.

### 3. `safe_getattr(obj, attr_chain, default)`

Safely retrieves nested attributes from an object. If any attribute in the chain is missing, it returns a default value.

- **Arguments**:
  - `obj`: The object to retrieve attributes from.
  - `attr_chain`: Dot-separated string of attributes.
  - `default`: The default value if any attribute is not found.

### 4. `create_jira_ticket(jira, project_key, summary, description_file_path, priority, epic_key, issue_type)`

Creates a new JIRA ticket in the specified project. It also allows the ticket to be linked to an epic.

- **Arguments**:
  - `jira`: Authenticated JIRA client instance.
  - `project_key`: JIRA project key.
  - `summary`: Summary of the ticket.
  - `description_file_path`: Path to a file containing the ticket's description.
  - `priority`: Priority of the ticket (default: 'Medium').
  - `epic_key`: Optional epic key to link the ticket to.
  - `issue_type`: Type of issue (e.g., Task, Bug, Story) (default: 'Task').

### 5. `edit_jira_ticket(jira, issue_key, field_name, new_value)`

Edits a field in an existing JIRA ticket.

- **Arguments**:
  - `jira`: Authenticated JIRA client instance.
  - `issue_key`: Key of the JIRA ticket.
  - `field_name`: Name of the field to update.
  - `new_value`: New value for the field.

### 6. `retrieve_ticket_fields(jira, issue_key, field_names)`

Retrieves specific fields from a JIRA ticket.

- **Arguments**:
  - `jira`: Authenticated JIRA client instance.
  - `issue_key`: Key of the JIRA ticket.
  - `field_names`: List of fields to retrieve.

- **Returns**: A dictionary with field names and their corresponding values.

### 7. `add_comment(jira, issue_key, comment)`

Adds a comment to a JIRA ticket.

- **Arguments**:
  - `jira`: Authenticated JIRA client instance.
  - `issue_key`: Key of the JIRA ticket.
  - `comment`: Comment to be added.

### 8. `list_tickets(jira, project_key, fields, extra_fields, output_format, filters, max_results, items_per_batch)`

Lists tickets in a JIRA project with flexible field and output options.

- **Arguments**:
  - `jira`: Authenticated JIRA client instance.
  - `project_key`: JIRA project key.
  - `fields`: List of fields to display.
  - `extra_fields`: Additional fields to include.
  - `output_format`: Output format (table, CSV, JSON).
  - `filters`: JQL filters to apply.
  - `max_results`: Maximum number of results to fetch.
  - `items_per_batch`: Number of tickets to fetch per batch.

### 9. `list_projects(jira)`

Lists all available JIRA projects.

- **Arguments**:
  - `jira`: Authenticated JIRA client instance.

### 10. `run_jql(jira, jql_query, fields, max_results, items_per_batch, output_format)`

Runs an arbitrary JQL query and returns matching tickets in a specified format.

- **Arguments**:
  - `jira`: Authenticated JIRA client instance.
  - `jql_query`: JQL query string.
  - `fields`: List of fields to display.
  - `max_results`: Maximum number of tickets to return.
  - `items_per_batch`: Number of tickets to fetch per batch.
  - `output_format`: Output format (table, CSV, JSON).

## CLI Commands

The tool uses the `Click` library to define CLI commands.

### 1. `list`

Lists tickets in a project with optional filters and custom output.

#### Usage:

```bash
jirafa.py list <project_key> --fields <fields> --filter <filters> --output <output>
```

### 2. `create`

Creates a new JIRA ticket in the specified project.

#### Usage:

```bash
jirafa.py create <module_name> <description_file> --priority <priority> --epic_key <epic_key> --project_key <project_key> --issue_type <issue_type>
```

### 3. `edit`

Edits a field of an existing JIRA ticket.

#### Usage:

```bash
jirafa.py edit <issue_key> <field_name> <new_value>
```

### 4. `retrieve`

Retrieves specific fields from a JIRA ticket.

#### Usage:

```bash
jirafa.py retrieve <issue_key> <fields>
```

### 5. `comment`

Adds a comment to a JIRA ticket.

#### Usage:

```bash
jirafa.py comment <issue_key> <comment>
```

### 6. `projects`

Lists all available JIRA projects.

#### Usage:

```bash
jirafa.py projects
```

### 7. `jql`

Runs a custom JQL query and returns matching tickets.

#### Usage:

```bash
jirafa.py jql <jql_query> --fields <fields> --max_results <max_results> --items_per_batch <items_per_batch> --output <output>
```

## Usage Example

1. **List tickets in a project**:
   ```bash
   jirafa.py list PROJECT123 --fields summary,status,key --filter status:Done --output table
   ```

2. **Create a new ticket**:
   ```bash
   jirafa.py create module_name description.md --priority High --epic_key EPIC123 --project_key PROJECT123
   ```

3. **Edit a ticket field**:
   ```bash
   jirafa.py edit ISSUE-123 summary "New summary"
   ```

4. **Run a JQL query**:
   ```bash
   jirafa.py jql "project = PROJECT123 AND status = 'To Do'" --fields summary,status,assignee --output json
   ```

This CLI tool is highly flexible and customizable for different JIRA use cases, allowing users to easily manage JIRA issues from the command line.
