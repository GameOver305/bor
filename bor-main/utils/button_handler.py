"""
معالج الأزرار المركزي - Centralized Button Handler
نظام موحد لمعالجة جميع تفاعلات الأزرار في البوت
"""
import discord
from discord.ext import commands
import logging
from typing import Dict, Callable, Optional, Awaitable

logger = logging.getLogger('button_handler')


class ButtonHandler:
    """
    معالج مركزي لجميع الأزرار في البوت
    يوفر نظام موحد لتسجيل ومعالجة تفاعلات الأزرار
    """
    
    def __init__(self):
        self._handlers: Dict[str, Callable[[discord.Interaction], Awaitable[None]]] = {}
        self._prefix_handlers: Dict[str, Callable[[discord.Interaction, str], Awaitable[None]]] = {}
    
    def register_handler(self, custom_id: str, handler: Callable[[discord.Interaction], Awaitable[None]]):
        """
        تسجيل معالج لـ custom_id محدد
        
        Args:
            custom_id: المعرف الفريد للزر
            handler: الدالة التي ستعالج التفاعل
        """
        if custom_id in self._handlers:
            logger.warning(f"⚠️ Overwriting existing handler for custom_id: {custom_id}")
        
        self._handlers[custom_id] = handler
        logger.debug(f"✅ Registered handler for: {custom_id}")
    
    def register_prefix_handler(self, prefix: str, handler: Callable[[discord.Interaction, str], Awaitable[None]]):
        """
        تسجيل معالج لجميع الأزرار التي تبدأ بـ prefix معين
        
        Args:
            prefix: البادئة (مثل 'main_btn_' أو 'res_')
            handler: الدالة التي ستعالج التفاعل (تستقبل interaction و custom_id الكامل)
        """
        if prefix in self._prefix_handlers:
            logger.warning(f"⚠️ Overwriting existing prefix handler for: {prefix}")
        
        self._prefix_handlers[prefix] = handler
        logger.debug(f"✅ Registered prefix handler for: {prefix}*")
    
    async def handle_interaction(self, interaction: discord.Interaction) -> bool:
        """
        معالجة التفاعل
        
        Args:
            interaction: تفاعل الديسكورد
            
        Returns:
            True إذا تمت معالجة التفاعل، False إذا لم يتم العثور على معالج
        """
        # التحقق من نوع التفاعل
        if interaction.type != discord.InteractionType.component:
            return False
        
        # الحصول على custom_id بشكل آمن
        custom_id = self._get_custom_id(interaction)
        if not custom_id:
            logger.warning("⚠️ Button interaction without custom_id")
            return False
        
        logger.debug(f"🔘 Processing button: {custom_id}")
        
        # البحث عن معالج مباشر
        if custom_id in self._handlers:
            try:
                await self._handlers[custom_id](interaction)
                logger.debug(f"✅ Handled by direct handler: {custom_id}")
                return True
            except Exception as e:
                logger.error(f"❌ Error in handler for {custom_id}: {e}", exc_info=True)
                await self._send_error(interaction, str(e))
                return True
        
        # البحث عن معالج بادئة
        for prefix, handler in self._prefix_handlers.items():
            if custom_id.startswith(prefix):
                try:
                    await handler(interaction, custom_id)
                    logger.debug(f"✅ Handled by prefix handler: {prefix}* -> {custom_id}")
                    return True
                except Exception as e:
                    logger.error(f"❌ Error in prefix handler {prefix} for {custom_id}: {e}", exc_info=True)
                    await self._send_error(interaction, str(e))
                    return True
        
        logger.debug(f"⚠️ No handler found for: {custom_id}")
        return False
    
    def _get_custom_id(self, interaction: discord.Interaction) -> Optional[str]:
        """
        الحصول على custom_id بشكل آمن من التفاعل
        
        Args:
            interaction: تفاعل الديسكورد
            
        Returns:
            custom_id أو None إذا لم يكن موجوداً
        """
        if not interaction.data:
            return None
        
        return interaction.data.get('custom_id', None)
    
    async def _send_error(self, interaction: discord.Interaction, error_msg: str):
        """
        إرسال رسالة خطأ للمستخدم
        
        Args:
            interaction: تفاعل الديسكورد
            error_msg: رسالة الخطأ
        """
        try:
            if interaction.response.is_done():
                await interaction.followup.send(
                    f"❌ حدث خطأ: {error_msg}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"❌ حدث خطأ: {error_msg}",
                    ephemeral=True
                )
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
    
    def get_registered_handlers(self) -> Dict[str, str]:
        """
        الحصول على قائمة بجميع المعالجات المسجلة
        
        Returns:
            قاموس بالـ custom_ids ومعالجاتها
        """
        return {
            'direct_handlers': list(self._handlers.keys()),
            'prefix_handlers': list(self._prefix_handlers.keys())
        }
    
    def unregister_handler(self, custom_id: str) -> bool:
        """
        إلغاء تسجيل معالج
        
        Args:
            custom_id: المعرف الفريد للزر
            
        Returns:
            True إذا تم الإلغاء بنجاح
        """
        if custom_id in self._handlers:
            del self._handlers[custom_id]
            logger.debug(f"🗑️ Unregistered handler for: {custom_id}")
            return True
        return False
    
    def unregister_prefix_handler(self, prefix: str) -> bool:
        """
        إلغاء تسجيل معالج بادئة
        
        Args:
            prefix: البادئة
            
        Returns:
            True إذا تم الإلغاء بنجاح
        """
        if prefix in self._prefix_handlers:
            del self._prefix_handlers[prefix]
            logger.debug(f"🗑️ Unregistered prefix handler for: {prefix}*")
            return True
        return False


# إنشاء instance عام
button_handler = ButtonHandler()


class ButtonHandlerCog(commands.Cog):
    """
    Cog لمعالجة الأزرار بشكل عام
    يستمع لجميع تفاعلات الأزرار ويوجهها للمعالج المناسب
    """
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.handler = button_handler
        logger.info("🔘 ButtonHandlerCog initialized")
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """
        المستمع العام لجميع التفاعلات
        يعالج تفاعلات الأزرار فقط
        """
        # معالجة التفاعل عبر المعالج المركزي
        await self.handler.handle_interaction(interaction)


async def setup(bot: commands.Bot):
    """تثبيت الـ Cog"""
    await bot.add_cog(ButtonHandlerCog(bot))
    logger.info("✅ ButtonHandler system loaded")
