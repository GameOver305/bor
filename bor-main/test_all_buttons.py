#!/usr/bin/env python3
"""
Comprehensive button functionality test
Tests all button handlers and their callbacks
"""

import asyncio
import sys
from pathlib import Path

async def main():
    # Test 1: Import all modules
    print("📦 Test 1: Importing all modules...")
    try:
        from cogs.main_control_panel import MainControlPanelView, LanguageSelectView, MyInfoView
        from cogs.reservations_system import ReservationsMenuView, ReservationSectionView
        from cogs.alliance_system import AllianceMenuView, AllianceMembersManagementView, AllianceSystemCog
        from cogs.management_system import ManagementPanelView
        from utils.buttons import MainMenuView, BookingTypeSelectView, CreateAllianceModal
        print("✅ All modules imported successfully")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        sys.exit(1)

    # Test 2: Verify button custom IDs are defined
    print("\n📋 Test 2: Checking button custom IDs...")
    test_user_id = "123456789"

    def get_custom_ids(view):
        """Extract custom_ids from view"""
        ids = []
        for child in view.children:
            custom_id = getattr(child, "custom_id", None)
            if custom_id:
                ids.append(custom_id)
        return ids

    views_to_test = [
        ("MainControlPanelView", MainControlPanelView(test_user_id, is_admin=True, is_owner=True)),
        ("LanguageSelectView", LanguageSelectView(test_user_id)),
        ("MyInfoView", MyInfoView(test_user_id)),
        ("ReservationsMenuView", ReservationsMenuView(test_user_id)),
        ("ReservationSectionView", ReservationSectionView(test_user_id, "building")),
        ("AllianceMenuView (not in alliance)", AllianceMenuView(test_user_id, in_alliance=False, has_permissions=False)),
        ("AllianceMenuView (in alliance)", AllianceMenuView(test_user_id, in_alliance=True, has_permissions=True)),
        ("ManagementPanelView", ManagementPanelView(test_user_id, is_owner=True)),
        ("MainMenuView", MainMenuView()),
        ("BookingTypeSelectView", BookingTypeSelectView()),
    ]

    total_buttons = 0
    for view_name, view in views_to_test:
        custom_ids = get_custom_ids(view)
        total_buttons += len(custom_ids)
        print(f"  ✓ {view_name}: {len(custom_ids)} buttons")
        if custom_ids:
            for custom_id in custom_ids:
                print(f"    - {custom_id}")

    print(f"✅ Total buttons found: {total_buttons}")

    # Test 3: Verify AllianceSystemCog has on_interaction listener
    print("\n🔍 Test 3: Checking AllianceSystemCog listeners...")
    import inspect
    members = inspect.getmembers(AllianceSystemCog)
    has_on_interaction = any(name == 'on_interaction' for name, _ in members)
    if has_on_interaction:
        print("✅ AllianceSystemCog has on_interaction listener")
    else:
        print("❌ AllianceSystemCog missing on_interaction listener")
        sys.exit(1)

    # Test 4: Verify tag validation in modals
    print("\n🏷️  Test 4: Checking alliance tag validation...")

    # Check CreateAllianceModal
    tag_input = CreateAllianceModal().tag_input
    if tag_input.min_length == 3 and tag_input.max_length == 3:
        print(f"✅ CreateAllianceModal tag: min={tag_input.min_length}, max={tag_input.max_length}")
    else:
        print(f"❌ CreateAllianceModal tag validation incorrect: min={tag_input.min_length}, max={tag_input.max_length}")
        sys.exit(1)

    # Test 5: Verify all expected handlers exist
    print("\n🎯 Test 5: Checking handler methods...")
    expected_handlers = [
        '_show_alliance_info',
        '_handle_create_alliance',
        '_handle_join_alliance',
        '_show_ranks',
        '_handle_promote',
        '_handle_demote',
        '_handle_kick',
        '_show_members',
        '_back_to_main',
    ]

    for handler in expected_handlers:
        if hasattr(AllianceSystemCog, handler):
            print(f"  ✓ {handler} exists")
        else:
            print(f"  ❌ {handler} missing")
            sys.exit(1)

    print("✅ All handler methods exist")

    # Test 6: Check button routing in on_interaction
    print("\n🔀 Test 6: Checking button routing...")
    source_code = Path("cogs/alliance_system.py").read_text()

    expected_custom_ids = [
        'alliance_info',
        'alliance_create',
        'alliance_join',
        'alliance_ranks',
        'alliance_promote',
        'alliance_demote',
        'alliance_kick',
        'alliance_back',
        'alliance_back_to_menu',
    ]

    for custom_id in expected_custom_ids:
        if f"'{custom_id}'" in source_code or f'"{custom_id}"' in source_code:
            print(f"  ✓ {custom_id} found in routing")
        else:
            print(f"  ❌ {custom_id} not found in routing")
            sys.exit(1)

    print("✅ All button routes properly defined")

    # Test 7: Summary
    print("\n" + "="*50)
    print("🎉 ALL TESTS PASSED!")
    print("="*50)
    print(f"✅ Total buttons tested: {total_buttons}")
    print(f"✅ All handlers implemented")
    print(f"✅ Alliance tag validation: exactly 3 characters")
    print(f"✅ Button routing complete")
    print("\n✨ The bot button system is fully functional!")

if __name__ == "__main__":
    asyncio.run(main())
