import discord
from discord.ext import commands
import json
import random
import string

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== DATABASE (simple JSON for now) =====
def load_data(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

users = load_data("users.json")
stock = load_data("stock.json")
orders = load_data("orders.json")
vouchers = load_data("vouchers.json")

# ===== UTIL =====
def generate_order_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# ===== WALLET =====
@bot.command()
async def balance(ctx):
    uid = str(ctx.author.id)
    bal = users.get(uid, {}).get("balance", 0)
    await ctx.send(f"💰 Your balance: {bal}")

# ===== ADD BALANCE (ADMIN) =====
@bot.command()
@commands.has_permissions(administrator=True)
async def addbal(ctx, member: discord.Member, amount: int):
    uid = str(member.id)
    users.setdefault(uid, {"balance": 0})
    users[uid]["balance"] += amount
    save_data("users.json", users)
    await ctx.send(f"Added {amount} to {member}")

# ===== STOCK =====
@bot.command()
@commands.has_permissions(administrator=True)
async def addstock(ctx, item, *, data):
    stock.setdefault(item, [])
    stock[item].append(data)
    save_data("stock.json", stock)
    await ctx.send(f"Added stock to {item}")

@bot.command()
async def stockview(ctx):
    msg = ""
    for item, items in stock.items():
        msg += f"{item}: {len(items)} available\n"
    await ctx.send(msg)

# ===== BUY SYSTEM =====
@bot.command()
async def buy(ctx, item):
    uid = str(ctx.author.id)

    if item not in stock or len(stock[item]) == 0:
        return await ctx.send("❌ Out of stock")

    price = 10  # change per item later
    users.setdefault(uid, {"balance": 0})

    if users[uid]["balance"] < price:
        return await ctx.send("❌ Not enough balance")

    # Deduct
    users[uid]["balance"] -= price

    # Deliver
    product = stock[item].pop(0)
    order_id = generate_order_id()

    orders[order_id] = {
        "user": uid,
        "item": item,
        "data": product
    }

    save_data("users.json", users)
    save_data("stock.json", stock)
    save_data("orders.json", orders)

    try:
        await ctx.author.send(f"🧾 Order ID: {order_id}\nYour item:\n{product}")
    except:
        await ctx.send("❌ Enable DMs to receive your item")

    await ctx.send(f"✅ Purchase successful! Order ID: {order_id}")

# ===== VOUCH =====
@bot.command()
async def review(ctx, *, msg):
    channel = discord.utils.get(ctx.guild.text_channels, name="vouches")
    if channel:
        await channel.send(f"{ctx.author}: {msg}")
        await ctx.send("✅ Review sent")

# ===== VOUCHER SYSTEM =====
@bot.command()
@commands.has_permissions(administrator=True)
async def createvoucher(ctx, code, amount: int):
    vouchers[code] = amount
    save_data("vouchers.json", vouchers)
    await ctx.send(f"Voucher {code} created")

@bot.command()
async def redeem(ctx, code):
    uid = str(ctx.author.id)

    if code not in vouchers:
        return await ctx.send("❌ Invalid code")

    amount = vouchers.pop(code)
    users.setdefault(uid, {"balance": 0})
    users[uid]["balance"] += amount

    save_data("users.json", users)
    save_data("vouchers.json", vouchers)

    await ctx.send(f"✅ Redeemed {amount}")

# ===== RUN =====
bot.run("MTQ5NzAwNDA1MzYxODYyNjU2MA.GsjDsN.hLFdB1xkBm3sUACVwwRBKWtd3CGqo3sxV6P6QI"