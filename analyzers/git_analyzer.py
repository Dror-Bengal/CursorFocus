import os
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict
from collections import defaultdict

class GitAnalyzer:
    def __init__(self, project_path: str):
        self.project_path = project_path
        
    def _is_git_repo(self) -> bool:
        """Check if it's a Git repository."""
        return os.path.exists(os.path.join(self.project_path, '.git'))
        
    def analyze(self) -> Dict:
        """Analyze Git repository."""
        if not self._is_git_repo():
            return {'error': 'Not a Git repository'}
            
        return {
            'commit_frequency': self._analyze_commit_frequency(),
            'code_churn': self._analyze_code_churn(),
            'authors': self._analyze_authors(),
            'branches': self._analyze_branches()
        }

    def _run_git_command(self, command: List[str]) -> str:
        """Run Git command and return output."""
        try:
            result = subprocess.run(
                ['git'] + command,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                check=False
            )
            return result.stdout.strip() if result.returncode == 0 else ''
        except Exception as e:
            print(f"⚠️ Warning: Git command failed: {str(e)}")
            return ''

    def _analyze_commit_frequency(self) -> Dict:
        """Analyze commit frequency."""
        frequency = {
            'daily': defaultdict(int),
            'weekly': defaultdict(int),
            'monthly': defaultdict(int),
            'total': 0
        }
        
        log = self._run_git_command([
            'log', '--format=%ai'  # ISO 8601 format
        ])
        
        for line in log.split('\n'):
            if not line: continue
            date = datetime.strptime(line.split()[0], '%Y-%m-%d')
            
            # Daily
            day_key = date.strftime('%Y-%m-%d')
            frequency['daily'][day_key] += 1
            
            # Weekly
            week_key = f"{date.year}-W{date.strftime('%V')}"
            frequency['weekly'][week_key] += 1
            
            # Monthly
            month_key = date.strftime('%Y-%m')
            frequency['monthly'][month_key] += 1
            
            frequency['total'] += 1
            
        # Convert defaultdict to dict for JSON serialization
        return {
            'daily': dict(frequency['daily']),
            'weekly': dict(frequency['weekly']),
            'monthly': dict(frequency['monthly']),
            'total': frequency['total']
        }

    def _analyze_code_churn(self) -> Dict:
        """Analyze code churn."""
        churn = {
            'total_additions': 0,
            'total_deletions': 0,
            'by_author': defaultdict(lambda: {'additions': 0, 'deletions': 0}),
            'by_file': defaultdict(lambda: {'additions': 0, 'deletions': 0})
        }
        
        log = self._run_git_command([
            'log', '--numstat', '--format=commit %an'  # Numstat format with author
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
                except:
                    continue
                    
        return {
            'total_additions': churn['total_additions'],
            'total_deletions': churn['total_deletions'],
            'by_author': dict(churn['by_author']),
            'by_file': dict(churn['by_file'])
        }

    def _analyze_authors(self) -> Dict:
        """Analyze author information."""
        authors = defaultdict(lambda: {
            'commits': 0,
            'first_commit': None,
            'last_commit': None,
            'files_changed': 0,
            'lines_changed': 0
        })
        
        # Get commit info
        log = self._run_git_command([
            'log', '--format=%an|%at|%H'  # author, timestamp, hash
        ])
        
        for line in log.split('\n'):
            if not line: continue
            author, timestamp, commit_hash = line.split('|')
            commit_time = datetime.fromtimestamp(int(timestamp))
            
            authors[author]['commits'] += 1
            
            if not authors[author]['first_commit'] or commit_time < authors[author]['first_commit']:
                authors[author]['first_commit'] = commit_time
            if not authors[author]['last_commit'] or commit_time > authors[author]['last_commit']:
                authors[author]['last_commit'] = commit_time
                
            # Get changed files for this commit
            stat = self._run_git_command(['show', '--stat', commit_hash])
            files_changed = len([l for l in stat.split('\n') if l.strip() and '|' in l])
            lines = sum(int(n) for n in stat.split('\n')[-1].split(',')[:-1] if n.strip().isdigit())
            
            authors[author]['files_changed'] = max(authors[author]['files_changed'], files_changed)
            authors[author]['lines_changed'] += lines
            
        return dict(authors)

    def _analyze_branches(self) -> List[Dict]:
        """Analyze branch information."""
        branches = []
        
        for branch in self._run_git_command(['branch']).split('\n'):
            if not branch: continue
            is_active = branch.startswith('*')
            name = branch.replace('*', '').strip()
            
            # Get last commit info
            last_commit = self._run_git_command([
                'log', '-1', '--format=%at|%an', name
            ])
            
            if last_commit:
                timestamp, author = last_commit.split('|')
                commit_time = datetime.fromtimestamp(int(timestamp))
                
                # Count commits and authors
                commits = int(self._run_git_command(['rev-list', '--count', name]))
                authors = len(set(self._run_git_command([
                    'log', '--format=%an', name
                ]).split('\n')))
                
                # Count changed files
                files = len(set(self._run_git_command([
                    'log', '--name-only', '--format=', name
                ]).split('\n')))
                
                branches.append({
                    'name': name,
                    'is_active': is_active,
                    'last_commit_date': commit_time,
                    'commits': commits,
                    'authors': authors,
                    'files_changed': files
                })
                
        return branches

    def generate_report(self) -> str:
        """Generate a Markdown report for Git analysis."""
        data = self.analyze()
        
        if 'error' in data:
            return f"# Git Repository Analysis\n\n❌ {data['error']}"
            
        report = [
            "# Git Repository Analysis\n",
            "## 📊 Commit Activity\n",
            "### Recent Activity",
            f"- Total Commits: **{data['commit_frequency']['total']}**",
            "\n### Daily Commits",
            "| Date | Commits |",
            "|------|---------|",
        ]
        
        # Add daily commits (last 7 days)
        sorted_days = sorted(data['commit_frequency']['daily'].items(), reverse=True)[:7]
        for day, count in sorted_days:
            report.append(f"| {day} | {count} |")
        
        # Code Churn Section
        report.extend([
            "\n## 📈 Code Churn",
            f"- Total Lines Added: **{data['code_churn']['total_additions']}**",
            f"- Total Lines Deleted: **{data['code_churn']['total_deletions']}**",
            "\n### Changes by Author",
            "| Author | Additions | Deletions | Total |",
            "|--------|-----------|-----------|-------|"
        ])
        
        # Add author statistics
        for author, stats in data['code_churn']['by_author'].items():
            total = stats['additions'] + stats['deletions']
            report.append(
                f"| {author} | +{stats['additions']} | -{stats['deletions']} | {total} |"
            )
        
        # Most Changed Files
        report.extend([
            "\n### Most Changed Files",
            "| File | Additions | Deletions | Total Changes |",
            "|------|-----------|-----------|---------------|"
        ])
        
        # Sort files by total changes and show top 10
        sorted_files = sorted(
            data['code_churn']['by_file'].items(),
            key=lambda x: x[1]['additions'] + x[1]['deletions'],
            reverse=True
        )[:10]
        
        for file, stats in sorted_files:
            total = stats['additions'] + stats['deletions']
            report.append(
                f"| {file} | +{stats['additions']} | -{stats['deletions']} | {total} |"
            )
        
        # Contributors Section
        report.extend([
            "\n## 👥 Contributors",
            "| Author | Commits | Files Changed | Lines Changed | First Commit | Last Commit |",
            "|--------|---------|---------------|---------------|--------------|-------------|"
        ])
        
        for author, stats in data['authors'].items():
            first = stats['first_commit'].strftime('%Y-%m-%d') if stats['first_commit'] else '-'
            last = stats['last_commit'].strftime('%Y-%m-%d') if stats['last_commit'] else '-'
            report.append(
                f"| {author} | {stats['commits']} | {stats['files_changed']} | "
                f"{stats['lines_changed']} | {first} | {last} |"
            )
        
        # Branches Section
        report.extend([
            "\n## 🌳 Branches",
            "| Branch | Status | Commits | Contributors | Files Changed | Last Commit |",
            "|--------|--------|---------|--------------|---------------|-------------|"
        ])
        
        for branch in data['branches']:
            status = "🟢 Active" if branch['is_active'] else "⚪️ Inactive"
            last_commit = branch['last_commit_date'].strftime('%Y-%m-%d')
            report.append(
                f"| {branch['name']} | {status} | {branch['commits']} | "
                f"{branch['authors']} | {branch['files_changed']} | {last_commit} |"
            )
        
        return '\n'.join(report) 