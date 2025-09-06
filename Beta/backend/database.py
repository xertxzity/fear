#!/usr/bin/env python3
"""
Database layer for Fortnite Season 7 Emulator
Provides persistent storage for game data using SQLite
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

class GameDatabase:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent / 'data' / 'game.db'
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Player profiles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS player_profiles (
                    account_id TEXT PRIMARY KEY,
                    profile_data TEXT NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Creative islands table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS creative_islands (
                    island_code TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    island_name TEXT NOT NULL,
                    description TEXT,
                    island_data TEXT NOT NULL,
                    published BOOLEAN DEFAULT FALSE,
                    plays INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    published_at TIMESTAMP
                )
            ''')
            
            # Battle pass progress table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS battle_pass_progress (
                    account_id TEXT PRIMARY KEY,
                    season INTEGER NOT NULL,
                    current_tier INTEGER DEFAULT 1,
                    battle_stars INTEGER DEFAULT 0,
                    premium_purchased BOOLEAN DEFAULT FALSE,
                    progress_data TEXT NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Challenges table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS challenges (
                    challenge_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    challenge_type TEXT NOT NULL,
                    progress INTEGER DEFAULT 0,
                    target INTEGER NOT NULL,
                    completed BOOLEAN DEFAULT FALSE,
                    completed_at TIMESTAMP,
                    reward TEXT
                )
            ''')
            
            # Player economy table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS player_economy (
                    account_id TEXT PRIMARY KEY,
                    vbucks INTEGER DEFAULT 1000,
                    purchase_history TEXT,
                    gift_history TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Parties table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS parties (
                    party_id TEXT PRIMARY KEY,
                    leader_id TEXT NOT NULL,
                    members TEXT NOT NULL,
                    party_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with automatic cleanup"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    # Creative Islands methods
    def create_island(self, island_code: str, owner_id: str, island_name: str, 
                     description: str = '', island_data: Dict[str, Any] = None) -> bool:
        """Create a new creative island"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO creative_islands 
                    (island_code, owner_id, island_name, description, island_data)
                    VALUES (?, ?, ?, ?, ?)
                ''', (island_code, owner_id, island_name, description, 
                     json.dumps(island_data or {})))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    def get_island(self, island_code: str) -> Optional[Dict[str, Any]]:
        """Get island by code"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM creative_islands WHERE island_code = ?', (island_code,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'island_code': row['island_code'],
                    'owner_id': row['owner_id'],
                    'island_name': row['island_name'],
                    'description': row['description'],
                    'island_data': json.loads(row['island_data']),
                    'published': bool(row['published']),
                    'plays': row['plays'],
                    'likes': row['likes'],
                    'created_at': row['created_at'],
                    'published_at': row['published_at']
                }
            return None
    
    def publish_island(self, island_code: str) -> bool:
        """Publish an island"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE creative_islands 
                SET published = TRUE, published_at = CURRENT_TIMESTAMP
                WHERE island_code = ?
            ''', (island_code,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_published_islands(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get published islands"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM creative_islands 
                WHERE published = TRUE 
                ORDER BY published_at DESC 
                LIMIT ?
            ''', (limit,))
            
            islands = []
            for row in cursor.fetchall():
                islands.append({
                    'island_code': row['island_code'],
                    'owner_id': row['owner_id'],
                    'island_name': row['island_name'],
                    'description': row['description'],
                    'plays': row['plays'],
                    'likes': row['likes'],
                    'published_at': row['published_at']
                })
            return islands
    
    # Battle Pass methods
    def get_battle_pass_progress(self, account_id: str, season: int = 7) -> Dict[str, Any]:
        """Get battle pass progress for player"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM battle_pass_progress 
                WHERE account_id = ? AND season = ?
            ''', (account_id, season))
            row = cursor.fetchone()
            
            if row:
                return {
                    'account_id': row['account_id'],
                    'season': row['season'],
                    'current_tier': row['current_tier'],
                    'battle_stars': row['battle_stars'],
                    'premium_purchased': bool(row['premium_purchased']),
                    'progress_data': json.loads(row['progress_data']),
                    'last_updated': row['last_updated']
                }
            else:
                # Create default progress
                default_progress = {
                    'unlocked_tiers': [1],
                    'completed_challenges': []
                }
                cursor.execute('''
                    INSERT INTO battle_pass_progress 
                    (account_id, season, progress_data)
                    VALUES (?, ?, ?)
                ''', (account_id, season, json.dumps(default_progress)))
                conn.commit()
                
                return {
                    'account_id': account_id,
                    'season': season,
                    'current_tier': 1,
                    'battle_stars': 0,
                    'premium_purchased': False,
                    'progress_data': default_progress,
                    'last_updated': datetime.utcnow().isoformat()
                }
    
    def update_battle_pass_progress(self, account_id: str, season: int, 
                                   current_tier: int = None, battle_stars: int = None,
                                   progress_data: Dict[str, Any] = None) -> bool:
        """Update battle pass progress"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if current_tier is not None:
                updates.append('current_tier = ?')
                params.append(current_tier)
            
            if battle_stars is not None:
                updates.append('battle_stars = ?')
                params.append(battle_stars)
            
            if progress_data is not None:
                updates.append('progress_data = ?')
                params.append(json.dumps(progress_data))
            
            if updates:
                updates.append('last_updated = CURRENT_TIMESTAMP')
                params.extend([account_id, season])
                
                cursor.execute(f'''
                    UPDATE battle_pass_progress 
                    SET {', '.join(updates)}
                    WHERE account_id = ? AND season = ?
                ''', params)
                conn.commit()
                return cursor.rowcount > 0
            
            return False
    
    # Economy methods
    def get_player_economy(self, account_id: str) -> Dict[str, Any]:
        """Get player economy data"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM player_economy WHERE account_id = ?', (account_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'account_id': row['account_id'],
                    'vbucks': row['vbucks'],
                    'purchase_history': json.loads(row['purchase_history'] or '[]'),
                    'gift_history': json.loads(row['gift_history'] or '[]'),
                    'last_updated': row['last_updated']
                }
            else:
                # Create default economy
                cursor.execute('''
                    INSERT INTO player_economy (account_id, purchase_history, gift_history)
                    VALUES (?, ?, ?)
                ''', (account_id, '[]', '[]'))
                conn.commit()
                
                return {
                    'account_id': account_id,
                    'vbucks': 1000,
                    'purchase_history': [],
                    'gift_history': [],
                    'last_updated': datetime.utcnow().isoformat()
                }
    
    def update_vbucks(self, account_id: str, amount: int) -> bool:
        """Update player V-Bucks balance"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE player_economy 
                SET vbucks = vbucks + ?, last_updated = CURRENT_TIMESTAMP
                WHERE account_id = ?
            ''', (amount, account_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def add_purchase(self, account_id: str, purchase_data: Dict[str, Any]) -> bool:
        """Add purchase to history"""
        economy = self.get_player_economy(account_id)
        economy['purchase_history'].append(purchase_data)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE player_economy 
                SET purchase_history = ?, last_updated = CURRENT_TIMESTAMP
                WHERE account_id = ?
            ''', (json.dumps(economy['purchase_history']), account_id))
            conn.commit()
            return cursor.rowcount > 0
    
    # Party methods
    def save_party(self, party_id: str, party_data: Dict[str, Any]) -> bool:
        """Save party data"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get leader ID from party data
                leader_id = None
                members = party_data.get('members', [])
                for member in members:
                    if member.get('role') == 'CAPTAIN':
                        leader_id = member.get('account_id')
                        break
                
                if not leader_id and members:
                    leader_id = members[0].get('account_id')
                
                # Create members list for storage
                member_ids = [member.get('account_id') for member in members]
                
                cursor.execute('''
                    INSERT OR REPLACE INTO parties 
                    (party_id, leader_id, members, party_data)
                    VALUES (?, ?, ?, ?)
                ''', (party_id, leader_id, json.dumps(member_ids), json.dumps(party_data)))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving party {party_id}: {e}")
            return False
    
    def get_party(self, party_id: str) -> Optional[Dict[str, Any]]:
        """Get party data"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT party_data FROM parties WHERE party_id = ?', (party_id,))
                row = cursor.fetchone()
                
                if row:
                    return json.loads(row['party_data'])
                return None
        except Exception as e:
            print(f"Error getting party {party_id}: {e}")
            return None
    
    def delete_party(self, party_id: str) -> bool:
        """Delete party"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM parties WHERE party_id = ?', (party_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting party {party_id}: {e}")
            return False
    
    def get_user_party(self, account_id: str) -> Optional[str]:
        """Get party ID that user is in"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT party_id FROM parties 
                    WHERE members LIKE ?
                ''', (f'%"{account_id}"%',))
                row = cursor.fetchone()
                
                if row:
                    return row['party_id']
                return None
        except Exception as e:
            print(f"Error getting user party for {account_id}: {e}")
            return None

# Global database instance
_db_instance = None

def get_database() -> GameDatabase:
    """Get the global database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = GameDatabase()
    return _db_instance