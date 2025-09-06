from pathlib import Path
import shutil
import datetime
import os

class HostsManager:
    """Simple hosts file manager to add/remove mappings for emulator use.

    - Backs up the hosts file before modifying
    - Adds idempotent entries mapping domains to 127.0.0.1
    - Restores from backup on request
    """

    def __init__(self, backup_dir: Path = None):
        self.hosts_path = self._get_hosts_path()
        self.backup_dir = backup_dir or (Path(__file__).parent.parent / 'backups')
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _get_hosts_path(self) -> Path:
        if os.name == 'nt':
            return Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32' / 'drivers' / 'etc' / 'hosts'
        else:
            return Path('/etc/hosts')

    def backup_hosts(self) -> Path:
        """Create a timestamped backup of the hosts file and return the backup path"""
        if not self.hosts_path.exists():
            return None
        ts = datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f'hosts_backup_{ts}.bak'
        shutil.copy2(self.hosts_path, backup_file)
        return backup_file

    def _read_hosts(self) -> str:
        try:
            return self.hosts_path.read_text()
        except Exception:
            return ''

    def _write_hosts(self, data: str) -> None:
        self.hosts_path.write_text(data)

    def add_mappings(self, domains, ip='127.0.0.1') -> bool:
        """Add mappings for the provided domains. Idempotent."""
        try:
            content = self._read_hosts()
            if not content:
                # Ensure the file exists
                self._write_hosts('')
                content = ''

            # Backup first
            self.backup_hosts()

            lines = content.splitlines()
            existing = set(l.strip() for l in lines if l.strip())

            added = False
            for d in domains:
                entry = f"{ip} {d}"
                if not any(d in l for l in existing):
                    lines.append(f"# Emulator entry - Fortnite redirect\n{entry}")
                    added = True

            if added:
                self._write_hosts('\n'.join(lines) + '\n')
            return True
        except Exception:
            return False

    def remove_mappings(self, domains) -> bool:
        """Remove mappings for the provided domains (best-effort)."""
        try:
            content = self._read_hosts()
            if not content:
                return True
            lines = content.splitlines()
            filtered = []
            skip_next = False
            for line in lines:
                if skip_next:
                    skip_next = False
                    continue
                if line.strip().startswith('# Emulator entry - Fortnite redirect'):
                    # Skip the comment and next line if it contains a mapping
                    skip_next = True
                    continue
                # Remove any line that maps one of our domains
                if any((' ' + d) in line or ('\t' + d) in line for d in domains):
                    continue
                filtered.append(line)

            self._write_hosts('\n'.join(filtered) + '\n')
            return True
        except Exception:
            return False
