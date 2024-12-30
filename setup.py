#!/usr/bin/env python3
import os
import json
import argparse
import logging
import sys
from project_detector import scan_for_projects
from analyzers.dependency_analyzer import DependencyAnalyzer
from analyzers.git_analyzer import GitAnalyzer

# Add current directory to PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_launch_agent(project_path, python_path='/usr/local/bin/python3'):
    """Create and install the LaunchAgent plist file."""
    home = os.path.expanduser('~')
    launch_agents_dir = os.path.join(home, 'Library/LaunchAgents')
    plist_path = os.path.join(launch_agents_dir, 'com.cursorfocus.plist')
    
    # Create LaunchAgents directory if it doesn't exist
    os.makedirs(launch_agents_dir, exist_ok=True)
    
    plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cursorfocus</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>{os.path.join(project_path, 'focus.py')}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{project_path}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{os.path.join(project_path, 'cursorfocus.log')}</string>
    <key>StandardErrorPath</key>
    <string>{os.path.join(project_path, 'cursorfocus.error.log')}</string>
</dict>
</plist>'''

    # Write the plist file
    with open(plist_path, 'w') as f:
        f.write(plist_content)
    
    # Set proper permissions
    os.chmod(plist_path, 0o644)
    
    return plist_path

def setup_cursorfocus():
    """Set up CursorFocus for multiple projects."""
    parser = argparse.ArgumentParser(description='Set up CursorFocus for your projects')
    parser.add_argument('--projects', '-p', nargs='+', help='Paths to projects to monitor')
    parser.add_argument('--names', '-n', nargs='+', help='Names for the projects (optional)')
    parser.add_argument('--intervals', '-i', nargs='+', type=int, help='Update intervals in seconds for each project')
    parser.add_argument('--depths', '-d', nargs='+', type=int, help='Maximum directory depths for each project')
    parser.add_argument('--install-agent', '-I', action='store_true', help='Install LaunchAgent for automatic startup')
    parser.add_argument('--list', '-l', action='store_true', help='List all configured projects')
    parser.add_argument('--remove', '-r', nargs='+', help='Remove projects by name or index')
    parser.add_argument('--clear', '-c', action='store_true', help='Remove all projects')
    parser.add_argument('--scan', '-s', nargs='?', const='.', 
                       help='Scan directory for projects. If no path provided, scans current directory')
    parser.add_argument('--scan-depth', type=int, default=3, help='Maximum depth for project scanning')
    parser.add_argument('--auto-add', '-a', action='store_true', help='Automatically add all found projects')
    parser.add_argument('--analyze-deps', '-D', action='store_true', 
                       help='Analyze project dependencies')
    parser.add_argument('--analyze-git', '-G', action='store_true',
                       help='Analyze Git repository')
    parser.add_argument('--output-dir', '-o', default='reports',
                       help='Directory for analysis reports')
    
    args = parser.parse_args()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.json')
    
    config = load_or_create_config(config_path)
    
    if 'projects' not in config:
        config['projects'] = []

    if args.list:
        list_projects(config['projects'])
        return

    if args.clear:
        if confirm_action("Are you sure you want to remove all projects?"):
            config['projects'] = []
            save_config(config_path, config)
            print("\n✅ All projects have been removed.")
        return

    if args.remove:
        remove_projects(config, args.remove)
        save_config(config_path, config)
        return

    # Handle scan option
    if args.scan is not None:
        scan_path = os.path.abspath(args.scan) if args.scan else os.getcwd()
        
        print(f"\n🔍 Scanning for projects in: {scan_path}")
        found_projects = scan_for_projects(scan_path, args.scan_depth)
        
        if not found_projects:
            print("No projects found.")
            return
            
        print(f"\nFound {len(found_projects)} projects:")
        for i, project in enumerate(found_projects, 1):
            print(f"\n  {i}. {project['name']} ({project['type']})")
            print(f"     Path: {project['path']}")
        
        if args.auto_add:
            # Automatically add all found projects
            added = 0
            for project in found_projects:
                if not any(p['project_path'] == project['path'] for p in config['projects']):
                    config['projects'].append({
                        'name': project['name'],
                        'project_path': project['path'],
                        'update_interval': 60,
                        'max_depth': 3
                    })
                    added += 1
            print(f"\n✅ Added {added} new projects to configuration")
        else:
            # Ask which projects to add
            print("\nSelect projects to add (enter numbers separated by space, 'all', or 'q' to quit):")
            try:
                selection = input("> ").strip().lower()
                
                if selection in ['q', 'quit', 'exit']:
                    print("\n❌ Operation cancelled.")
                    return
                    
                if selection == 'all':
                    indices = range(len(found_projects))
                else:
                    try:
                        indices = [int(i) - 1 for i in selection.split()]
                        # Validate indices
                        if any(i < 0 or i >= len(found_projects) for i in indices):
                            print("\n❌ Invalid project number(s). Operation cancelled.")
                            return
                    except ValueError:
                        print("\n❌ Invalid input. Operation cancelled.")
                        return
                
                # Add selected projects
                added = 0
                for idx in indices:
                    project = found_projects[idx]
                    if not any(p['project_path'] == project['path'] for p in config['projects']):
                        config['projects'].append({
                            'name': project['name'],
                            'project_path': project['path'],
                            'update_interval': 60,
                            'max_depth': 3
                        })
                        added += 1
                    else:
                        print(f"\n⚠️  Project already exists: {project['name']}")
                
                if added > 0:
                    print(f"\n✅ Added {added} new projects to configuration")
                else:
                    print("\n⚠️  No new projects were added")
                    
            except KeyboardInterrupt:
                print("\n\n❌ Operation cancelled.")
                return
        
        if config['projects']:  # Only save if we have projects
            save_config(config_path, config)
        return

    # Add/update projects
    if args.projects:
        # Validate project paths first
        valid_projects = []
        for i, project_path in enumerate(args.projects):
            abs_path = os.path.abspath(project_path)
            if not os.path.exists(abs_path):
                print(f"\n⚠️  Warning: Project path does not exist: {abs_path}")
                continue
                
            project_config = {
                'name': args.names[i] if args.names and i < len(args.names) else f"Project {i+1}",
                'project_path': abs_path,
                'update_interval': args.intervals[i] if args.intervals and i < len(args.intervals) else 60,
                'max_depth': args.depths[i] if args.depths and i < len(args.depths) else 3
            }
            valid_projects.append(project_config)
            
        # Check for duplicate names
        names = [p['name'] for p in valid_projects]
        if len(names) != len(set(names)):
            print("\n⚠️  Warning: Duplicate project names found. Adding unique suffixes...")
            name_counts = {}
            for project in valid_projects:
                base_name = project['name']
                if base_name in name_counts:
                    name_counts[base_name] += 1
                    project['name'] = f"{base_name} ({name_counts[base_name]})"
                else:
                    name_counts[base_name] = 1
        
        # Update existing projects or add new ones
        for project in valid_projects:
            existing = next((p for p in config['projects'] if p['project_path'] == project['project_path']), None)
            if existing:
                existing.update(project)
            else:
                config['projects'].append(project)

    # Save the config
    save_config(config_path, config)
    
    # Install LaunchAgent if requested
    if args.install_agent:
        try:
            python_path = args.python_path or '/usr/local/bin/python3'
            if not os.path.exists(python_path):
                print("⚠️  Warning: Default Python path not found. Please specify with --python-path")
                return
            
            plist_path = create_launch_agent(script_dir, python_path)
            print(f"\n✅ LaunchAgent installed at: {plist_path}")
            print("CursorFocus will now start automatically at login")
            print("\nTo start now:")
            print(f"$ launchctl load {plist_path}")
            print("\nTo stop:")
            print(f"$ launchctl unload {plist_path}")
        except Exception as e:
            print(f"\n❌ Error installing LaunchAgent: {e}")
            print("Please check permissions and try again")
    
    print("\n✅ CursorFocus configuration updated!")
    print("\n📁 Configured projects:")
    for project in config['projects']:
        print(f"\n  • {project['name']}:")
        print(f"    Path: {project['project_path']}")
        print(f"    Update interval: {project['update_interval']} seconds")
        print(f"    Max depth: {project['max_depth']} levels")
    
    print("\nTo start monitoring all projects, run:")
    print(f"python3 {os.path.join(script_dir, 'focus.py')}")

    # Process analysis if requested
    if args.analyze_deps or args.analyze_git:
        for project in config['projects']:
            project_path = project['project_path']
            
            # Create reports directory if it doesn't exist
            reports_dir = os.path.join(project_path, args.output_dir)
            os.makedirs(reports_dir, exist_ok=True)
            
            if args.analyze_deps:
                print(f"\n📦 Analyzing dependencies for {project['name']}...")
                try:
                    dep_analyzer = DependencyAnalyzer(project_path)
                    dep_report = dep_analyzer.generate_report()
                    
                    report_path = os.path.join(reports_dir, 'dependencies.md')
                    # Add encoding='utf-8' when writing file
                    with open(report_path, 'w', encoding='utf-8') as f:
                        f.write(dep_report)
                    print(f"✅ Dependencies report saved to: {report_path}")
                except Exception as e:
                    print(f"❌ Error analyzing dependencies: {str(e)}")
                
            if args.analyze_git:
                print(f"\n🔍 Analyzing Git repository for {project['name']}...")
                try:
                    git_analyzer = GitAnalyzer(project_path)
                    git_report = git_analyzer.generate_report()
                    
                    report_path = os.path.join(reports_dir, 'git_analysis.md')
                    # Add encoding='utf-8' when writing file
                    with open(report_path, 'w', encoding='utf-8') as f:
                        f.write(git_report)
                    print(f"✅ Git analysis report saved to: {report_path}")
                except Exception as e:
                    print(f"❌ Error analyzing git repository: {str(e)}")

def load_or_create_config(config_path):
    """Load existing config or create default one."""
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return get_default_config()

def get_default_config():
    """Return default configuration."""
    return {
        "projects": [],
        "ignored_directories": [
            "__pycache__",
            "node_modules",
            "venv",
            ".git",
            ".idea",
            ".vscode",
            "dist",
            "build"
        ],
        "ignored_files": [
            ".DS_Store",
            "*.pyc",
            "*.pyo"
        ]
    }

def save_config(config_path, config):
    """Save configuration to file."""
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

def list_projects(projects):
    """Display list of configured projects."""
    if not projects:
        print("\n📁 No projects configured.")
        return
        
    print("\n📁 Configured projects:")
    for i, project in enumerate(projects, 1):
        print(f"\n  {i}. {project['name']}:")
        print(f"     Path: {project['project_path']}")
        print(f"     Update interval: {project['update_interval']} seconds")
        print(f"     Max depth: {project['max_depth']} levels")

def remove_projects(config, targets):
    """Remove specific projects by name or index."""
    if not config['projects']:
        print("\n⚠️ No projects configured.")
        return
        
    remaining_projects = []
    removed = []
    
    for project in config['projects']:
        should_keep = True
        
        for target in targets:
            # Check if target is an index
            try:
                idx = int(target)
                if idx == config['projects'].index(project) + 1:
                    should_keep = False
                    removed.append(project['name'])
                    break
            except ValueError:
                # Target is a name
                if project['name'].lower() == target.lower():
                    should_keep = False
                    removed.append(project['name'])
                    break
                    
        if should_keep:
            remaining_projects.append(project)
    
    if removed:
        config['projects'] = remaining_projects
        print(f"\n✅ Removed projects: {', '.join(removed)}")
    else:
        print("\n⚠️ No matching projects found.")

def confirm_action(message):
    """Ask for user confirmation."""
    while True:
        response = input(f"\n{message} (y/n): ").lower()
        if response in ['y', 'yes']:
            return True
        if response in ['n', 'no']:
            return False

if __name__ == '__main__':
    setup_cursorfocus() 