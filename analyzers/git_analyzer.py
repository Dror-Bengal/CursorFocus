import os
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict
from .base_analyzer import BaseAnalyzer

class GitAnalyzer(BaseAnalyzer):
    def __init__(self, project_path: str):
        super().__init__(project_path)
        self._validate_git_repo()

    def _validate_git_repo(self) -> None:
        """Validate that the project path contains a Git repository."""
        if not os.path.exists(os.path.join(self.project_path, '.git')):
            raise ValueError(f"No Git repository found in {self.project_path}")

    def analyze(self) -> Dict:
        """Analyze Git repository metrics."""
        return self.safe_execute(
            lambda: {
                'commit_history': self._analyze_commit_history(),
                'code_churn': self._analyze_code_churn(),
                'contributor_stats': self._analyze_contributors(),
                'branch_stats': self._analyze_branches(),
                'hotspots': self._identify_hotspots()
            },
            "Error analyzing git repository",
            self._get_empty_analysis()
        )

    def _run_git_command(self, args: List[str]) -> str:
        """Run a git command safely."""
        return self.safe_execute(
            lambda: subprocess.run(
                ['git'] + args,
                capture_output=True,
                text=True,
                cwd=self.project_path
            ).stdout.strip(),
            f"Error running git command: {' '.join(args)}",
            ""
        )

    def _analyze_commit_history(self) -> Dict:
        """Analyze commit history patterns."""
        history = {
            'total_commits': 0,
            'commit_frequency': defaultdict(int),
            'commit_times': defaultdict(int),
            'recent_activity': [],
            'largest_commits': []
        }

        # Get commit history
        log = self._run_git_command([
            'log', '--pretty=format:%h|%an|%at|%s', '--shortstat'
        ])

        current_commit = None
        for line in log.split('\n'):
            if '|' in line:  # Commit info line
                hash, author, timestamp, message = line.split('|')
                date = datetime.fromtimestamp(int(timestamp))
                
                history['total_commits'] += 1
                history['commit_frequency'][date.strftime('%Y-%m')] += 1
                history['commit_times'][date.strftime('%H')] += 1
                
                current_commit = {
                    'hash': hash,
                    'author': author,
                    'message': message,
                    'date': date.strftime('%Y-%m-%d %H:%M:%S'),
                    'changes': 0
                }
            elif line.strip():  # Changes line
                changes = sum(int(s.split()[0]) for s in line.split(',') if s.strip())
                if current_commit:
                    current_commit['changes'] = changes
                    history['largest_commits'].append(current_commit.copy())

        # Sort and limit largest commits
        history['largest_commits'].sort(key=lambda x: x['changes'], reverse=True)
        history['largest_commits'] = history['largest_commits'][:10]

        return history

    def _analyze_code_churn(self) -> Dict:
        """Analyze code churn metrics."""
        churn = {
            'total_additions': 0,
            'total_deletions': 0,
            'by_author': defaultdict(lambda: {'additions': 0, 'deletions': 0}),
            'by_file': defaultdict(lambda: {'additions': 0, 'deletions': 0}),
            'churn_rate': defaultdict(float)
        }
        
        log = self._run_git_command([
            'log', '--numstat', '--format=commit %an'
        ])
        
        current_author = ''
        for line in log.split('\n'):
            if line.startswith('commit '):
                current_author = line.replace('commit ', '')
            elif line.strip():
                try:
                    adds, dels, file = line.split('\t')
                    if adds.isdigit() and dels.isdigit():
                        adds, dels = int(adds), int(dels)
                        
                        churn['total_additions'] += adds
                        churn['total_deletions'] += dels
                        
                        churn['by_author'][current_author]['additions'] += adds
                        churn['by_author'][current_author]['deletions'] += dels
                        
                        churn['by_file'][file]['additions'] += adds
                        churn['by_file'][file]['deletions'] += dels
                        
                        # Calculate churn rate (changes per commit)
                        total_changes = adds + dels
                        if total_changes > 0:
                            churn['churn_rate'][file] = total_changes
                except:
                    continue

        return churn

    def _analyze_contributors(self) -> Dict:
        """Analyze contributor statistics."""
        stats = {
            'total_contributors': 0,
            'contributions_by_author': defaultdict(int),
            'active_days_by_author': defaultdict(set),
            'expertise_by_file': defaultdict(lambda: defaultdict(int))
        }

        log = self._run_git_command([
            'log', '--pretty=format:%an|%at', '--numstat'
        ])

        current_author = None
        current_date = None

        for line in log.split('\n'):
            if '|' in line:
                author, timestamp = line.split('|')
                current_author = author
                current_date = datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d')
                stats['contributions_by_author'][author] += 1
                stats['active_days_by_author'][author].add(current_date)
            elif line.strip() and current_author:
                try:
                    adds, dels, file = line.split('\t')
                    if adds.isdigit() and dels.isdigit():
                        stats['expertise_by_file'][file][current_author] += int(adds) + int(dels)
                except:
                    continue

        stats['total_contributors'] = len(stats['contributions_by_author'])

        return stats

    def _analyze_branches(self) -> Dict:
        """Analyze branch statistics."""
        branches = {
            'total_branches': 0,
            'active_branches': [],
            'stale_branches': [],
            'recently_merged': []
        }

        # Get all branches
        branch_list = self._run_git_command(['branch', '-r', '--format=%(refname:short)|%(committerdate:unix)'])
        
        current_time = datetime.now().timestamp()
        for branch in branch_list.split('\n'):
            if branch.strip():
                name, last_commit = branch.split('|')
                last_commit_date = datetime.fromtimestamp(int(last_commit))
                days_since_commit = (current_time - int(last_commit)) / 86400
                
                branches['total_branches'] += 1
                
                if days_since_commit <= 30:  # Active in last 30 days
                    branches['active_branches'].append({
                        'name': name,
                        'last_commit': last_commit_date.strftime('%Y-%m-%d')
                    })
                else:
                    branches['stale_branches'].append({
                        'name': name,
                        'days_stale': int(days_since_commit)
                    })

        return branches

    def _identify_hotspots(self) -> Dict:
        """Identify code hotspots based on frequency of changes and complexity."""
        hotspots = {
            'files': [],
            'directories': defaultdict(int)
        }

        # Get files with most changes
        changes = self._run_git_command([
            'log', '--pretty=format:', '--name-only', '--diff-filter=AM'
        ])

        file_changes = defaultdict(int)
        for file in changes.split('\n'):
            if file.strip():
                file_changes[file] += 1
                directory = os.path.dirname(file)
                hotspots['directories'][directory] += 1

        # Convert to list and sort
        hotspots['files'] = [
            {'file': file, 'changes': count}
            for file, count in file_changes.items()
        ]
        hotspots['files'].sort(key=lambda x: x['changes'], reverse=True)
        hotspots['files'] = hotspots['files'][:20]  # Top 20 hotspots

        return hotspots

    def _get_empty_analysis(self) -> Dict:
        """Return empty analysis structure when analysis fails."""
        return {
            'commit_history': {
                'total_commits': 0,
                'commit_frequency': {},
                'commit_times': {},
                'recent_activity': [],
                'largest_commits': []
            },
            'code_churn': {
                'total_additions': 0,
                'total_deletions': 0,
                'by_author': {},
                'by_file': {}
            },
            'contributor_stats': {
                'total_contributors': 0,
                'contributions_by_author': {},
                'active_days_by_author': {}
            },
            'branch_stats': {
                'total_branches': 0,
                'active_branches': [],
                'stale_branches': []
            },
            'hotspots': {
                'files': [],
                'directories': {}
            }
        } 

    def generate_report(self) -> str:
        """Generate a Markdown report about git repository."""
        data = self.analyze()
        
        report = [
            "# Git Repository Analysis Report\n",
            
            "## 📊 Commit History\n",
            f"- Total Commits: {data['commit_history']['total_commits']}",
            
            "\n### 📈 Largest Commits",
            "| Hash | Author | Date | Message | Changes |",
            "|------|--------|------|---------|----------|"
        ]
        
        # Add largest commits
        for commit in data['commit_history']['largest_commits'][:5]:
            report.append(
                f"| {commit['hash']} | {commit['author']} | {commit['date']} | "
                f"{commit['message'][:50]}... | {commit['changes']} |"
            )
        
        # Add code churn section
        report.extend([
            "\n## 📝 Code Churn",
            f"- Total Additions: {data['code_churn']['total_additions']}",
            f"- Total Deletions: {data['code_churn']['total_deletions']}",
            
            "\n### 👥 Changes by Author",
            "| Author | Additions | Deletions |",
            "|--------|-----------|-----------|"
        ])
        
        for author, stats in data['code_churn']['by_author'].items():
            report.append(
                f"| {author} | {stats['additions']} | {stats['deletions']} |"
            )
        
        # Add contributor stats
        report.extend([
            f"\n## 👥 Contributors ({data['contributor_stats']['total_contributors']})",
            "\n### Most Active Contributors",
            "| Author | Commits | Active Days |",
            "|--------|---------|-------------|"
        ])
        
        # Sort contributors by number of commits
        sorted_contributors = sorted(
            data['contributor_stats']['contributions_by_author'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for author, commits in sorted_contributors[:10]:
            active_days = len(data['contributor_stats']['active_days_by_author'][author])
            report.append(f"| {author} | {commits} | {active_days} |")
        
        # Add branch stats
        report.extend([
            f"\n## 🌿 Branches ({data['branch_stats']['total_branches']})",
            f"- Active Branches: {len(data['branch_stats']['active_branches'])}",
            f"- Stale Branches: {len(data['branch_stats']['stale_branches'])}",
            
            "\n### Stale Branches",
            "| Branch | Days Stale |",
            "|--------|------------|"
        ])
        
        for branch in sorted(data['branch_stats']['stale_branches'], 
                            key=lambda x: x['days_stale'], 
                            reverse=True)[:5]:
            report.append(f"| {branch['name']} | {branch['days_stale']} |")
        
        # Add hotspots section
        report.extend([
            "\n## 🔥 Code Hotspots",
            "\n### Most Changed Files",
            "| File | Changes |",
            "|------|----------|"
        ])
        
        for hotspot in data['hotspots']['files'][:10]:
            report.append(f"| {hotspot['file']} | {hotspot['changes']} |")
        
        return '\n'.join(report) 