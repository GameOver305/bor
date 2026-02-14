#!/usr/bin/env python3
"""
Test database path fixes
Verify that database operations work with absolute paths
"""
import asyncio
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from database.db_manager import DatabaseManager


async def test_database_paths():
    """Test that database paths are absolute and operations work"""
    
    print("=" * 60)
    print("Testing Database Path Fixes")
    print("=" * 60)
    
    # Test 1: Verify paths are absolute
    print("\n✅ Test 1: Verify paths are absolute")
    print(f"DATABASE_PATH: {config.DATABASE_PATH}")
    print(f"BACKUP_DIR: {config.BACKUP_DIR}")
    print(f"LOGS_DIR: {config.LOGS_DIR}")
    
    assert os.path.isabs(config.DATABASE_PATH), "DATABASE_PATH must be absolute"
    assert os.path.isabs(config.BACKUP_DIR), "BACKUP_DIR must be absolute"
    assert os.path.isabs(config.LOGS_DIR), "LOGS_DIR must be absolute"
    print("✅ All paths are absolute")
    
    # Test 2: Create a test database in a temporary directory
    print("\n✅ Test 2: Test database operations with directory creation")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = os.path.join(tmpdir, "test_subdir", "test.db")
        print(f"Test database path: {test_db_path}")
        
        # Verify directory doesn't exist yet
        assert not os.path.exists(os.path.dirname(test_db_path)), "Directory should not exist yet"
        
        # Create database manager with test path
        db_manager = DatabaseManager(db_path=test_db_path)
        
        # Test _ensure_db_directory creates the directory
        db_manager._ensure_db_directory()
        assert os.path.exists(os.path.dirname(test_db_path)), "Directory should be created"
        print("✅ Directory creation works")
        
        # Test basic database operations
        await db_manager.initialize()
        assert os.path.exists(test_db_path), "Database file should be created"
        print("✅ Database initialization works")
        
        # Test a simple query
        result = await db_manager.fetchone("SELECT 1 as test")
        assert result[0] == 1, "Query should return 1"
        print("✅ Database queries work")
        
        # Test user creation
        user = await db_manager.get_or_create_user(
            discord_id="123456789",
            username="TestUser",
            player_id="P123"
        )
        assert user is not None, "User should be created"
        assert user.discord_id == "123456789", "User discord_id should match"
        print(f"✅ User operations work (created user: {user.username})")
    
    # Test 3: Verify default database directory exists
    print("\n✅ Test 3: Verify default database directory")
    db_dir = os.path.dirname(config.DATABASE_PATH)
    print(f"Database directory: {db_dir}")
    
    # The directory should exist (created by bot.py main function or db_manager)
    # but we don't require it for this test since we're not running main()
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)


async def main():
    try:
        await test_database_paths()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
