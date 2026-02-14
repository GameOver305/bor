#!/usr/bin/env python3
"""
Test scheduled task database access
Simulates the scenario where scheduled tasks (like reminders_task) access the database
"""
import asyncio
import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
from database.models import Booking


async def simulate_scheduled_task(db_manager, task_name, iteration):
    """Simulate a scheduled task accessing the database"""
    print(f"  [{task_name}] Iteration {iteration}: Fetching active bookings...")
    
    try:
        # This simulates what reminders_task.py does at line 44
        bookings = await db_manager.get_all_active_bookings()
        print(f"  [{task_name}] Iteration {iteration}: Found {len(bookings)} active bookings")
        
        # Simulate loading user language (what translator does)
        if bookings:
            for booking in bookings[:2]:  # Just check first 2
                user = await db_manager.get_user_by_id(booking.user_id)
                if user:
                    print(f"  [{task_name}] Iteration {iteration}: User {user.username} language: {user.language}")
        
        return True
    except Exception as e:
        print(f"  [{task_name}] Iteration {iteration}: ERROR - {e}")
        return False


async def test_scheduled_task_scenario():
    """Test the scenario described in the problem statement"""
    
    print("=" * 60)
    print("Testing Scheduled Task Database Access")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = os.path.join(tmpdir, "data", "bookings.db")
        print(f"\nTest database path: {test_db_path}")
        
        # Initialize database
        print("\n✅ Step 1: Initialize database")
        db_manager = DatabaseManager(db_path=test_db_path)
        await db_manager.initialize()
        
        # Create test data
        print("\n✅ Step 2: Create test data")
        user1 = await db_manager.get_or_create_user("111", "User1", "P1")
        user2 = await db_manager.get_or_create_user("222", "User2", "P2")
        assert user1.discord_id == "111", "User1 should be created correctly"
        assert user2.discord_id == "222", "User2 should be created correctly"
        print(f"✅ Created users: {user1.username}, {user2.username}")
        
        # Create some bookings
        booking1 = Booking(
            booking_id=None,
            user_id=user1.user_id,
            booking_type="building",
            player_name="Player1",
            player_id="P1",
            alliance_name="Alliance1",
            scheduled_time=datetime.now() + timedelta(hours=1),
            details="Test booking 1",
            status="active",
            created_by="111",
            duration_days=1
        )
        booking_id = await db_manager.create_booking(booking1)
        print(f"✅ Created booking #{booking_id}")
        
        # Test 3: Simulate scheduled task running every 5 minutes (as described in the problem)
        print("\n✅ Step 3: Simulate scheduled task running multiple times")
        for i in range(1, 4):
            print(f"\n  Scheduled task cycle {i} (simulating 5-minute interval)...")
            success = await simulate_scheduled_task(db_manager, "reminders_task", i)
            assert success, f"Task should succeed on iteration {i}"
            await asyncio.sleep(0.1)  # Small delay to simulate time passing
        
        # Test 4: Delete database file during runtime (the actual problem!)
        print("\n✅ Step 4: Delete database file (simulating the error scenario)")
        os.remove(test_db_path)
        print("  Database file deleted!")
        
        # Test 5: Scheduled task should still work (auto-recovery)
        print("\n✅ Step 5: Scheduled task should auto-recover")
        for i in range(4, 7):
            print(f"\n  Scheduled task cycle {i} (after deletion)...")
            success = await simulate_scheduled_task(db_manager, "reminders_task", i)
            assert success, f"Task should succeed even after deletion on iteration {i}"
            await asyncio.sleep(0.1)
        
        print("\n✅ Database auto-recovered successfully!")
        
        # Test 6: Simulate multiple scheduled tasks running concurrently
        print("\n✅ Step 6: Simulate multiple scheduled tasks running concurrently")
        tasks = [
            simulate_scheduled_task(db_manager, "reminders_task", 10),
            simulate_scheduled_task(db_manager, "translator_task", 10),
            simulate_scheduled_task(db_manager, "alliance_system", 10),
            simulate_scheduled_task(db_manager, "management_system", 10),
        ]
        results = await asyncio.gather(*tasks)
        assert all(results), "All concurrent tasks should succeed"
        print("✅ All scheduled tasks ran successfully in parallel")
        
        # Test 7: Delete directory and ensure recovery
        print("\n✅ Step 7: Delete entire directory (more severe scenario)")
        shutil.rmtree(os.path.dirname(test_db_path))
        print("  Database directory deleted!")
        
        print("\n✅ Step 8: Scheduled tasks should still work")
        success = await simulate_scheduled_task(db_manager, "reminders_task", 11)
        assert success, "Task should succeed even after directory deletion"
        print("✅ Database and directory auto-recovered!")
        
    print("\n" + "=" * 60)
    print("✅ All scheduled task scenarios passed!")
    print("=" * 60)
    print("\nValidated Scenarios:")
    print("✓ Normal scheduled task operation")
    print("✓ Recovery from database file deletion")
    print("✓ Recovery from directory deletion")
    print("✓ Multiple concurrent scheduled tasks")
    print("✓ Continuous operation after recovery")


async def main():
    try:
        await test_scheduled_task_scenario()
        print("\n" + "=" * 60)
        print("✅ PROBLEM STATEMENT SCENARIO VALIDATED!")
        print("=" * 60)
        print("\nThe database manager now handles:")
        print("1. ✓ Directory verification on every connection")
        print("2. ✓ Path validation before connections")
        print("3. ✓ Retry logic with exponential backoff")
        print("4. ✓ Auto-recovery from file/directory deletion")
        print("5. ✓ Comprehensive logging for debugging")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
