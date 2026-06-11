import logging
import aiohttp
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode

# Configure logging
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.reply(
        "🕵️‍♂️ **OSINT Intelligence Bot Active**\n\n"
        "Available intelligence commands:\n"
        "👉 `/github <username>` - Scan GitHub profile\n"
        "👉 `/phone <+countrycode_number>` - Lookup phone metadata"
    )

# --- GITHUB OSINT HANDLER ---
@dp.message(Command("github"))
async def github_osint(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("❌ Please provide a username. Example: `/github torvalds`")
        return
    
    target_username = args[1].strip()
    await message.reply(f"🔍 Investigating GitHub: `{target_username}`...")

    url = f"https://api.github.com/users/{target_username}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 404:
                await message.reply("❌ Target not found.")
                return
            data = await response.json()

    intel_report = (
        f"🕵️‍♂️ **OSINT REPORT: GITHUB**\n"
        f"👤 **Name:** {data.get('name', 'N/A')}\n"
        f"🏷️ **Username:** {data.get('login')}\n"
        f"📍 **Location:** {data.get('location', 'N/A')}\n"
        f"📬 **Public Email:** {data.get('email', 'N/A')}\n"
        f"🔗 [Profile Link]({data.get('html_url')})"
    )
    await message.reply(intel_report, parse_mode=ParseMode.MARKDOWN)


# --- PHONE OSINT HANDLER ---
@dp.message(Command("phone"))
async def phone_osint(message: types.Message):
    # Extract phone number from command
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("❌ Please provide a phone number with country code. \nExample: `/phone +14155552671`")
        return

    raw_number = args[1].strip()
    await message.reply(f"🔍 Analyzing phone target: `{raw_number}`... Please wait.")

    try:
        # Parse the string into an international phone number format
        parsed_number = phonenumbers.parse(raw_number, None)
        
        # Validate if the number is even possible/real
        is_valid = phonenumbers.is_valid_number(parsed_number)
        is_possible = phonenumbers.is_possible_number(parsed_number)
        
        if not is_possible:
            await message.reply("❌ This number format is completely invalid.")
            return

        # Extract intelligence metrics
        number_type = phonenumbers.number_type(parsed_number)
        # Convert type integer to a readable string (Mobile, Fixed Line, etc.)
        type_mapping = {0: "Fixed Line", 1: "Mobile", 2: "Fixed Line or Mobile", 3: "Toll Free", 4: "Premium Rate"}
        readable_type = type_mapping.get(number_type, "Unknown / VoIP")

        country = geocoder.country_name_for_number(parsed_number, "en")
        location = geocoder.description_for_number(parsed_number, "en")
        phone_carrier = carrier.name_for_number(parsed_number, "en")
        timezones = timezone.time_zones_for_number(parsed_number)

        # Format Intel Report
        phone_report = (
            f"🕵️‍♂️ **OSINT INTEL REPORT: PHONE TARGET**\n"
            f"----------------------------------------\n"
            f"🔢 **Formatted No:** {phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)}\n"
            f"🌍 **Country:** {country if country else 'Unknown'}\n"
            f"📍 **Location/Region:** {location if location else 'Unknown'}\n"
            f"📶 **Carrier:** {phone_carrier if phone_carrier else 'Unknown/Virtual (VoIP)'}\n"
            f"📱 **Line Type:** {readable_type}\n"
            f"⏰ **Timezones:** {', '.join(timezones)}\n"
            f"----------------------------------------\n"
            f"✅ **Valid Number:** {'Yes' if is_valid else 'No (Active/Spoofed format)'}\n"
        )

        await message.reply(phone_report, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await message.reply(f"❌ Verification error. Make sure to include the '+' and the country code. \n_Error: {str(e)}_", parse_mode=ParseMode.MARKDOWN)


async def main():
    print("🤖 Bot is up with GitHub & Phone OSINT modules...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
