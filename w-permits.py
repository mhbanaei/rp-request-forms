import discord
from discord.ext import commands
import datetime

# ===== تنظیمات اولیه =====
TOKEN = "YourDiscordTokenU"  # توکن بات
GUILD_ID = YourDiscordToken  # آیدی سرور (به صورت عدد)
LOG_CHANNEL_ID = YourDiscordToken  # آیدی کانالی که خروجی فرم‌ها ارسال می‌شود (به صورت عدد)
ALLOWED_ROLE_ID = YourDiscordToken  # آیدی نقش مجاز برای استفاده از فرم‌ها (به صورت عدد)
ACCEPT_CHANNEL_ID = YourDiscordToken  # آیدی کانال پذیرش درخواست‌ها
DENY_CHANNEL_ID = YourDiscordToken    # آیدی کانال رد درخواست‌ها

# تنظیم intents لازم
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------------- Modal توضیحات ----------------------
class ExplanationModal(discord.ui.Modal):
    def __init__(self, applicant: discord.User, original_embed: discord.Embed, reviewer: discord.User, action: str, original_message: discord.Message):
        """
        :param applicant: کاربر درخواست‌دهنده
        :param original_embed: ایمبد فرم درخواست (قبل از افزودن توضیحات)
        :param reviewer: کاربری که درخواست را بررسی می‌کند (Accept/Deny)
        :param action: "accept" یا "deny"
        :param original_message: پیام اصلی که دکمه‌ها روی آن قرار دارند
        """
        title = "توضیحات پذیرش" if action == "accept" else "توضیحات رد"
        super().__init__(title=title)
        self.applicant = applicant
        self.original_embed = original_embed
        self.reviewer = reviewer
        self.action = action
        self.original_message = original_message

        self.explanation = discord.ui.TextInput(
            label="توضیحات (اختیاری)",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=500
        )
        self.add_item(self.explanation)

    async def on_submit(self, interaction: discord.Interaction):
        now = datetime.datetime.now()
        date_str = now.strftime("%H:%M %m/%d/%Y")
        file_number = f"{now.hour:02d}{now.minute:02d}{now.month:02d}{now.day:02d}{now.year}"

        # استخراج اطلاعات از ایمبد اصلی
        applicant_name = self.original_embed.fields[0].value if self.original_embed.fields else "نامشخص"
        footer_text = self.original_embed.footer.text if self.original_embed.footer.text else ""
        if "Discord ID:" in footer_text:
            applicant_id = footer_text.split("Discord ID:")[-1].strip()
        else:
            applicant_id = str(self.applicant.id)
        applicant_tag = self.applicant.mention

        # تنظیم عنوان و رنگ بر اساس نوع اقدام
        if self.action == "accept":
            embed_title = "مجوز اسلحه پذیرفته شده"
            color = discord.Color.green()
            target_channel_id = ACCEPT_CHANNEL_ID
        else:
            embed_title = "مجوز اسلحه رد شده"
            color = discord.Color.red()
            target_channel_id = DENY_CHANNEL_ID

        new_embed = discord.Embed(title=embed_title, color=color)
        new_embed.add_field(name="تاریخ (میلادی)", value=date_str, inline=False)
        new_embed.add_field(name="شماره پیگیری", value=file_number, inline=False)
        new_embed.add_field(name="نام و نام خانوادگی ((IC))", value=applicant_name, inline=False)
        new_embed.add_field(name="Discord ID", value=applicant_id, inline=False)
        new_embed.add_field(name="Discord Tag", value=applicant_tag, inline=False)
        new_embed.add_field(name="توسط", value=self.reviewer.mention, inline=False)

        if self.explanation.value:
            new_embed.add_field(name="توضیحات", value=self.explanation.value, inline=False)

        # ارسال به کانال مورد نظر
        channel = bot.get_channel(target_channel_id)
        if channel:
            await channel.send(embed=new_embed)
        else:
            await interaction.response.send_message("کانال مورد نظر یافت نشد.", ephemeral=True)
            return

        # ارسال پیام خصوصی به درخواست‌دهنده
        try:
            await self.applicant.send(embed=new_embed)
        except Exception:
            await interaction.followup.send("ارسال پیام خصوصی به شما ناموفق بود.", ephemeral=True)

        # حذف دکمه‌های پیام اصلی پس از موفقیت
        try:
            await self.original_message.edit(view=None)
        except Exception:
            pass

        await interaction.response.send_message(
            f"درخواست با موفقیت {'پذیرفته' if self.action == 'accept' else 'رد'} شد.",
            ephemeral=True
        )

# ---------------------- Persistent View دکمه‌های Accept/Deny ----------------------
class ApprovalView(discord.ui.View):
    def __init__(self):
        # timeout=None یعنی ویو هرگز منقضی نمی‌شود
        super().__init__(timeout=None)

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, custom_id="persistent_accept")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # بررسی نقش مجاز
        if ALLOWED_ROLE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("شما مجاز به استفاده از این دکمه نیستید.", ephemeral=True)
            return
        
        if not interaction.message.embeds:
            await interaction.response.send_message("هیچ ایمبدی یافت نشد.", ephemeral=True)
            return
        embed = interaction.message.embeds[0]
        footer_text = embed.footer.text if embed.footer.text else ""
        if "Discord ID:" in footer_text:
            applicant_id_str = footer_text.split("Discord ID:")[-1].strip()
        else:
            await interaction.response.send_message("اطلاعات کاربر یافت نشد.", ephemeral=True)
            return
        try:
            applicant = await bot.fetch_user(int(applicant_id_str))
        except Exception:
            await interaction.response.send_message("خطا در بازیابی اطلاعات کاربر.", ephemeral=True)
            return
        
        modal = ExplanationModal(
            applicant=applicant,
            original_embed=embed,
            reviewer=interaction.user,
            action="accept",
            original_message=interaction.message
        )
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger, custom_id="persistent_deny")
    async def deny_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # بررسی نقش مجاز
        if ALLOWED_ROLE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("شما مجاز به استفاده از این دکمه نیستید.", ephemeral=True)
            return
        
        if not interaction.message.embeds:
            await interaction.response.send_message("هیچ ایمبدی یافت نشد.", ephemeral=True)
            return
        embed = interaction.message.embeds[0]
        footer_text = embed.footer.text if embed.footer.text else ""
        if "Discord ID:" in footer_text:
            applicant_id_str = footer_text.split("Discord ID:")[-1].strip()
        else:
            await interaction.response.send_message("اطلاعات کاربر یافت نشد.", ephemeral=True)
            return
        try:
            applicant = await bot.fetch_user(int(applicant_id_str))
        except Exception:
            await interaction.response.send_message("خطا در بازیابی اطلاعات کاربر.", ephemeral=True)
            return
        
        modal = ExplanationModal(
            applicant=applicant,
            original_embed=embed,
            reviewer=interaction.user,
            action="deny",
            original_message=interaction.message
        )
        await interaction.response.send_modal(modal)

# ---------------------- View دکمه‌های تایید اولیه در DM ----------------------
class ConfirmView(discord.ui.View):
    def __init__(self, author: discord.User):
        super().__init__(timeout=60)  # تایم‌اوت 60 ثانیه
        self.author = author
        self.value = None

    @discord.ui.button(label="متوجه شدم", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("این دکمه برای شما نیست!", ephemeral=True)
            return
        self.value = True
        self.stop()
        await interaction.response.edit_message(content="تأیید شد، فرم درخواست شروع می‌شود...", view=None)

    @discord.ui.button(label="منصرف شدم", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("این دکمه برای شما نیست!", ephemeral=True)
            return
        self.value = False
        self.stop()
        await interaction.response.edit_message(content="فرآیند لغو شد.", view=None)

# ---------------------- رویداد آماده بودن ----------------------
@bot.event
async def on_ready():
    # ثبت ویوی persistent برای دکمه‌های Accept/Deny
    bot.add_view(ApprovalView())
    await bot.tree.sync()  # همگام‌سازی دستورات اسلش
    print(f"Logged in as {bot.user}")

# ---------------------- دستور اسلش برای شروع فرآیند ----------------------
@bot.tree.command(name="mojavez_aslahe", description="شروع فرآیند درخواست")
async def mojavez_aslahe(interaction: discord.Interaction):
    view = ConfirmView(interaction.user)
    await interaction.response.send_message(
        "آیا مطمئن هستید که می‌خواهید درخواست دهید؟ \n\n"
        "در نقش‌آفرینی (Roleplay)، دو مفهوم OOC و IC به این شکل تعریف می‌شوند:\n"
        "IC (In Character): یعنی هر چیزی که داخل بازی و در چارچوب شخصیت شما اتفاق می‌افتد.\n"
        "OOC (Out of Character): یعنی هر چیزی که خارج از نقش و داستان بازی باشد.\n\n"
        "ترکیب این دو معمولاً خلاف قوانین نقش‌آفرینی محسوب می‌شود.",
        view=view,
        ephemeral=True
    )
    await view.wait()
    
    if view.value is None or view.value is False:
        return

    try:
        dm_channel = await interaction.user.create_dm()
    except Exception:
        await interaction.followup.send("نمی‌توانم به DM شما پیام بفرستم. لطفاً تنظیمات حریم خصوصی خود را بررسی کنید.", ephemeral=True)
        return

    # لیست سوال‌های فرم
    questions = [
        {"question": "نام و نام خانوادگی ((IC))", "key": "name_ic", "min": 5, "max": 50},
        {"question": "سن ((IC))", "key": "age_ic", "min": 1, "max": 2, "numeric": True},
        {"question": "شماره تماس ((IC))", "key": "phone_ic", "exact": 6, "numeric": True},
        {"question": "محل سکونت ((IC))", "key": "residence_ic"},
        {"question": "آیا قبلاً مجوز اسلحه داشتید ؟ بلی/خیر", "key": "had_gun_license"},
        {"question": "در صورت داشتن مجوز اسلحه قبلی، علت باطل شدن مجوز قبلی چه بود ؟", "key": "gun_license_revoked_reason"},
        {"question": "علت درخواست", "key": "request_reason"},
        {"question": "متوجه هستید برای شرکت در جلسه باید فرم برسی سابقه کیفری همراه شما باشد ؟ بلی/خیر", "key": "understand_criminal_record"},
        {"question": "نام و نام خانوادگی ((OOC))", "key": "name_ooc"},
        {"question": "سن ((OOC))", "key": "age_ooc", "min": 1, "max": 2, "numeric": True}
    ]

    answers = {}

    await dm_channel.send("شروع فرم درخواست دریافت مجوز اسلحه سری الف، لطفاً به ترتیب به سوالات پاسخ دهید")

    def check(m: discord.Message):
        return m.author == interaction.user and m.channel == dm_channel

    for q in questions:
        while True:
            await dm_channel.send(q["question"])
            try:
                msg = await bot.wait_for("message", check=check, timeout=600)  # 600 ثانیه زمان پاسخ
            except Exception:
                await dm_channel.send("زمان پاسخگویی شما به یکی از سوالات تمام شد. لطفاً دوباره امتحان کنید.")
                return

            content = msg.content

            if q.get("numeric", False):
                if not content.isdigit():
                    await dm_channel.send("پاسخ باید فقط شامل ارقام باشد. لطفاً دوباره تلاش کنید.")
                    continue

            if "exact" in q:
                if len(content) != q["exact"]:
                    await dm_channel.send(f"پاسخ شما باید دقیقاً {q['exact']} کاراکتر (رقم) باشد. لطفاً دوباره تلاش کنید.")
                    continue

            if "min" in q:
                if len(content) < q["min"]:
                    await dm_channel.send(f"پاسخ شما باید حداقل {q['min']} کاراکتر داشته باشد. لطفاً دوباره تلاش کنید.")
                    continue

            if "max" in q:
                if len(content) > q["max"]:
                    await dm_channel.send(f"پاسخ شما نباید بیش از {q['max']} کاراکتر باشد. لطفاً دوباره تلاش کنید.")
                    continue

            answers[q["key"]] = content
            break

    await dm_channel.send("فرم شما تکمیل شد. از شما سپاسگزاریم.")

    # ایجاد Embed فرم اولیه جهت گزارش به کانال لاگ
    embed = discord.Embed(title="فرم درخواست", color=discord.Color.red())
    embed.set_author(name=str(interaction.user), icon_url=interaction.user.display_avatar.url)
    embed.add_field(name="نام و نام خانوادگی ((IC))", value=answers.get("name_ic", "ندارد"), inline=False)
    embed.add_field(name="سن ((IC))", value=answers.get("age_ic", "ندارد"), inline=False)
    embed.add_field(name="شماره تماس ((IC))", value=answers.get("phone_ic", "ندارد"), inline=False)
    embed.add_field(name="محل سکونت ((IC))", value=answers.get("residence_ic", "ندارد"), inline=False)
    embed.add_field(name="آیا قبلاً مجوز اسلحه داشتید ؟ بلی/خیر", value=answers.get("had_gun_license", "ندارد"), inline=False)
    embed.add_field(name="علت باطل شدن مجوز اسلحه قبلی", value=answers.get("gun_license_revoked_reason", "ندارد"), inline=False)
    embed.add_field(name="علت درخواست", value=answers.get("request_reason", "ندارد"), inline=False)
    embed.add_field(name="آیا از نیاز داشتن فرم برسی سابقه کیفری مطلع هستید؟", value=answers.get("understand_criminal_record", "ندارد"), inline=False)
    embed.add_field(name="نام و نام خانوادگی ((OOC))", value=answers.get("name_ooc", "ندارد"), inline=False)
    embed.add_field(name="سن ((OOC))", value=answers.get("age_ooc", "ندارد"), inline=False)
    # ذخیره Discord ID درخواست‌دهنده در فوتر ایمبد
    embed.set_footer(text=f"Discord ID: {interaction.user.id}")

    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        # ارسال فرم به کانال لاگ به همراه ویوی persistent
        await log_channel.send(content=interaction.user.mention, embed=embed, view=ApprovalView())
    else:
        await dm_channel.send("خطا: کانال لاگ پیدا نشد.")

    await dm_channel.send("درخواست شما ارسال شد.")

bot.run(TOKEN)
