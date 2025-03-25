import os
import click
import json
import csv
import tomllib
from jira import JIRA
from tabulate import tabulate
from tqdm import tqdm

# Default configuration file path
CONFIG_FILE = "jirafa.toml"

def load_config(config_file=CONFIG_FILE):
    """
    Loads configuration from a TOML file if available.

    Args:
        config_file (str): Path to the TOML configuration file.

    Returns:
        dict: Configuration data loaded from the file, or an empty dict if file not found.
    """
    config = {}
    if os.path.exists(config_file):
        with open(config_file, "rb") as f:
            config = tomllib.load(f)
    return config

def get_jira_client(config):
    """
    Returns a JIRA client object using credentials from the config, environment variables, or CLI arguments.

    Args:
        config (dict): Configuration data that contains JIRA credentials.

    Returns:
        jira.JIRA: Authenticated JIRA client instance.

    Raises:
        ValueError: If JIRA URL, username, or API token is missing.
    """
    jira_url = config.get('JIRA_URL', os.getenv('JIRA_URL'))
    username = config.get('JIRA_USERNAME', os.getenv('JIRA_USERNAME'))
    api_token = config.get('JIRA_API_TOKEN', os.getenv('JIRA_API_TOKEN'))

    if not jira_url or not username or not api_token:
        raise ValueError("JIRA URL, Username, and API token must be provided either via config, environment, or CLI.")

    return JIRA(server=jira_url, basic_auth=(username, api_token))

def safe_getattr(obj, attr_chain, default=None):
    """
    Helper function to safely access nested attributes within an object. Returns a default value if any attribute
    in the chain is missing.

    Args:
        obj: The object to traverse.
        attr_chain (str): A dot-separated string of nested attribute names.
        default: The value to return if an attribute is missing.

    Returns:
        The value of the attribute or the default value.
    """
    try:
        for attr in attr_chain.split('.'):
            obj = getattr(obj, attr)
        return obj
    except AttributeError:
        return default

def create_jira_ticket(jira, project_key, summary, description_file_path, priority='Medium', epic_key=None, issue_type='Task'):
    """
    Creates a JIRA ticket with the given details and optionally links it to an epic.

    Args:
        jira (jira.JIRA): Authenticated JIRA client instance.
        project_key (str): JIRA project key where the ticket will be created.
        summary (str): Summary of the ticket.
        description_file_path (str): Path to the file containing the ticket description.
        priority (str, optional): Priority of the ticket (default is 'Medium').
        epic_key (str, optional): Epic key to link the ticket to (default is None).
        issue_type (str, optional): Issue type, e.g., Task, Story, Bug (default is 'Task').

    Returns:
        jira.Issue: The created JIRA issue object.

    Raises:
        FileNotFoundError: If the provided description file path does not exist.
    """
    if os.path.exists(description_file_path):
        with open(description_file_path, 'r') as file:
            description = file.read()
    else:
        raise FileNotFoundError(f"Markdown file {description_file_path} not found.")

    issue_fields = {
        'project': {'key': project_key},
        'summary': summary,
        'description': description,
        'issuetype': {'name': issue_type},
        'priority': {'name': priority},
    }

    issue = jira.create_issue(fields=issue_fields)
    click.echo(f"Created issue {issue.key}")

    if epic_key:
        jira.add_issues_to_epic(epic_key, [issue.key])
        click.echo(f"Issue {issue.key} linked to epic {epic_key}")

    return issue

def edit_jira_ticket(jira, issue_key, field_name, new_value):
    """
    Edit a specific field of a JIRA ticket.

    Args:
        jira (jira.JIRA): Authenticated JIRA client instance.
        issue_key (str): Key of the JIRA ticket to be edited.
        field_name (str): The field to be updated.
        new_value: The new value for the field.
    """
    issue = jira.issue(issue_key)
    issue.update(fields={field_name: new_value})
    click.echo(f"Updated {field_name} of {issue_key} to {new_value}")

def retrieve_ticket_fields(jira, issue_key, field_names):
    """
    Retrieve specific fields from a JIRA ticket.

    Args:
        jira (jira.JIRA): Authenticated JIRA client instance.
        issue_key (str): Key of the JIRA ticket.
        field_names (list): List of field names to retrieve.

    Returns:
        dict: A dictionary of field names and their corresponding values from the JIRA ticket.
    """
    issue = jira.issue(issue_key)
    result = {}
    for field_name in field_names:
        field_value = safe_getattr(issue.fields, field_name, 'Field not found')
        if hasattr(field_value, '__dict__'):
            field_value = str(field_value)
        result[field_name] = field_value
    return result

def add_comment(jira, issue_key, comment):
    """
    Add a comment to a JIRA ticket.

    Args:
        jira (jira.JIRA): Authenticated JIRA client instance.
        issue_key (str): Key of the JIRA ticket.
        comment (str): Comment to be added.
    """
    jira.add_comment(issue_key, comment)
    click.echo(f"Added comment to {issue_key}")

def list_tickets(jira, project_key, fields=['summary', 'status', 'key'], extra_fields=None, output_format='table', filters=None, max_results=0, items_per_batch=50):
    """
    List JIRA tickets from a project, with flexible field and output options.

    Args:
        jira (jira.JIRA): Authenticated JIRA client instance.
        project_key (str): JIRA project key to list tickets from.
        fields (list, optional): List of fields to include in the output (default is ['summary', 'status', 'key']).
        extra_fields (list, optional): Additional fields to include (default is None).
        output_format (str, optional): Format of the output - 'table', 'csv', or 'json' (default is 'table').
        filters (list, optional): List of JQL filters to apply (default is None).
        max_results (int, optional): Maximum number of tickets to return (default is 0, meaning all).
        items_per_batch (int, optional): Number of items to retrieve per batch (default is 50).

    Returns:
        None
    """
    if 'key' not in fields:
        fields.append('key')

    # Prepare the JQL query
    jql_query = f"project = {project_key}"

    # Add filters to the JQL query
    if filters:
        filter_query = " AND ".join(filters)
        jql_query += f" AND {filter_query}"

    all_fields = fields + (extra_fields or [])
    start_at = 0
    total_issues = []

    while True:
        batch_size = min(items_per_batch, max_results - len(total_issues)) if max_results > 0 else items_per_batch
        issues = jira.search_issues(jql_query, fields=all_fields, startAt=start_at, maxResults=batch_size)
        if not issues:
            break
        total_issues.extend(issues)
        start_at += len(issues)
        if len(issues) < batch_size or (max_results > 0 and len(total_issues) >= max_results):
            break

    tickets_data = []

    if output_format == 'table':
        for issue in total_issues:
            ticket = []
            for field in fields:
                if field == 'key':
                    ticket.append(issue.key)
                else:
                    field_value = safe_getattr(issue.fields, field, 'N/A')
                    if hasattr(field_value, '__dict__'):
                        field_value = str(field_value)
                    ticket.append(field_value)
            tickets_data.append(ticket)
    else:
        for issue in total_issues:
            ticket = {}
            for field in fields:
                if field == 'key':
                    ticket['key'] = issue.key
                else:
                    field_value = safe_getattr(issue.fields, field, 'N/A')
                    if hasattr(field_value, '__dict__'):
                        field_value = str(field_value)
                    ticket[field] = field_value
            tickets_data.append(ticket)

    if output_format == 'table':
        headers = fields
        click.echo(tabulate(tickets_data, headers=headers, tablefmt="plain"))
    elif output_format == 'csv':
        with open(f'{project_key}_tickets.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(fields)
            for ticket in tickets_data:
                writer.writerow([ticket.get(field, 'N/A') for field in fields])
        click.echo(f"Data written to {project_key}_tickets.csv")
    elif output_format == 'json':
        with open(f'{project_key}_tickets.json', 'w') as jsonfile:
            json.dump(tickets_data, jsonfile, indent=4)
        click.echo(f"Data written to {project_key}_tickets.json")

def list_projects(jira):
    """
    List all available JIRA projects.

    Args:
        jira (jira.JIRA): Authenticated JIRA client instance.

    Returns:
        None
    """
    projects = jira.projects()
    click.echo("Available JIRA Projects:")
    for project in projects:
        click.echo(f"{project.key} - {project.name}")

def get_ticket_comments(jira, issue_key, filters=None, max_results=0, output_format='table'):
    """
    Retrieve comments from a JIRA ticket with optional filtering.

    Args:
        jira (jira.JIRA): Authenticated JIRA client instance.
        issue_key (str): Key of the JIRA ticket.
        filters (list, optional): List of filters to apply to comments (e.g., author, date, text).
        max_results (int, optional): Maximum number of comments to retrieve (default is 0, meaning all).
        output_format (str, optional): Format of the output - 'table', 'csv', or 'json' (default is 'table').

    Returns:
        list: Comments data in the requested format.
    """
    issue = jira.issue(issue_key)
    comments = jira.comments(issue)

    # Apply filters if provided
    filtered_comments = []
    for comment in comments:
        include_comment = True

        if filters:
            for filter_str in filters:
                try:
                    field, value = filter_str.split(":", 1)
                    field = field.lower().strip()
                    value = value.lower().strip('"\'')

                    if field == "author" and value not in comment.author.displayName.lower():
                        include_comment = False
                        break
                    elif field == "text" and value not in comment.body.lower():
                        include_comment = False
                        break
                    elif field == "date":
                        # Parse date ranges or specific dates
                        comment_date = comment.created[:10]  # Get YYYY-MM-DD part
                        if "to" in value:
                            start_date, end_date = value.split("to")
                            if (comment_date < start_date.strip() or
                                comment_date > end_date.strip()):
                                include_comment = False
                                break
                        elif comment_date != value:
                            include_comment = False
                            break
                except (ValueError, AttributeError) as e:
                    click.echo(f"Warning: Invalid filter format or field: {filter_str}. Error: {e}", err=True)
                    continue

        if include_comment:
            filtered_comments.append(comment)

    # Apply max_results limitation
    if max_results > 0 and len(filtered_comments) > max_results:
        filtered_comments = filtered_comments[:max_results]

    comments_data = []

    # Format the comments based on the requested output format
    for comment in filtered_comments:
        comment_data = {
            'id': comment.id,
            'author': comment.author.displayName,
            'date': comment.created[:19],  # Keep only YYYY-MM-DD HH:MM:SS
            'body': comment.body
        }

        if output_format == 'table':
            comments_data.append([
                comment_data['id'],
                comment_data['author'],
                comment_data['date'],
                comment_data['body'][:50] + ('...' if len(comment_data['body']) > 50 else '')
            ])
        else:
            comments_data.append(comment_data)

    # Output the comments in the requested format
    if output_format == 'table':
        headers = ['ID', 'Author', 'Date', 'Comment']
        click.echo(tabulate(comments_data, headers=headers, tablefmt="plain"))
    elif output_format == 'csv':
        with open(f'{issue_key}_comments.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['ID', 'Author', 'Date', 'Comment'])
            for comment in comments_data:
                writer.writerow([comment['id'], comment['author'], comment['date'], comment['body']])
        click.echo(f"Comments written to {issue_key}_comments.csv")
    elif output_format == 'json':
        with open(f'{issue_key}_comments.json', 'w') as jsonfile:
            json.dump(comments_data, jsonfile, indent=4)
        click.echo(f"Comments written to {issue_key}_comments.json")

    return comments_data

def run_jql(jira, jql_query, fields=['summary', 'status', 'assignee', 'key'], max_results=0, items_per_batch=50, output_format='table'):
    """
    Run an arbitrary JQL query and return all matching tickets.

    Args:
        jira (jira.JIRA): Authenticated JIRA client instance.
        jql_query (str): JQL query string to execute.
        fields (list, optional): List of fields to include in the output (default is ['summary', 'status', 'assignee', 'key']).
        max_results (int, optional): Maximum number of tickets to retrieve (default is 0, meaning all).
        items_per_batch (int, optional): Number of items to retrieve per batch (default is 50).
        output_format (str, optional): Output format - 'table', 'csv', or 'json' (default is 'table').

    Returns:
        None
    """
    start_at = 0
    total_issues = []

    if max_results == 0:
        total_issues_count = jira.search_issues(jql_query, fields="id", maxResults=0).total
        click.echo(f"Total tickets found: {total_issues_count}")
    else:
        total_issues_count = min(max_results, jira.search_issues(jql_query, fields="id", maxResults=0).total)
        click.echo(f"Fetching a maximum of {max_results} tickets (out of {total_issues_count} found).")

    num_batches = (total_issues_count // items_per_batch) + (1 if total_issues_count % items_per_batch else 0)
    click.echo(f"Will fetch in {num_batches} batch(es) of {items_per_batch} items.")

    progress_bar = tqdm(total=total_issues_count, desc="Fetching tickets", unit="tickets")

    while start_at < total_issues_count:
        batch_size = min(items_per_batch, total_issues_count - start_at)
        issues = jira.search_issues(jql_query, fields=fields, startAt=start_at, maxResults=batch_size)

        if not issues:
            break

        total_issues.extend(issues)
        progress_bar.update(len(issues))
        start_at += len(issues)

        if max_results > 0 and len(total_issues) >= max_results:
            total_issues = total_issues[:max_results]
            break

    progress_bar.close()

    tickets_data = []
    for issue in total_issues:
        ticket = [
            getattr(issue.fields, 'summary', 'N/A'),
            safe_getattr(issue.fields, 'status.name', 'N/A'),
            safe_getattr(issue.fields, 'assignee.displayName', 'Unassigned'),
            issue.key
        ]
        tickets_data.append(ticket)

    if output_format == 'table':
        click.echo(tabulate(tickets_data, headers=fields, tablefmt="plain"))
    elif output_format == 'csv':
        with open('jql_query_tickets.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(fields)
            writer.writerows(tickets_data)
        click.echo("Data written to jql_query_tickets.csv")
    elif output_format == 'json':
        tickets_json = [dict(zip(fields, ticket)) for ticket in tickets_data]
        with open('jql_query_tickets.json', 'w') as jsonfile:
            json.dump(tickets_json, jsonfile, indent=4)
        click.echo("Data written to jql_query_tickets.json")

# CLI definition using Click
@click.group()
@click.pass_context
def cli(ctx):
    """
    Jirafa: A command-line tool to interact with JIRA API for creating, retrieving, editing, and managing tickets.
    """
    ctx.obj = load_config()

@cli.command()
@click.argument('project_key')
@click.option('--fields', default="summary,status,key", help="Comma-separated list of fields to display")
@click.option('--filter', '-f', multiple=True, help="Field filter in key:value format, e.g., 'status:Done'")
@click.option('--output', default="table", type=click.Choice(['table', 'csv', 'json'], case_sensitive=False), help="Output format")
@click.pass_context
def list(ctx, project_key, fields, filter, output):
    """
    List tickets in a JIRA project with optional filters and custom output.

    Args:
        project_key (str): JIRA project key.
        fields (str): Comma-separated list of fields to display.
        filter (tuple): Key:value pairs for field filters.
        output (str): Output format - table, csv, or json.
    """
    jira = get_jira_client(ctx.obj)
    fields = fields.split(",")

    filters = []
    if filter:
        for f in filter:
            key, value = f.split(":", 1)
            value = value.strip('"')
            filters.append(f"{key} = '{value}'")

    list_tickets(jira, project_key, fields=fields, filters=filters, output_format=output)

@cli.command()
@click.argument('module_name')
@click.argument('description_file')
@click.option('--priority', default="Medium", help="Priority of the ticket")
@click.option('--epic_key', help="Epic key to link the ticket to")
@click.option('--project_key', default=None, help="JIRA project key")
@click.option('--issue_type', default="Task", help="Issue type, e.g., Task, Story, Bug")
@click.pass_context
def create(ctx, module_name, description_file, priority, epic_key, project_key, issue_type):
    """
    Create a new JIRA ticket.

    Args:
        module_name (str): Name of the module related to the ticket.
        description_file (str): Path to the file containing the ticket description.
        priority (str): Priority of the ticket.
        epic_key (str, optional): Epic key to link the ticket to.
        project_key (str): JIRA project key.
        issue_type (str): Type of issue (Task, Story, Bug, etc.).
    """
    jira = get_jira_client(ctx.obj)
    project_key = project_key or ctx.obj.get('JIRA_PROJECT_KEY', os.getenv('JIRA_PROJECT_KEY'))
    if not project_key:
        click.echo("Error: No project key provided.", err=True)
        sys.exit(1)
    summary = f"Update {module_name} for Python 3.12 Compatibility"
    create_jira_ticket(jira, project_key, summary, description_file, priority, epic_key, issue_type)

@cli.command()
@click.argument('issue_key')
@click.argument('field_name')
@click.argument('new_value')
@click.pass_context
def edit(ctx, issue_key, field_name, new_value):
    """
    Edit a specific field of a JIRA ticket.

    Args:
        issue_key (str): JIRA ticket key.
        field_name (str): The field to be updated.
        new_value (str): New value for the field.
    """
    jira = get_jira_client(ctx.obj)
    edit_jira_ticket(jira, issue_key, field_name, new_value)

@cli.command()
@click.argument('issue_key')
@click.argument('fields', nargs=-1)
@click.pass_context
def retrieve(ctx, issue_key, fields):
    """
    Retrieve specific fields from a JIRA ticket.

    Args:
        issue_key (str): JIRA ticket key.
        fields (tuple): List of fields to retrieve.
    """
    jira = get_jira_client(ctx.obj)
    fields_data = retrieve_ticket_fields(jira, issue_key, fields)
    click.echo(json.dumps(fields_data, indent=4))

@cli.command()
@click.argument('issue_key')
@click.argument('comment')
@click.pass_context
def comment(ctx, issue_key, comment):
    """
    Add a comment to a JIRA ticket.

    Args:
        issue_key (str): JIRA ticket key.
        comment (str): Comment to be added.
    """
    jira = get_jira_client(ctx.obj)
    add_comment(jira, issue_key, comment)

@cli.command()
@click.pass_context
def projects(ctx):
    """
    List all available JIRA projects.
    """
    jira = get_jira_client(ctx.obj)
    list_projects(jira)

@cli.command()
@click.argument('jql_query')
@click.option('--fields', default="summary,status,assignee,key", help="Comma-separated list of fields to display")
@click.option('--max_results', default=None, help="Maximum number of tickets to fetch (0 for all)")
@click.option('--items_per_batch', default=None, help="Number of items to fetch per batch/page (default 50)")
@click.option('--output', default="table", type=click.Choice(['table', 'csv', 'json'], case_sensitive=False), help="Output format")
@click.pass_context
def jql(ctx, jql_query, fields, max_results, items_per_batch, output):
    """
    Run an arbitrary JQL query and list matching tickets.

    Args:
        jql_query (str): JQL query string.
        fields (str): Comma-separated list of fields to display.
        max_results (int, optional): Maximum number of tickets to fetch.
        items_per_batch (int, optional): Number of items per batch/page.
        output (str): Output format - table, csv, or json.
    """
    jira = get_jira_client(ctx.obj)
    config = ctx.obj

    max_results = int(max_results) if max_results is not None else int(config.get('DEFAULT_MAX_RESULTS', 0))
    items_per_batch = int(items_per_batch) if items_per_batch is not None else int(config.get('ITEMS_PER_BATCH', 50))

    fields = fields.split(",")
    run_jql(jira, jql_query, fields=fields, max_results=max_results, items_per_batch=items_per_batch, output_format=output)

@cli.command()
@click.argument('issue_key')
@click.option('--filter', '-f', multiple=True, help="Filter comments in key:value format, e.g., 'author:JohnDoe', 'text:important', 'date:2023-01-01'")
@click.option('--max_results', default=0, help="Maximum number of comments to fetch (0 for all)")
@click.option('--output', default="table", type=click.Choice(['table', 'csv', 'json'], case_sensitive=False), help="Output format")
@click.pass_context
def comments(ctx, issue_key, filter, max_results, output):
    """
    Retrieve comments from a JIRA ticket with optional filtering.

    Args:
        issue_key (str): JIRA ticket key.
        filter (tuple): Key:value pairs for comment filters (author, text, date).
        max_results (int): Maximum number of comments to fetch.
        output (str): Output format - table, csv, or json.
    """
    jira = get_jira_client(ctx.obj)
    max_results = int(max_results)
    get_ticket_comments(jira, issue_key, filters=filter, max_results=max_results, output_format=output)

if __name__ == '__main__':
    cli()
