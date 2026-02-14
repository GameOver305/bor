"""
نظام التحالف - Alliance System
Complete alliance management with member control and ranks
"""
import discord
from discord import app_commands
from discord.ext import commands
from discord import ui
import logging
from datetime import datetime

from utils.translator import translator, get_text
from utils.ui_components import create_colored_embed
from utils import permissions
from database import db

logger = logging.getLogger('alliance_system')


class AllianceMenuView(discord.ui.View):
    @discord.ui.button(label='عرض الأعضاء', style=discord.ButtonStyle.primary, custom_id='alliance_members', row=1)
    async def alliance_members_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        cog = interaction.client.get_cog('AllianceSystemCog')
        if cog:
            await cog._show_members(interaction)
    """Alliance main menu"""
    
    def __init__(self, user_id: str, in_alliance: bool = False, has_permissions: bool = False):
        super().__init__(timeout=None)  # Persistent view - no timeout
        self.user_id = user_id
        self.in_alliance = in_alliance
        self.has_permissions = has_permissions
        self._build_buttons()
    
    def _build_buttons(self):
        """Build alliance menu buttons (شامل)"""
        user_id = self.user_id
        # زر معلومات التحالف دائمًا
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'alliance.info'),
            style=discord.ButtonStyle.primary,
            custom_id='alliance_info',
            emoji='ℹ️',
            row=0
        ))
        # إذا لم يكن في تحالف: أزرار تسجيل/انضمام
        if not self.in_alliance:
            self.add_item(discord.ui.Button(
                label=get_text(user_id, 'alliance.create'),
                style=discord.ButtonStyle.success,
                custom_id='alliance_create',
                emoji='🆕',
                row=0
            ))
            self.add_item(discord.ui.Button(
                label=get_text(user_id, 'alliance.join'),
                style=discord.ButtonStyle.primary,
                custom_id='alliance_join',
                emoji='➕',
                row=0
            ))
        else:
            # إذا كان في تحالف: أزرار المعلومات والرتب
            self.add_item(discord.ui.Button(
                label=get_text(user_id, 'alliance.ranks'),
                style=discord.ButtonStyle.primary,
                custom_id='alliance_ranks',
                emoji='🏖️',
                row=1
            ))
            # أزرار إدارة الأعضاء (ترقية/تنزيل/طرد) - only if has_permissions
            if self.has_permissions:
                self.add_item(discord.ui.Button(
                    label=get_text(user_id, 'alliance.promote'),
                    style=discord.ButtonStyle.success,
                    custom_id='alliance_promote',
                    emoji='⬆️',
                    row=2
                ))
                self.add_item(discord.ui.Button(
                    label=get_text(user_id, 'alliance.demote'),
                    style=discord.ButtonStyle.secondary,
                    custom_id='alliance_demote',
                    emoji='⬇️',
                    row=2
                ))
                self.add_item(discord.ui.Button(
                    label=get_text(user_id, 'alliance.kick'),
                    style=discord.ButtonStyle.danger,
                    custom_id='alliance_kick',
                    emoji='❌',
                    row=2
                ))
        # زر العودة
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'common.back'),
            style=discord.ButtonStyle.secondary,
            custom_id='alliance_back',
            row=4
        ))
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if user owns this menu"""
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "❌ This menu is not for you!",
                ephemeral=True
            )
            return False
        return True


class AllianceMembersManagementView(discord.ui.View):
    """View for managing alliance members"""
    
    def __init__(self, user_id: str, members_data: list):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.members_data = members_data
        
        # Add back button
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'common.back'),
            style=discord.ButtonStyle.secondary,
            custom_id='alliance_back_to_menu'
        ))
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if user owns this menu"""
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "❌ This menu is not for you!",
                ephemeral=True
            )
            return False
        return True


class AllianceSystemCog(commands.Cog):
    """Alliance System"""
    
    def __init__(self, bot):
        self.bot = bot
        self._register_button_handlers()
    
    def _register_button_handlers(self):
        """تسجيل معالجات الأزرار في النظام المركزي"""
        from utils.button_handler import button_handler
        
        # تسجيل معالج البادئة لجميع أزرار التحالفات
        button_handler.register_prefix_handler('alliance_', self._handle_alliance_button)
        
        logger.info("✅ Registered AllianceSystem button handlers")
    
    async def _handle_alliance_button(self, interaction: discord.Interaction, custom_id: str):
        """معالجة أزرار التحالفات"""
        # Alliance menu button routing
        if custom_id == 'alliance_info':
            await interaction.response.defer()
            await self._show_alliance_info(interaction)
        
        elif custom_id == 'alliance_create':
            await self._handle_create_alliance(interaction)
        
        elif custom_id == 'alliance_join':
            await self._handle_join_alliance(interaction)
        
        elif custom_id == 'alliance_ranks':
            await self._show_ranks(interaction)
        
        elif custom_id == 'alliance_promote':
            await self._handle_promote(interaction)
        
        elif custom_id == 'alliance_demote':
            await self._handle_demote(interaction)
        
        elif custom_id == 'alliance_kick':
            await self._handle_kick(interaction)
        
        elif custom_id == 'alliance_back':
            await interaction.response.defer()
            await self._back_to_main(interaction)
        
        elif custom_id == 'alliance_back_to_menu':
            await interaction.response.defer()
            await self.show_alliance_menu(interaction)
        
        elif custom_id == 'alliance_members':
            await interaction.response.defer()
            await self._show_members(interaction)



    async def _safe_send(self, interaction: discord.Interaction, **kwargs):
        if interaction.response.is_done():
            return await interaction.followup.send(**kwargs)
        return await interaction.response.send_message(**kwargs)

    async def _safe_edit(self, interaction: discord.Interaction, **kwargs):
        if interaction.response.is_done():
            return await interaction.edit_original_response(**kwargs)
        return await interaction.response.edit_message(**kwargs)

    @app_commands.command(name='alliance', description='🤝 Alliance actions')
    @app_commands.describe(action='Action: menu/info/create/join/leave', name='Alliance name', tag='Alliance tag (3 chars)')
    @app_commands.choices(action=[
        app_commands.Choice(name='menu', value='menu'),
        app_commands.Choice(name='info', value='info'),
        app_commands.Choice(name='create', value='create'),
        app_commands.Choice(name='join', value='join'),
        app_commands.Choice(name='leave', value='leave'),
    ])
    async def alliance(self, interaction: discord.Interaction, action: app_commands.Choice[str], name: str = '', tag: str = ''):
        """Alliance slash entry point"""
        user_id = str(interaction.user.id)
        await translator.load_user_language_from_db(db, user_id)

        user = await db.get_user_by_discord_id(user_id)
        if not user:
            user = await db.get_or_create_user(user_id, interaction.user.name, user_id)

        if action.value == 'menu':
            return await self.show_alliance_menu(interaction)

        if action.value == 'info':
            return await self._show_alliance_info(interaction)

        if action.value == 'create':
            clean_tag = (tag or '').strip().upper()
            if len(clean_tag) != 3:
                return await self._safe_send(interaction, content='❌ TAG must be exactly 3 characters.', ephemeral=True)
            if user.alliance_id:
                return await self._safe_send(interaction, content=get_text(user_id, 'alliance.already_member'), ephemeral=True)
            if not name.strip():
                return await self._safe_send(interaction, content='❌ Please provide alliance name.', ephemeral=True)

            try:
                await db.create_alliance(name=name.strip(), tag=clean_tag, leader_id=user.user_id, description='')
                return await self._safe_send(interaction, content=get_text(user_id, 'alliance.created_success'), ephemeral=True)
            except Exception as e:
                return await self._safe_send(interaction, content=f'❌ {e}', ephemeral=True)

        if action.value == 'join':
            clean_tag = (tag or '').strip().upper()
            if len(clean_tag) != 3:
                return await self._safe_send(interaction, content='❌ TAG must be exactly 3 characters.', ephemeral=True)
            if user.alliance_id:
                return await self._safe_send(interaction, content=get_text(user_id, 'alliance.already_member'), ephemeral=True)

            alliance = await db.get_alliance_by_tag(clean_tag)
            if not alliance:
                return await self._safe_send(interaction, content=get_text(user_id, 'alliance.not_found'), ephemeral=True)

            await db.join_alliance(user.user_id, alliance.alliance_id)
            return await self._safe_send(interaction, content=get_text(user_id, 'alliance.joined_success'), ephemeral=True)

        if action.value == 'leave':
            if not user.alliance_id:
                return await self._safe_send(interaction, content=get_text(user_id, 'alliance.no_alliance'), ephemeral=True)

            alliance = await db.get_alliance(user.alliance_id)
            if alliance and alliance.leader_id == user.user_id:
                return await self._safe_send(interaction, content='❌ Leader cannot leave before transferring leadership.', ephemeral=True)

            await db.leave_alliance(user.user_id, user.alliance_id)
            return await self._safe_send(interaction, content=get_text(user_id, 'alliance.left_success'), ephemeral=True)
    
    async def show_alliance_menu(self, interaction: discord.Interaction):
        """Show alliance main menu"""
        user_id = str(interaction.user.id)
        
        try:
            # Get user
            user = await db.get_user_by_discord_id(user_id)
            in_alliance = bool(user and user.alliance_id)
            # Check if user has alliance permissions
            has_permissions = (
                permissions.is_owner(interaction.user) or
                permissions.is_admin(interaction.user) or
                await permissions.has_permission(interaction.user, 'alliance_management')
            )
            view = AllianceMenuView(user_id, in_alliance, has_permissions)
            if not in_alliance:
                embed = create_colored_embed(
                    get_text(user_id, 'alliance.menu_title'),
                    get_text(user_id, 'alliance.no_alliance'),
                    'warning'
                )
            else:
                embed = create_colored_embed(
                    get_text(user_id, 'alliance.menu_title'),
                    get_text(user_id, 'alliance.menu_desc'),
                    'info'
                )
            await self._safe_edit(interaction, embed=embed, view=view)
        except Exception as e:
            logger.error(f"Error showing alliance menu: {e}")
            await self._safe_send(interaction, content=f"❌ Error: {str(e)}", ephemeral=True)
    
    # تم حذف بقايا كود غير مرتب خارج الدوال
    
    async def _show_alliance_info(self, interaction: discord.Interaction):
        """Show alliance information"""
        user_id = str(interaction.user.id)
        
        try:
            user = await db.get_user_by_discord_id(user_id)
            if not user or not user.alliance_id:
                await self._safe_send(interaction, content=get_text(user_id, 'alliance.no_alliance'), ephemeral=True)
                return
            
            alliance = await db.get_alliance(user.alliance_id)
            if not alliance:
                await self._safe_send(interaction, content=get_text(user_id, 'alliance.not_found'), ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"🤝 {alliance.name}",
                description=get_text(user_id, 'alliance.info'),
                color=discord.Color.gold()
            )
            
            # Alliance details
            embed.add_field(
                name=get_text(user_id, 'alliance.name'),
                value=f"{alliance.name} [{alliance.tag}]",
                inline=True
            )
            
            embed.add_field(
                name=get_text(user_id, 'alliance.level'),
                value=str(alliance.level),
                inline=True
            )
            
            embed.add_field(
                name=get_text(user_id, 'alliance.member_count'),
                value=f"{alliance.member_count}/{alliance.max_members}",
                inline=True
            )
            
            embed.add_field(
                name=get_text(user_id, 'alliance.total_power'),
                value=str(alliance.total_power),
                inline=True
            )
            
            if alliance.description:
                embed.add_field(
                    name=get_text(user_id, 'alliance.description'),
                    value=alliance.description,
                    inline=False
                )
            
            if alliance.rules:
                embed.add_field(
                    name=get_text(user_id, 'alliance.rules'),
                    value=alliance.rules,
                    inline=False
                )
            
            # Back button
            view = discord.ui.View(timeout=180)
            view.add_item(discord.ui.Button(
                label=get_text(user_id, 'common.back'),
                style=discord.ButtonStyle.secondary,
                custom_id='alliance_back_to_menu'
            ))
            
            await self._safe_edit(interaction, embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error showing alliance info: {e}")
            await self._safe_send(interaction, content=f"❌ Error: {str(e)}", ephemeral=True)
    
    async def _show_members(self, interaction: discord.Interaction):
        """Show alliance members (منظم ونهائي)"""
        user_id = str(interaction.user.id)
        try:
            user = await db.get_user_by_discord_id(user_id)
            if not user or not user.alliance_id:
                embed = discord.Embed(title=get_text(user_id, 'alliance.members_title'), color=discord.Color.blue())
                embed.description = get_text(user_id, 'alliance.no_alliance')
                view = discord.ui.View(timeout=180)
                view.add_item(discord.ui.Button(
                    label=get_text(user_id, 'common.back'),
                    style=discord.ButtonStyle.secondary,
                    custom_id='alliance_back_to_menu'
                ))
                await self._safe_edit(interaction, embed=embed, view=view)
                return
            alliance = await db.get_alliance(user.alliance_id)
            if not alliance:
                embed = discord.Embed(title=get_text(user_id, 'alliance.members_title'), color=discord.Color.blue())
                embed.description = get_text(user_id, 'alliance.not_found')
                view = discord.ui.View(timeout=180)
                view.add_item(discord.ui.Button(
                    label=get_text(user_id, 'common.back'),
                    style=discord.ButtonStyle.secondary,
                    custom_id='alliance_back_to_menu'
                ))
                await self._safe_edit(interaction, embed=embed, view=view)
                return
            members_data = await db.fetchall(
                "SELECT discord_id, username, alliance_rank, last_activity FROM users WHERE alliance_id = ? ORDER BY alliance_rank DESC",
                (alliance.alliance_id,)
            )
            embed = discord.Embed(
                title=get_text(user_id, 'alliance.members_title'),
                description=f"**{alliance.name}** - {len(members_data)} members",
                color=discord.Color.blue()
            )
            if members_data:
                for member in members_data[:15]:  # Show first 15
                    discord_id, username, rank, last_activity = member
                    rank_name = rank or "R1"
                    embed.add_field(
                        name=f"**{username}** - {rank_name}",
                        value=f"ID: {discord_id}",
                        inline=False
                    )
                view = AllianceMembersManagementView(user_id, members_data[:5])
            else:
                embed.description = get_text(user_id, 'alliance.no_members')
                view = discord.ui.View(timeout=180)
                view.add_item(discord.ui.Button(
                    label=get_text(user_id, 'common.back'),
                    style=discord.ButtonStyle.secondary,
                    custom_id='alliance_back_to_menu'
                ))
            await self._safe_edit(interaction, embed=embed, view=view)
            return
        except Exception as e:
            logger.error(f"Error showing members: {e}")
            await self._safe_send(interaction, content=f"❌ Error: {str(e)}", ephemeral=True)
    
    async def _show_ranks(self, interaction: discord.Interaction):
        """Show alliance ranks"""
        await interaction.response.defer()
        user_id = str(interaction.user.id)
        
        try:
            user = await db.get_user_by_discord_id(user_id)
            if not user or not user.alliance_id:
                embed = discord.Embed(
                    title=get_text(user_id, 'alliance.ranks_title'),
                    description=get_text(user_id, 'alliance.no_alliance'),
                    color=discord.Color.blue()
                )
            else:
                alliance = await db.get_alliance(user.alliance_id)
                embed = discord.Embed(
                    title=get_text(user_id, 'alliance.ranks_title'),
                    description=f"**{alliance.name if alliance else 'Alliance'}**",
                    color=discord.Color.blue()
                )
                
                # Define alliance ranks
                ranks_info = [
                    ("R5 - Leader", "Full alliance control"),
                    ("R4 - Deputy", "Manage members, Accept/Reject"),
                    ("R3 - Elder", "Manage reservations"),
                    ("R2 - Member", "Make reservations"),
                    ("R1 - Recruit", "Basic access")
                ]
                
                for rank_name, rank_desc in ranks_info:
                    embed.add_field(
                        name=rank_name,
                        value=rank_desc,
                        inline=False
                    )
            
            view = discord.ui.View(timeout=180)
            view.add_item(discord.ui.Button(
                label=get_text(user_id, 'common.back'),
                style=discord.ButtonStyle.secondary,
                custom_id='alliance_back_to_menu'
            ))
            
            await self._safe_edit(interaction, embed=embed, view=view)
        except Exception as e:
            logger.error(f"Error showing ranks: {e}")
            await self._safe_send(interaction, content=f"❌ Error: {str(e)}", ephemeral=True)
    
    async def _handle_create_alliance(self, interaction: discord.Interaction):
        """Handle create alliance button - show modal"""
        from utils.buttons import CreateAllianceModal
        modal = CreateAllianceModal()
        await interaction.response.send_modal(modal)
    
    async def _handle_join_alliance(self, interaction: discord.Interaction):
        """Handle join alliance button - show modal for tag input"""
        user_id = str(interaction.user.id)
        
        class JoinAllianceModal(ui.Modal, title=get_text(user_id, 'alliance.join')):
            tag_input = ui.TextInput(
                label='Alliance Tag',
                placeholder='Enter 3-letter alliance tag (e.g., ABC)',
                required=True,
                min_length=3,
                max_length=3
            )
            
            async def on_submit(self, modal_interaction: discord.Interaction):
                user_id = str(modal_interaction.user.id)
                tag = self.tag_input.value.strip().upper()
                
                try:
                    user = await db.get_user_by_discord_id(user_id)
                    if user and user.alliance_id:
                        await modal_interaction.response.send_message(
                            get_text(user_id, 'alliance.already_member'),
                            ephemeral=True
                        )
                        return
                    
                    alliance = await db.get_alliance_by_tag(tag)
                    if not alliance:
                        await modal_interaction.response.send_message(
                            get_text(user_id, 'alliance.not_found'),
                            ephemeral=True
                        )
                        return
                    
                    if not user:
                        user = await db.get_or_create_user(user_id, modal_interaction.user.name, user_id)
                    
                    await db.join_alliance(user.user_id, alliance.alliance_id)
                    await modal_interaction.response.send_message(
                        get_text(user_id, 'alliance.joined_success'),
                        ephemeral=True
                    )
                except Exception as e:
                    logger.error(f"Error joining alliance: {e}")
                    await modal_interaction.response.send_message(
                        f"❌ Error: {str(e)}",
                        ephemeral=True
                    )
        
        await interaction.response.send_modal(JoinAllianceModal())
    
    async def _handle_promote(self, interaction: discord.Interaction):
        """Handle promote member button"""
        user_id = str(interaction.user.id)
        await interaction.response.send_message(
            "⚠️ Promote feature coming soon. Use `/alliance` command for now.",
            ephemeral=True
        )
    
    async def _handle_demote(self, interaction: discord.Interaction):
        """Handle demote member button"""
        user_id = str(interaction.user.id)
        await interaction.response.send_message(
            "⚠️ Demote feature coming soon. Use `/alliance` command for now.",
            ephemeral=True
        )
    
    async def _handle_kick(self, interaction: discord.Interaction):
        """Handle kick member button"""
        user_id = str(interaction.user.id)
        await interaction.response.send_message(
            "⚠️ Kick feature coming soon. Use `/alliance` command for now.",
            ephemeral=True
        )
        
        
    
    async def _back_to_main(self, interaction: discord.Interaction):
        """Go back to main control panel"""
        user_id = str(interaction.user.id)
        
        is_admin = permissions.is_admin(interaction.user)
        is_owner = permissions.is_owner(interaction.user)
        
        from cogs.main_control_panel import MainControlPanelView
        view = MainControlPanelView(user_id, is_admin, is_owner)
        
        embed = create_colored_embed(
            get_text(user_id, 'main_menu.title'),
            get_text(user_id, 'main_menu.description'),
            'info'
        )
        
        await self._safe_edit(interaction, embed=embed, view=view)


async def setup(bot):
    """Setup the cog"""
    await bot.add_cog(AllianceSystemCog(bot))
